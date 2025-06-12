import os
from gtts import gTTS
import logging
from flask import Flask, request, jsonify, send_from_directory, url_for
from flasgger import Swagger
import uuid
from pdf2image import convert_from_path
import pytesseract
from PIL import Image # Pillow es una dependencia de pdf2image y/o pytesseract
import cv2 # Para preprocesamiento de imágenes
import time # Para añadir retrasos
import numpy as np # Para trabajar con imágenes como arrays
import subprocess # Para ejecutar Piper
import re # Para expresiones regulares en clean_text
from pydub import AudioSegment # Para unir audio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configuración para Tesseract (opcional si está en el PATH)
# Asegúrate de que esta ruta sea la correcta para tu instalación de Tesseract OCR.
TESSERACT_INSTALL_PATH = r'C:\Program Files\Tesseract-OCR' # Ajusta si tu instalación está en otra ruta

try:
    pytesseract.pytesseract.tesseract_cmd = os.path.join(TESSERACT_INSTALL_PATH, 'tesseract.exe')
    if not os.path.exists(pytesseract.pytesseract.tesseract_cmd):
        logging.error(f"El ejecutable de Tesseract no se encontró en: {pytesseract.pytesseract.tesseract_cmd}")
        # Considera levantar un error o manejar esto de forma más robusta si es crítico

    # Establecer TESSDATA_PREFIX para ayudar a Tesseract a encontrar los archivos de idioma.
    tessdata_dir = os.path.join(TESSERACT_INSTALL_PATH, 'tessdata')
    os.environ['TESSDATA_PREFIX'] = tessdata_dir
    logging.info(f"Intentando establecer TESSDATA_PREFIX a: {tessdata_dir}")
except Exception as e:
    logging.error(f"Error configurando la ruta de Tesseract o TESSDATA_PREFIX: {e}")

# Configuración para Poppler (opcional si está en el PATH)
# En Windows, pdf2image podría necesitar la ruta a los binarios de Poppler:
# Descomenta la siguiente línea y ajusta la ruta a tu instalación de Poppler si no está en el PATH.
POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin" # Ejemplo de ruta, ¡AJUSTA ESTO!

# --- Configuración para Piper ---
# Ajusta esta ruta a donde tienes piper.exe si no está en C:\Program Files\piper\
PIPER_EXECUTABLE_PATH = r"C:\Program Files\piper\piper.exe" # ¡AJUSTA ESTA RUTA A TU INSTALACIÓN DE PIPER!

# Define la ruta base para tus modelos de Piper.
# Asumimos que la carpeta 'models' está en el directorio raíz del proyecto,
# al mismo nivel que la carpeta 'src'.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Sube un nivel desde src
PIPER_MODELS_BASE_DIR = os.path.join(PROJECT_ROOT, "models")

# Define aquí tus modelos de Piper disponibles. La clave será lo que uses en la API.
PIPER_VOICES = {
    "es_MX-claude-high": { # Usamos el nombre del modelo como clave
        "model_path": os.path.join(PIPER_MODELS_BASE_DIR, "es_MX", "es_MX-claude-high.onnx"),
        "description": "Voz Claude en Español (México) - Alta calidad"
    },
    "es_ES-mls_9972-low": { # Otra voz que tenías configurada antes
        "model_path": os.path.join(PIPER_MODELS_BASE_DIR, "es_ES-mls_9972-low", "es_ES-mls_9972-low.onnx"), # Asumiendo una estructura similar
        "description": "Voz MLS en Español (España) - Baja calidad"
    }
}

