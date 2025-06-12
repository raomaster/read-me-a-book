# 📚 read-me-a-book

**read-me-a-book** es una herramienta para convertir PDFs (incluyendo escaneados) y texto en archivos de audio. Utiliza OCR para PDFs basados en imágenes y motores TTS locales o servicios gratuitos.


*Nota: Para el desarrollo de este proyecto, se utilizaron herramientas de IA como Gemini y ChatGPT como apoyo en la investigación y la realización de pruebas de concepto.*

---

## 🚀 Características Principales

-   📄 Extracción de texto desde PDFs (digitales y escaneados mediante OCR).
-   🗣️ Conversión de texto a voz utilizando:
    -   **gTTS**: Gratuito, online, fácil de usar.
    -   **Piper TTS**: Local, alta calidad, requiere configuración adicional.
-   ⚙️ Funciona 100% localmente (con Piper TTS) o con conexión a internet (con gTTS).
-   🎶 Une fragmentos de audio generados en un solo archivo (`_full.mp3` o `_full.wav`).
-   🌐 API RESTful con Flask y Swagger para una fácil integración.
-   📄 Soporte para procesar rangos de páginas específicos en PDFs.
-   🖼️ Preprocesamiento de imágenes (escala de grises, binarización con Otsu) para mejorar la precisión del OCR.


---

## ⚙️ Tecnologías utilizadas

-   **Python**: Lenguaje principal.
-   **Flask**: Para la API web.
-   **Flasgger**: Para la documentación Swagger UI.
-   **Pytesseract**: Para Tesseract OCR.
-   **pdf2image**: Para convertir PDFs a imágenes.
-   **gTTS**: Google Text-to-Speech.
-   **Piper TTS**: Motor TTS local (ejecutado a través de `subprocess`).
-   **Pydub**: Para manipulación y unión de audio.
-   **Pillow (PIL)**: Para manipulación de imágenes.
-   **OpenCV (cv2)**: Para preprocesamiento de imágenes.
-   **Numpy**: Para manipulación de arrays de imágenes.

---

## 🧰 Requisitos
- Python 3.10 o superior.
- Git
- **FFmpeg**: Necesario para `pydub` (manipulación de audio).
    -   Descárgalo desde ffmpeg.org.
    -   Asegúrate de añadir el directorio `bin` de FFmpeg a la variable de entorno PATH de tu sistema.

---
## 🛠️ Herramientas Externas Requeridas

### 1. Tesseract OCR
-   **Por qué**: Para extraer texto de PDFs escaneados (OCR).
-   **Instalación**:
    -   Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-spa`
    -   Windows: Descarga el instalador desde el repositorio oficial de Tesseract en GitHub (UB Mannheim). Durante la instalación, asegúrate de seleccionar los paquetes de idioma que necesites (ej. "Spanish"). Añade la ruta de instalación de Tesseract al PATH del sistema, o configúrala en `src/server.py` (variable `TESSERACT_INSTALL_PATH`).
    -   macOS: `brew install tesseract tesseract-lang`
    -   **Importante**: Para español, se recomienda descargar el archivo `spa.traineddata` (idealmente de `tessdata_best` para mayor precisión) y colocarlo en el directorio `tessdata` de tu instalación de Tesseract (link: https://github.com/tesseract-ocr/tessdata_best/blob/main/spa.traineddata ).
        -   Tessdata_best repository

### 2. Poppler
-   **Por qué**: `pdf2image` lo necesita para convertir PDFs a imágenes.
-   **Instalación**:
    -   Linux: `sudo apt-get install poppler-utils`
    -   **Windows**:
        1.  Descarga los binarios de Poppler. Algunas fuentes comunes son:
            *   Poppler for Windows (oschwartz10612) (busca la última versión, ej. `poppler-24.02.0-0.zip`).
            *   Poppler Binaries by UB Mannheim (a menudo referenciado en la documentación de `pdf2image`).
        2.  Extrae el contenido del archivo ZIP a una ubicación en tu sistema (ej. `C:\poppler-24.02.0`).
        3.  Añade la ruta a la subcarpeta `bin` (que usualmente está dentro de una carpeta como `Library` o directamente, ej. `C:\poppler-24.02.0\Library\bin` o `C:\poppler-24.02.0\bin`) al PATH de tu sistema.
        4.  **Alternativa (Recomendada para Windows)**: En lugar de modificar el PATH del sistema, puedes configurar la ruta a la carpeta `bin` de Poppler directamente en el archivo `src/server.py`. Busca la variable `POPPLER_PATH`, descoméntala si es necesario, y ajústala según tu instalación:
            ```python
            # En src/server.py, ajusta esta línea:
            # POPPLER_PATH = r"C:\Program Files\poppler-24.08.0\Library\bin" # ¡AJUSTA ESTA RUTA!
            ```
            El código en `src/server.py` ya está preparado para usar esta variable si está definida, pasándola al argumento `poppler_path` de `convert_from_path`.
    -   macOS: `brew install poppler`


### 3. Piper TTS (Opcional, para TTS local de alta calidad)

-   **Por qué**: Alternativa local a gTTS, ofrece voces de alta calidad y mayor control, funcionando offline.
-   **Instalación y Configuración**:
    1.  **Descarga el ejecutable de Piper TTS**: Ve al repositorio de Piper en GitHub y descarga la versión adecuada para tu sistema operativo.
    2.  **Coloca el ejecutable**: Guarda `piper.exe` (o el ejecutable correspondiente) en una ubicación accesible.
    3.  **Configura la ruta en `src/server.py`**: Ajusta la variable `PIPER_EXECUTABLE_PATH` en `src/server.py` para que apunte a tu ejecutable de Piper:
        ```python
        # En src/server.py, ajusta esta línea:
        PIPER_EXECUTABLE_PATH = r"C:\Ruta\A\Tu\piper\piper.exe" # ¡AJUSTA ESTA RUTA!
        ```
    4.  **Descarga modelos de voz**:
        *   Los modelos de voz para Piper (archivos `.onnx` y su correspondiente `.onnx.json`) se pueden encontrar en Hugging Face (rhasspy/piper-voices).
        *   Descarga los modelos que desees. Cada modelo generalmente viene con un archivo `.onnx` y un archivo `.onnx.json`.
    5.  **Organiza los modelos**:
        *   Crea una carpeta `models` en la raíz de tu proyecto (al mismo nivel que la carpeta `src`).
        *   Dentro de `models`, organiza los archivos de voz según la estructura esperada por la configuración `PIPER_VOICES` en `src/server.py`. Por ejemplo, para las voces configuradas:
            *   Para `"es_MX-claude-high"`:
                *   Crea la carpeta `models/es_MX/`.
                *   Coloca `es_MX-claude-high.onnx` (y su `.json` si existe) dentro de `models/es_MX/`.
            *   Para `"es_ES-mls_9972-low"`:
                *   Crea la carpeta `models/es_ES-mls_9972-low/`.
                *   Coloca `es_ES-mls_9972-low.onnx` (y su `.json` si existe) dentro de `models/es_ES-mls_9972-low/`.
            *   La estructura general sería:
                ```
                read-me-a-book/
                ├── models/
                │   ├── es_MX/
                │   │   ├── es_MX-claude-high.onnx
                │   │   └── es_MX-claude-high.onnx.json (si aplica)
                │   └── es_ES-mls_9972-low/
                │       ├── es_ES-mls_9972-low.onnx
                │       └── es_ES-mls_9972-low.onnx.json (si aplica)
                ├── src/
                │   └── server.py
                └── README.md
                ```
    6.  **Verifica/Configura las voces en `src/server.py`**: El diccionario `PIPER_VOICES` en `src/server.py` ya define las rutas. Asegúrate de que los nombres de archivo y las rutas coincidan con los modelos que has descargado y su ubicación.
        ```python
        # En src/server.py (esto ya está configurado, solo verifica que tus archivos coincidan):
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        PIPER_MODELS_BASE_DIR = os.path.join(PROJECT_ROOT, "models")

        PIPER_VOICES = {
            "es_MX-claude-high": {
                "model_path": os.path.join(PIPER_MODELS_BASE_DIR, "es_MX", "es_MX-claude-high.onnx"),
                "description": "Voz Claude en Español (México) - Alta calidad"
            },
            "es_ES-mls_9972-low": {
                "model_path": os.path.join(PIPER_MODELS_BASE_DIR, "es_ES-mls_9972-low", "es_ES-mls_9972-low.onnx"),
                "description": "Voz MLS en Español (España) - Baja calidad"
            }
            # Añade más voces aquí si es necesario, siguiendo el patrón de rutas.
        }
        ```

---

## 📦 Instalación del Proyecto

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/read-me-a-book.git # Reemplaza con la URL de tu repositorio
    cd read-me-a-book
    ```