class PDFToAudioOCR:
    def __init__(self, pdf_path, output_txt_path, output_audio_path, lang='es', tts_engine='gtts', piper_voice_key=None):
        self.pdf_path = pdf_path
        self.output_txt_path = output_txt_path
        self.output_audio_path = output_audio_path
        self.lang = lang
        # Mapeo de idiomas para Tesseract (ISO 639-2/B o ISO 639-3)
        self.ocr_lang_map = {
            'es': 'spa',
            'en': 'eng'
            # Añade más mapeos si es necesario
        }
        self.tesseract_lang = self.ocr_lang_map.get(self.lang, 'spa') # Por defecto a español si no se encuentra
        self.tts_engine = tts_engine
        self.piper_voice_key = piper_voice_key

    def extract_text_from_pdf_ocr(self, start_page=None, end_page=None):
        logging.info(f"Iniciando extracción de texto OCR para {self.pdf_path} en idioma {self.tesseract_lang}")
        if start_page or end_page:
            logging.info(f"Extrayendo páginas: Inicio={start_page if start_page else 'Primera'}, Fin={end_page if end_page else 'Última'}")

        try:
            convert_kwargs = {}
            if start_page:
                convert_kwargs['first_page'] = start_page
            if end_page:
                convert_kwargs['last_page'] = end_page

            # Si POPPLER_PATH está definido y no es None, úsalo.
            # Esto es útil principalmente para Windows si Poppler no está en el PATH.
            if 'POPPLER_PATH' in globals() and POPPLER_PATH:
                images = convert_from_path(self.pdf_path, poppler_path=POPPLER_PATH, **convert_kwargs)
            else:
                images = convert_from_path(self.pdf_path, **convert_kwargs)
            full_text = ''
            for i, image in enumerate(images):
                actual_page_num_in_pdf = (start_page if start_page else 1) + i
                logging.info(f"Procesando página {actual_page_num_in_pdf} del PDF (índice {i} de selección) con OCR...")

                # --- Inicio del Preprocesamiento de Imagen ---
                # Convertir imagen PIL a formato OpenCV (numpy array)
                open_cv_image = np.array(image)
                # Convertir de RGB (PIL) a BGR (OpenCV)
                open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

                # 1. Convertir a escala de grises
                gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

                # 2. Binarización (umbralización)
                # Usar el método de Otsu para encontrar un umbral óptimo automáticamente.
                # Esto convierte la imagen a blanco y negro puro, lo que ayuda a Tesseract.
                _, preprocessed_image_cv = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Opcional: Denoising (si las imágenes son ruidosas)
                # preprocessed_image_cv = cv2.medianBlur(preprocessed_image_cv, 3) # Ejemplo con median blur

                # Convertir imagen preprocesada de OpenCV de nuevo a formato PIL para Tesseract
                preprocessed_pil_image = Image.fromarray(cv2.cvtColor(preprocessed_image_cv, cv2.COLOR_BGR2RGB) if len(preprocessed_image_cv.shape) == 3 else cv2.cvtColor(preprocessed_image_cv, cv2.COLOR_GRAY2RGB))
                # --- Fin del Preprocesamiento de Imagen ---
                try:
                    page_text = pytesseract.image_to_string(preprocessed_pil_image, lang=self.tesseract_lang)
                    # Unir el texto de la página actual. Usar un espacio como separador
                    # es generalmente más seguro que añadir un \n, ya que clean_text
                    # se encargará de interpretar correctamente los \n dentro de page_text
                    # y consolidar los espacios.
                    full_text += page_text + ' '
                except pytesseract.TesseractError as te:
                    logging.error(f"Error de Tesseract en la página {i+1}: {te}")
                    logging.error("Asegúrate de que Tesseract esté instalado y configurado correctamente, y que los paquetes de idioma necesarios (ej. tesseract-ocr-spa) estén instalados.")
                    # Continuar con otras páginas si es posible
            
            if not full_text.strip():
                logging.warning("OCR no extrajo texto del PDF.")
                return None
            logging.info(f"Texto extraído con OCR: {len(full_text)} caracteres.")
            return full_text
        except pytesseract.TesseractNotFoundError:
            logging.error("Tesseract no está instalado o no se encuentra en el PATH del sistema.")
            logging.error("Por favor, instala Tesseract OCR y asegúrate de que esté en el PATH.")
            raise # Re-lanzar para que el endpoint lo maneje
        except Exception as e: # Captura errores de pdf2image (ej. Poppler no encontrado)
            logging.error(f"Error durante la conversión de PDF a imagen o OCR: {e}")
            if "pdfinfo" in str(e).lower() or "pdftoppm" in str(e).lower():
                logging.error("Utilidades de Poppler no encontradas o no en PATH. pdf2image requiere Poppler.")
                logging.error("En Windows, considera especificar 'poppler_path' en convert_from_path.")
            return None

    def clean_text(self, text):
        if not text:
            return ""
        # Normalizar todos los tipos de saltos de línea a \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Preservar los saltos de párrafo intencionales (dos o más saltos de línea)
        # reemplazándolos temporalmente con un marcador único.
        # Esto también consolida 3+ saltos de línea en el marcador.
        paragraph_marker = "[[PARA_BREAK_MARKER]]"
        text = re.sub(r'\n\s*\n+', paragraph_marker, text) # Coincide con \n\n, \n \n, \n\n\n etc.

        # Reemplazar los saltos de línea individuales restantes (probablemente rupturas de formato no deseadas
        # dentro de un párrafo) con un espacio.
        text = text.replace('\n', ' ')

        # Restaurar los saltos de párrafo.
        text = text.replace(paragraph_marker, '\n\n')
        
        # Consolidar múltiples espacios que podrían haberse introducido.
        text = re.sub(r' +', ' ', text)
        
        return text.strip()


    def save_to_txt(self, text):
        with open(self.output_txt_path, 'w', encoding='utf-8') as file:
            file.write(text)
        logging.info(f"Texto guardado en {self.output_txt_path}")

    def _split_text_into_chunks(self, text, max_length=48000): # Corregido: Reducido a un valor razonable para gTTS
        """Divide el texto en fragmentos, intentando respetar finales de oración/párrafo."""
        chunks = []
        current_pos = 0
        text_len = len(text)
        while current_pos < text_len:
            if text_len - current_pos <= max_length:
                chunks.append(text[current_pos:])
                break
            else:
                chunk_candidate = text[current_pos : current_pos + max_length]
                last_break = -1 # Indica la posición donde cortar el chunk_candidate

                # Delimitadores revisados. Después de clean_text, '\n' y '.' solos son menos necesarios
                # y pueden ser problemáticos. Priorizamos \n\n y finales de oración claros.
                delimiters = ['\n\n', '. ', '.\n', '! ', '!\n', '? ', '?\n']

                for delim in delimiters:
                    pos = chunk_candidate.rfind(delim)
                    if pos != -1:
                        # Aceptar el delimitador si crea un fragmento de tamaño razonable
                        # o si el chunk_candidate ya es corto.
                        # (pos + len(delim)) es la longitud del fragmento que se crearía.
                        potential_chunk_length = pos + len(delim)
                        if potential_chunk_length > max_length // 4 or potential_chunk_length == len(chunk_candidate):
                            last_break = pos + len(delim)
                            break
                
                if last_break == -1 or last_break == 0: # Si no se encontró un delimitador preferido o está al inicio
                    # Intentar dividir por el último espacio para no cortar palabras.
                    pos = chunk_candidate.rfind(' ')
                    if pos != -1 and pos > max_length // 4: # Evitar fragmentos muy pequeños si es posible
                        last_break = pos + 1
                
                if last_break != -1 and last_break > 0: # Si se encontró un punto de división válido
                    chunks.append(text[current_pos : current_pos + last_break])
                    current_pos += last_break
                else: # Fallback: tomar el fragmento de max_length
                    chunks.append(text[current_pos : current_pos + max_length])
                    current_pos += max_length
        return [c.strip() for c in chunks if c.strip()]

    def text_to_speech(self, text):
        if not text or not text.strip():
            logging.warning("No hay texto para convertir a voz.")
            return [] # Devuelve una lista vacía si no hay texto

        text_chunks = self._split_text_into_chunks(text)
        generated_audio_paths = []
        # self.output_audio_path ahora es la ruta base SIN extensión
        base_output_path = self.output_audio_path 
        
        # Si usamos Piper, la extensión será .wav, si no, la que venga (ej. .mp3 para gTTS)
        output_extension = ".wav" if self.tts_engine == "piper" else ".mp3"
        temp_fragment_paths = [] # Para los fragmentos individuales
        for i, chunk in enumerate(text_chunks):
            if not chunk.strip(): continue
            chunk_audio_path = f"{base_output_path}_part_{i}{output_extension}"

            if self.tts_engine == "piper":
                if not self.piper_voice_key or self.piper_voice_key not in PIPER_VOICES:
                    logging.error(f"Clave de voz de Piper no válida o no proporcionada: {self.piper_voice_key}")
                    continue # O manejar el error de otra forma

                voice_config = PIPER_VOICES[self.piper_voice_key]
                piper_model_path = voice_config["model_path"]

                try:
                    if not os.path.exists(PIPER_EXECUTABLE_PATH):
                        logging.error(f"Piper ejecutable no encontrado en: {PIPER_EXECUTABLE_PATH}")
                        continue
                    if not os.path.exists(piper_model_path):
                        logging.error(f"Modelo de voz de Piper no encontrado en: {piper_model_path}")
                        continue

                    process = subprocess.Popen(
                        [
                            PIPER_EXECUTABLE_PATH,
                            "--model", piper_model_path,
                            "--output_file", chunk_audio_path
                        ],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0 # Evitar ventana de consola en Windows
                    )
                    stdout, stderr = process.communicate(input=chunk.encode('utf-8'))

                    if process.returncode != 0:
                        logging.error(f"Error al generar audio con Piper para el fragmento {i+1}: {stderr.decode('utf-8', errors='ignore')}")
                    else:
                        temp_fragment_paths.append(chunk_audio_path)
                        logging.info(f"Fragmento de audio {i+1}/{len(text_chunks)} generado con Piper ({self.piper_voice_key}): {chunk_audio_path}")
                except Exception as e_piper:
                    logging.error(f"Excepción al generar audio para el fragmento {i+1} con Piper ({self.piper_voice_key}): {e_piper}")

            elif self.tts_engine == "gtts":
                try:
                    tts = gTTS(text=chunk, lang=self.lang)
                    tts.save(chunk_audio_path)
                    generated_audio_paths.append(chunk_audio_path)
                    time.sleep(5) 
                    temp_fragment_paths.append(chunk_audio_path)
                    logging.info(f"Fragmento de audio {i+1}/{len(text_chunks)} generado con gTTS ({self.lang}): {chunk_audio_path}")
                except Exception as e_gtts:
                    logging.error(f"Error al generar audio para el fragmento {i+1} con gTTS: {e_gtts}")
            else:
                logging.error(f"Motor TTS no soportado: {self.tts_engine}")
        
        if not temp_fragment_paths:
            logging.warning("No se generaron fragmentos de audio.")
            return []

        # Unir los fragmentos
        combined_audio = AudioSegment.empty()
        final_audio_path_with_ext = f"{base_output_path}_full{output_extension}"

        try:
            for fragment_path in temp_fragment_paths:
                if output_extension == ".wav":
                    segment = AudioSegment.from_wav(fragment_path)
                elif output_extension == ".mp3":
                    segment = AudioSegment.from_mp3(fragment_path)
                else: # Por si acaso, aunque no debería llegar aquí con la lógica actual
                    segment = AudioSegment.from_file(fragment_path)
                combined_audio += segment
            
            combined_audio.export(final_audio_path_with_ext, format=output_extension.lstrip('.'))
            logging.info(f"Audio completo unido y guardado en: {final_audio_path_with_ext}")
            generated_audio_paths.append(final_audio_path_with_ext) # Devolver solo la ruta al archivo completo
        except Exception as e_combine:
            logging.error(f"Error al unir fragmentos de audio: {e_combine}")
            return [] # O devolver los fragmentos si la unión falla: return temp_fragment_paths
        finally:
            # Limpiar fragmentos temporales
            for fragment_path in temp_fragment_paths:
                if os.path.exists(fragment_path):
                    try:
                        os.remove(fragment_path)
                        logging.info(f"Fragmento temporal eliminado: {fragment_path}")
                    except Exception as e_clean:
                        logging.error(f"Error al eliminar fragmento temporal {fragment_path}: {e_clean}")
        return generated_audio_paths # Debería ser una lista con un solo elemento: el archivo unido

    def process(self, start_page=None, end_page=None):
        logging.info(f"Iniciando procesamiento para PDF: {self.pdf_path}")
        if start_page or end_page:
            logging.info(f"Rango de páginas solicitado: Inicio={start_page if start_page else 'N/A'}, Fin={end_page if end_page else 'N/A'}")
        text = self.extract_text_from_pdf_ocr(start_page=start_page, end_page=end_page)
        if text:
            cleaned_text = self.clean_text(text)
            if cleaned_text:
                self.save_to_txt(cleaned_text)
                audio_file_paths = self.text_to_speech(cleaned_text) # Ahora devuelve una lista
                
                if audio_file_paths:
                    logging.info(f"PDF procesado exitosamente. Texto: {self.output_txt_path}, Audios: {audio_file_paths}")
                    # Devolver las rutas para que el endpoint pueda crear URLs
                    return {"status": "success", "text_file": self.output_txt_path, "audio_files": audio_file_paths}
                else:
                    logging.warning("Texto procesado pero no se generaron archivos de audio.")
                    return {"status": "partial_success_no_audio", "text_file": self.output_txt_path, "audio_files": []}
            else:
                logging.warning("El texto quedó vacío después de la limpieza. No se generó salida.")
                return {"status": "failure_empty_text"}
        else:
            logging.warning("No se extrajo texto del PDF mediante OCR. No se generó salida.")
            return {"status": "failure_no_text_extracted"}