2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    # En Windows
    venv\Scripts\activate
    # En macOS/Linux
    source venv/bin/activate
    ```

3.  **Instala las dependencias de Python:**
    ```bash
    pip install Flask flasgger gTTS pdf2image Pillow opencv-python pydub numpy pytesseract
    ```

---

## 🚀 Uso

1.  **Configura las rutas (si es necesario)**: Verifica que las rutas a Tesseract, Poppler (especialmente en Windows si no está en PATH), y Piper (ejecutable y modelos) estén correctamente configuradas en `src/server.py` como se describe en la sección "Herramientas Externas Requeridas".

2.  **Inicia el servidor Flask:**
    Desde el directorio raíz del proyecto (donde está la carpeta `src`):
    ```bash
    # Asegúrate de que tu entorno virtual esté activado

    # Opción 1: Ejecutando el script directamente (recomendado si __main__ está configurado)
    python src/server.py

    # Opción 2: Usando el comando flask
    # En macOS/Linux:
    # export FLASK_APP=src.server
    # En Windows (cmd):
    # set FLASK_APP=src.server
    # En Windows (PowerShell):
    # $env:FLASK_APP="src.server"
    #
    # flask run --host=0.0.0.0 --port=5000
    ```
    El servidor estará disponible en `http://localhost:5000` (o la IP y puerto que configure `app.run`).

3.  **Accede a la API:**
    -   **Swagger UI (documentación interactiva de la API)**: Abre tu navegador y ve a `http://localhost:5000/apidocs`
    -   **Endpoints principales**:
        -   `POST /process-pdf`: Sube un archivo PDF, extrae texto y lo convierte a audio.
        -   `POST /text-to-audio`: Convierte un texto JSON proporcionado a audio.
        -   `GET /outputs/<filename>`: Sirve los archivos de texto y audio generados.

### Ejemplo de uso con `curl` para `/process-pdf`:

```bash
curl -X POST -F "file=@/ruta/completa/a/tu/libro.pdf" \
             -F "lang=es" \
             -F "tts_engine=piper" \
             -F "piper_voice=es_MX-claude-high" \
             -F "start_page=5" \
             -F "end_page=10" \
             http://localhost:5000/process-pdf

```
Reemplaza /ruta/completa/a/tu/libro.pdf con la ruta real a tu archivo. Si usas gtts, cambia el motor y omite piper_voice: -F "tts_engine=gtts".

### Ejemplo de uso con curl para /text-to-audio:

```bash
curl -X POST -H "Content-Type: application/json" \
             -d '{
                   "text": "Hola mundo, esto es una prueba de conversión de texto a voz.",
                   "lang": "es",
                   "tts_engine": "gtts"
                 }' \
             http://localhost:5000/text-to-audio
```


Para usar Piper TTS:

```bash
curl -X POST -H "Content-Type: application/json" \
             -d '{
                   "text": "Hola mundo con Piper TTS.",
                   "lang": "es",
                   "tts_engine": "piper",
                   "piper_voice": "es_MX-claude-high"
                 }' \
             http://localhost:5000/text-to-audio

```

---
## 📁 Estructura de Carpetas Esperada

El servidor crea y utiliza las siguientes carpetas dentro del directorio raíz del proyecto:

uploads/: Para los archivos PDF subidos temporalmente.
outputs/: Para los archivos de texto (.txt) y audio (_full.mp3 o _full.wav) generados.
models/ (debes crearla tú y poblarla): Para almacenar los modelos de Piper TTS, como se describe en la sección de instalación de Piper.

---
## 📝 Notas Adicionales

Límites de gTTS: gTTS es un servicio online y puede tener límites en la longitud del texto o frecuencia de solicitudes. El script divide el texto en fragmentos más pequeños (basado en _split_text_into_chunks con max_length=48000) y añade un retraso (time.sleep(5)) entre fragmentos para mitigar problemas. Para textos muy largos o uso intensivo, Piper TTS (local) es más robusto.
Calidad de OCR: La calidad de la extracción de texto OCR depende en gran medida de la calidad del PDF escaneado. El preprocesamiento de imágenes implementado (escala de grises, binarización con Otsu) ayuda, pero los resultados pueden variar.
Configuración de Idioma: Asegúrate de que los paquetes de idioma correctos para Tesseract estén instalados (ej. spa para español, eng para inglés) y que el código de idioma (lang) proporcionado a la API sea compatible con los motores TTS y Tesseract. El script mapea es a spa y en a eng para Tesseract internamente.
Archivos de Salida: Los archivos de audio generados se guardan en la carpeta outputs/ con un nombre base único seguido de _full.mp3 (para gTTS) o _full.wav (para Piper TTS). Los archivos de texto también se guardan en outputs/ con un nombre único y extensión .txt.

---
## 🤝 Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue para discutir cambios o un pull request con tus mejoras.