app = Flask(__name__)
swagger = Swagger(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/process-pdf', methods=['POST'])
def process_pdf_endpoint():
    """
    Procesa un archivo PDF para extraer texto y convertirlo a voz en múltiples partes si es necesario.
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: El archivo PDF a procesar.
      - name: lang
        in: formData
        type: string
        required: false
        default: 'es'
        description: Idioma para OCR y texto a voz (ej. 'es', 'en').
      - name: tts_engine
        in: formData
        type: string
        required: false
        default: 'gtts'
        description: Motor TTS a utilizar ('gtts' o 'piper').
      - name: piper_voice
        in: formData
        type: string
        required: false
        description: Clave de la voz de Piper a utilizar (ej. 'es_MX-claude-high'). Requerido si tts_engine es 'piper'.
      - name: start_page
        in: formData
        type: integer
        required: false
        description: Página de inicio para la extracción (1-indexado). Si se omite, comienza desde la primera página.
      - name: end_page
        in: formData
        type: integer
        required: false
        description: Página de fin para la extracción (1-indexado). Si se omite, procesa hasta la última página.
    responses:
      200:
        description: PDF procesado. Devuelve URL al archivo de texto y URLs a los archivos de audio generados.
        schema:
          type: object
          properties:
            message:
              type: string
            text_file_url:
              type: string
            audio_file_urls:
              type: array
              items:
                type: string
      400:
        description: Solicitud incorrecta (ej. sin archivo, tipo de archivo inválido).
      500:
        description: Error interno del servidor durante el procesamiento.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No se encontró la parte del archivo en la solicitud"}), 400
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({"error": "No se seleccionó ningún archivo o el archivo no tiene nombre"}), 400

    if file.filename.lower().endswith('.pdf'):
        input_pdf_path = "" # Para asegurar que esté definida en el bloque finally
        try:
            unique_id = str(uuid.uuid4())
            pdf_filename = f"{unique_id}.pdf"
            txt_filename = f"{unique_id}.txt"
            # El nombre base para los audios, la extensión se decidirá por el motor TTS
            audio_base_filename_no_ext = f"{unique_id}" 
            
            tts_engine = request.form.get('tts_engine', 'gtts').lower()
            piper_voice_key = request.form.get('piper_voice')
            
            input_pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
            output_txt_path = os.path.join(OUTPUT_FOLDER, txt_filename)
            output_audio_base_path = os.path.join(OUTPUT_FOLDER, audio_base_filename_no_ext)

            file.save(input_pdf_path)
            logging.info(f"PDF subido guardado en {input_pdf_path}")

            lang = request.form.get('lang', 'es')
            start_page_str = request.form.get('start_page')
            end_page_str = request.form.get('end_page')
            start_page, end_page = None, None

            try:
                if start_page_str:
                    start_page = int(start_page_str)
                    if start_page <= 0:
                        return jsonify({"error": "start_page debe ser un número positivo."}), 400
                if end_page_str:
                    end_page = int(end_page_str)
                    if end_page <= 0:
                        return jsonify({"error": "end_page debe ser un número positivo."}), 400
                if start_page and end_page and start_page > end_page:
                    return jsonify({"error": "start_page no puede ser mayor que end_page."}), 400
            except ValueError:
                return jsonify({"error": "start_page y end_page deben ser números enteros."}), 400

            if tts_engine == "piper" and not piper_voice_key:
                return jsonify({"error": "Se debe especificar 'piper_voice' cuando tts_engine es 'piper'."}), 400
            if tts_engine == "piper" and piper_voice_key not in PIPER_VOICES:
                return jsonify({"error": f"Clave de voz de Piper no válida: {piper_voice_key}. Voces disponibles: {list(PIPER_VOICES.keys())}"}), 400
            processor = PDFToAudioOCR(input_pdf_path, output_txt_path, output_audio_base_path, lang=lang, tts_engine=tts_engine, piper_voice_key=piper_voice_key)
            result = processor.process(start_page=start_page, end_page=end_page)

            if result["status"] == "success" or result["status"] == "partial_success_no_audio":
                text_file_url = None
                if result.get("text_file") and os.path.exists(result["text_file"]):
                    text_file_url = url_for('serve_output_file', filename=os.path.basename(result["text_file"]), _external=True)
                
                audio_file_urls = []
                if result.get("audio_files"):
                    for audio_path in result["audio_files"]:
                        if os.path.exists(audio_path):
                           audio_file_urls.append(url_for('serve_output_file', filename=os.path.basename(audio_path), _external=True))
                
                response_message = "PDF procesado."
                if result["status"] == "success" and audio_file_urls:
                    response_message = "PDF procesado exitosamente."
                elif result["status"] == "partial_success_no_audio":
                    response_message = "PDF procesado, texto extraído pero no se generaron audios."

                return jsonify({
                    "message": response_message,
                    "text_file_url": text_file_url,
                    "audio_file_urls": audio_file_urls
                }), 200
            else:
                if os.path.exists(input_pdf_path): os.remove(input_pdf_path)
                return jsonify({"error": f"Falló el procesamiento del PDF: {result['status']}. Revisa los logs."}), 500

        except pytesseract.TesseractNotFoundError:
            logging.error("Error de Tesseract no encontrado en el endpoint.")
            if input_pdf_path and os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            return jsonify({"error": "Error de configuración del servidor: Tesseract OCR no está instalado o configurado correctamente."}), 500
        except Exception as e:
            logging.error(f"Error en el endpoint /process-pdf: {e}", exc_info=True)
            if input_pdf_path and os.path.exists(input_pdf_path): os.remove(input_pdf_path)
            return jsonify({"error": f"Ocurrió un error interno: {str(e)}"}), 500
    else:
        return jsonify({"error": "Tipo de archivo inválido. Solo se aceptan archivos PDF."}), 400

@app.route('/outputs/<path:filename>', methods=['GET'])
def serve_output_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)

@app.route('/text-to-audio', methods=['POST'])
def text_to_audio_endpoint():
    """
    Convierte texto proporcionado a voz, generando múltiples archivos si el texto es largo.
    ---
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              description: El texto a convertir en audio.
            lang:
              type: string
              default: 'es'
              description: Idioma para la voz (ej. 'es', 'en').
            tts_engine:
              type: string
              default: 'gtts'
              description: Motor TTS a utilizar ('gtts' o 'piper').
            piper_voice:
              type: string
              required: false # Solo si tts_engine es piper
              description: Clave de la voz de Piper a utilizar (ej. 'es_MX-claude-high').
                           Requerido si tts_engine es 'piper'.
                           Ignorado si tts_engine es 'gtts'.
    responses:
      200:
        description: Audio generado. Devuelve URLs a los archivos de audio.
        schema:
          type: object
          properties:
            message:
              type: string
            audio_file_urls:
              type: array
              items:
                type: string
      400:
        description: Solicitud incorrecta (ej. falta texto, texto vacío).
      500:
        description: Error interno del servidor durante la generación del audio.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "Falta el campo 'text' en el cuerpo JSON"}), 400

    text_to_convert = data['text']
    lang = data.get('lang', 'es')

    if not text_to_convert.strip():
        return jsonify({"error": "El texto no puede estar vacío"}), 400

    tts_engine = data.get('tts_engine', 'gtts').lower()
    piper_voice_key = data.get('piper_voice')

    if tts_engine == "piper" and not piper_voice_key:
        return jsonify({"error": "Se debe especificar 'piper_voice' cuando tts_engine es 'piper'."}), 400
    if tts_engine == "piper" and piper_voice_key not in PIPER_VOICES:
        return jsonify({"error": f"Clave de voz de Piper no válida: {piper_voice_key}. Voces disponibles: {list(PIPER_VOICES.keys())}"}), 400

    # Usar una instancia temporal de PDFToAudioOCR para acceder a _split_text_into_chunks
    # y text_to_speech. Se pasa un nombre base para los archivos de audio.
    unique_id_base = str(uuid.uuid4())
    # La extensión se determinará dentro de text_to_speech basado en el engine
    temp_audio_base_filename_no_ext = f"direct_tts_{unique_id_base}" 
    temp_audio_base_path = os.path.join(OUTPUT_FOLDER, temp_audio_base_filename_no_ext)

    tts_processor = PDFToAudioOCR(pdf_path="", 
                                  output_txt_path="", 
                                  output_audio_path=temp_audio_base_path, # Pasamos la base sin extensión
                                  lang=lang, tts_engine=tts_engine, piper_voice_key=piper_voice_key)
    
    generated_audio_paths = []
    audio_file_urls = []

    try:
        generated_audio_paths = tts_processor.text_to_speech(text_to_convert)

        if not generated_audio_paths:
            # Si text_to_speech devuelve una lista vacía (ej. texto vacío o solo espacios)
            return jsonify({"message": "No se generaron archivos de audio para el texto proporcionado.", "audio_file_urls": []}), 200

        for audio_path in generated_audio_paths:
            if os.path.exists(audio_path):
                audio_file_urls.append(url_for('serve_output_file', filename=os.path.basename(audio_path), _external=True))

        return jsonify({
            "message": "Audio generado exitosamente en partes.",
            "audio_file_urls": audio_file_urls
        }), 200
    except Exception as e:
        logging.error(f"Error en el endpoint /text-to-audio: {e}", exc_info=True)
        # Limpiar archivos generados parcialmente si ocurre un error
        for path in generated_audio_paths: # Usa la lista de rutas que se intentaron generar
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e_clean:
                    logging.error(f"Error limpiando archivo temporal {path}: {e_clean}")
        return jsonify({"error": f"Ocurrió un error interno al generar el audio: {str(e)}"}), 500

if __name__ == "__main__":
    # Para ejecutar: flask run (después de export FLASK_APP=main.py) o python main.py
    app.run(debug=True, host='0.0.0.0', port=5000)