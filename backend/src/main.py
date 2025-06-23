import shutil
from typing import List, Optional, Text
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import uuid

from pydantic import BaseModel, Field # Para generar nombres de directorio únicos

from src.services.tts_chunk_service import generate_audio_with_chunking

# Servicios y motores
from .services.pdf_service import extract_text_from_pdf
from .services.epub_service import convert_text_to_epub
from .services.audio_service import extract_text_from_epub
from .engines.engine_factory import create_engine
from .interfaces import TextToSpeechInterface # Contrato
from .config import PIPER_EXECUTABLE_PATH, PIPER_VOICES_CONFIG, OUTPUTS_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
# --- Constantes ---
PDF_MEDIA_TYPE = "application/pdf"
EPUB_MEDIA_TYPE = "application/epub+zip"
MP3_MEDIA_TYPE = "audio/mpeg"
WAV_MEDIA_TYPE = "audio/wav"

TTS_PROVIDERS: List[str] = ["gtts", "piper"]
SUPPORTED_LANGUAGES: List[str] = ["es", "en"]

# Asegurarse de que el directorio de salidas principal exista
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# --- Modelos de Pydantic ---
class TextToAudioRequest(BaseModel):
    text: str = Field(..., description="El texto a convertir en audio.", min_length=1)

# --- Funciones Auxiliares ---
def save_upload_file_to_temp_sync(upload_file: UploadFile, temp_dir: Path) -> Path:
    """Guarda un UploadFile en un directorio temporal y devuelve la ruta."""
    temp_file_path = temp_dir / upload_file.filename
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
    return temp_file_path

def validate_tts_parameters(
    tts_provider: str,
    piper_voice_key: Optional[str],
    available_piper_voices_config: dict
):
    """Valida los parámetros del proveedor TTS y la voz de Piper."""
    if tts_provider == "piper":
        if not piper_voice_key:
            raise HTTPException(status_code=400, detail="Se requiere 'piper_voice_key' cuando se usa el motor Piper.")
        if piper_voice_key not in available_piper_voices_config:
            raise HTTPException(
                status_code=400,
                detail=f"Clave de voz de Piper inválida: '{piper_voice_key}'. Disponibles: {list(available_piper_voices_config.keys())}"
            )

app = FastAPI(
    title="Read Me a Book API",
    description="API para convertir documentos en audiolibros",
    version="1.0.1"
)

# Configuración de CORS
origins = [
    "http://localhost:5173", # Origen de tu SvelteKit en desarrollo
    # Añade aquí el origen de tu PWA en producción si es diferente
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/pdf_to_epub",
    summary="Convierte un PDF en un EPUB",
    tags=["PDF to EPUB"]
)
async def pdf_to_epub(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo PDF a convertir")
):
    """
    Convierte un PDF en un EPUB.

    Args:
        file (UploadFile, optional): Archivo PDF a convertir. Defaults to File(..., description="Archivo PDF a convertir").
        background_tasks (BackgroundTasks): Tareas en segundo plano para limpieza.
    """
    if file.content_type != PDF_MEDIA_TYPE:
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF.")
    
    # Crear un subdirectorio único dentro de OUTPUTS_DIR para esta solicitud
    request_specific_dir_name = str(uuid.uuid4())
    temp_dir = OUTPUTS_DIR / request_specific_dir_name
    temp_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_temp_dir():
        try:
            shutil.rmtree(temp_dir)
            logging.info(f"Directorio temporal {temp_dir} y su contenido eliminados.")
        except Exception as e:
            logging.error(f"Error al eliminar el directorio temporal {temp_dir}: {e}")

    try:
        input_pdf_path = save_upload_file_to_temp_sync(file, temp_dir)
        
        try:
            
            logging.info(f"Extrayendo texto del PDF: {input_pdf_path}")
            text_content = extract_text_from_pdf(input_pdf_path)

            if not text_content or not text_content.strip():
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF o el PDF está vacío.")

            # Generar un título de libro robusto
            raw_stem = input_pdf_path.stem
            book_title = raw_stem if raw_stem and not raw_stem.startswith('.') and len(raw_stem) > 0 else f"document_{uuid.uuid4().hex[:8]}"

            # Ruta temporal para el archivo de texto que Calibre usará (aunque el servicio lo crea)
            temp_txt_path = temp_dir / f"{book_title}.txt"
            output_epub_filename = f"{book_title}.epub" # Usar el book_title saneado
            output_epub_path = temp_dir / output_epub_filename

            logging.info(f"Convirtiendo texto a EPUB. Título: {book_title}")
            convert_text_to_epub(text_content, temp_txt_path, output_epub_path, title=book_title)
            
            logging.info(f"EPUB generado: {output_epub_path}")
            # background_tasks.add_task(cleanup_temp_dir) # Comentado para que los archivos persistan
            return FileResponse(str(output_epub_path), media_type=EPUB_MEDIA_TYPE, filename=output_epub_filename)

        except RuntimeError as e:
            logging.error(f"Error de servicio durante la conversión PDF a EPUB: {e}")
            cleanup_temp_dir() # Limpiar en caso de error antes de devolver FileResponse
            raise HTTPException(status_code=500, detail=f"Error en el procesamiento del PDF: {e}")
        except Exception as e:
            logging.error(f"Error inesperado durante la conversión PDF a EPUB: {e}")
            cleanup_temp_dir() # Limpiar en caso de error antes de devolver FileResponse
            raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {e}")
    except Exception as e: # Captura errores que puedan ocurrir antes del bloque try interno
        cleanup_temp_dir()
        logging.error(f"Error general antes del procesamiento principal en pdf_to_epub: {e}")
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado al configurar: {e}")
@app.post(
    "/epub_to_audio",
    summary="Convierte un EPUB en un libro de audio",
    tags=["EPUB to Audio"]
)
async def epub_to_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Archivo EPUB a convertir"),
    tts_provider: str = Query("piper", enum=TTS_PROVIDERS, description="Motor de texto a voz a usar"),
    lang: str = Query("es", enum=SUPPORTED_LANGUAGES, description="Idioma para TTS (principalmente para gTTS)"),
    piper_voice_key: Optional[str] = Query(None, description=f"Clave de voz de Piper (requerido si tts_provider es 'piper'). Disponibles: {list(PIPER_VOICES_CONFIG.keys())}")
):
    """
    Recibe un archivo EPUB, extrae su texto y lo convierte en un archivo de audio MP3
    usando el proveedor de TTS especificado.
    """
    if file.content_type != EPUB_MEDIA_TYPE:
        raise HTTPException(status_code=400, detail="El archivo debe ser un EPUB.")

    validate_tts_parameters(tts_provider, piper_voice_key, PIPER_VOICES_CONFIG)

    # Crear un subdirectorio único dentro de OUTPUTS_DIR para esta solicitud
    request_specific_dir_name = str(uuid.uuid4())
    temp_dir = OUTPUTS_DIR / request_specific_dir_name
    temp_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_temp_dir_audio():
        try:
            shutil.rmtree(temp_dir)
            logging.info(f"Directorio temporal de audio {temp_dir} y su contenido eliminados.")
        except Exception as e:
            logging.error(f"Error al eliminar el directorio temporal de audio {temp_dir}: {e}")
    try:
        input_epub_path = save_upload_file_to_temp_sync(file, temp_dir)

        try:
            logging.info(f"Extrayendo texto del EPUB: {input_epub_path}")
            text_content = extract_text_from_epub(input_epub_path)

            if not text_content or not text_content.strip():
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del EPUB o el EPUB está vacío.")

            logging.info(f"Creando motor TTS: {tts_provider} para idioma/voz: {lang if tts_provider=='gtts' else piper_voice_key}")
            tts_engine: TextToSpeechInterface = create_engine(
                engine_type=tts_provider,
                lang=lang,
                piper_voice_key=piper_voice_key,
                piper_executable_path=PIPER_EXECUTABLE_PATH,
                piper_voices_config=PIPER_VOICES_CONFIG
            )

            # Generar un nombre base robusto para los archivos de audio
            raw_audio_stem = input_epub_path.stem
            base_audio_name = raw_audio_stem if raw_audio_stem and not raw_audio_stem.startswith('.') and len(raw_audio_stem) > 0 else f"audio_{uuid.uuid4().hex[:8]}"

            output_extension = "mp3" if tts_provider == "gtts" else "wav"
            # final_output_audio_filename = f"{input_epub_path.stem}.{output_extension}"
            final_output_audio_filename = f"{base_audio_name}.{output_extension}" # Usar el base_audio_name saneado
            final_output_audio_path = temp_dir / final_output_audio_filename
            
            media_type = MP3_MEDIA_TYPE if tts_provider == "gtts" else WAV_MEDIA_TYPE

            # logging.info(f"Generando audio a: {output_audio_path}")
            # tts_engine.text_to_speech(text_content, str(output_audio_path))
            inter_chunk_delay = 1.0 if tts_provider == "gtts" else 0.0
            logging.info(f"Preparando para generar audio en: {final_output_audio_path}")
            try:
                generate_audio_with_chunking(
                    tts_engine=tts_engine,
                    text_content=text_content,
                    temp_dir=temp_dir,
                    base_filename=base_audio_name, # Usar el base_audio_name saneado
                    final_outputh_path=final_output_audio_path,
                    output_format=output_extension,
                    inter_chunk_delay=inter_chunk_delay
                )
            except Exception as e_chunk:
                logging.error(f"Error durante la generación de audio con fragmentación: {e_chunk}")
                # La limpieza de fragmentos individuales ya está en generate_audio_with_chunking
                raise HTTPException(status_code=500, detail=f"Error al procesar audio: {e_chunk}")


            if not final_output_audio_path.exists() or final_output_audio_path.stat().st_size == 0:
                logging.error(f"El archivo de audio no fue generado o está vacío: {final_output_audio_path}")
                raise HTTPException(status_code=500, detail="Error al generar el archivo de audio: el archivo no se creó o está vacío.")

            logging.info(f"Audio generado: {final_output_audio_path}")
            # background_tasks.add_task(cleanup_temp_dir_audio) # Comentado para que los archivos persistan
            return FileResponse(str(final_output_audio_path), media_type=media_type, filename=final_output_audio_filename)

        except ValueError as e: # Errores de create_engine
            logging.error(f"Error al crear el motor TTS: {e}")
            cleanup_temp_dir_audio()
            raise HTTPException(status_code=400, detail=f"Error de configuración del motor TTS: {e}")
        except FileNotFoundError as e: # Errores de PiperEngine si no encuentra ejecutable/modelo
            logging.error(f"Error de archivo no encontrado (TTS Engine): {e}")
            cleanup_temp_dir_audio()
            raise HTTPException(status_code=500, detail=f"Error de configuración del servidor TTS: {e}")
        except Exception as e:
            logging.error(f"Error inesperado durante la conversión EPUB a Audio: {e}")
            cleanup_temp_dir_audio()
            raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {e}")
    except Exception as e: # Captura errores que puedan ocurrir antes del bloque try interno
        cleanup_temp_dir_audio()
        logging.error(f"Error general antes del procesamiento principal en epub_to_audio: {e}")
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado al configurar: {e}")

@app.post(
    "/text_to_audio",
    summary="Convierte texto a un libro de audio",
    tags=["Text to Audio"]
)
async def text_to_audio(
    background_tasks: BackgroundTasks,
    text_input: TextToAudioRequest,
    tts_provider: str = Query("piper", enum=TTS_PROVIDERS, description="Motor de texto a utilizar"),
    lang: str = Query("es", enum=SUPPORTED_LANGUAGES, description="Idioma para TTS"),
    piper_voice_key: Optional[str] = Query(None, description=f"Clave de voz de Piper (requerido si tts_provider es 'piper'). Disponibles: {list(PIPER_VOICES_CONFIG.keys())}")
):
    """_summary_

    Args:
        background_tasks (BackgroundTasks): BackgroundTasks
        text_input (str, optional): Text to Process. Defaults to TextToAudioRequest.
        tts_provider (str, optional): TTS Engine to use. Defaults to Query("piper", enum=TTS_PROVIDERS, description="Motor de texto a utilizar").
        lang (str, optional): TTS Language. Defaults to Query("es", enum=SUPPORTED_LANGUAGES, description="Idioma para TTS").
        piper_voice_key (_type_, optional): TTS Voice Key. Defaults to Query(None, description=f"Clave de voz de Piper (requerido si tts_provider es 'piper'). Disponibles: {list(PIPER_VOICES_CONFIG.keys())}").
    """

    validate_tts_parameters(tts_provider=tts_provider, piper_voice_key=piper_voice_key, available_piper_voices_config=PIPER_VOICES_CONFIG)

    text_content = text_input.text
    if not text_content or not text_content.strip():
        raise HTTPException(status_code=400, detail="No se proporcionó texto para convertir.")

    # Crear un Subdirectorio dentro de OUTPUTS_DIR para esta solicitud
    request_specific_dir = str(uuid.uuid4())
    temp_dir = OUTPUTS_DIR / request_specific_dir
    temp_dir.mkdir(parents=True, exist_ok=True)


    def cleanup_temp_dir_audio():
        try:
            shutil.rmtree(temp_dir)
            logging.info(f"Directorio temporal de audio {temp_dir} y su contenido eliminados.")
        except Exception as e:
            logging.error(f"Error al eliminar al irectorio temporal de audio {temp_dir}: {e}")  

    try:
        logging.info(f"Creando motor TTS: {tts_provider}")
        tts_engine: TextToSpeechInterface = create_engine(
            engine_type=tts_provider,
            lang=lang,
            piper_voice_key=piper_voice_key,
            piper_executable_path=PIPER_EXECUTABLE_PATH,
            piper_voices_config=PIPER_VOICES_CONFIG
        )

        base_audio_name = f"audio_{uuid.uuid4().hex[:12]}"
        output_extension = "mp3" if tts_provider == "gtts" else "wav"
        final_output_audio_filename = f"{base_audio_name}.{output_extension}"
        final_output_audio_path = temp_dir / final_output_audio_filename
        media_type = MP3_MEDIA_TYPE if tts_provider == "gtts" else WAV_MEDIA_TYPE

        inter_chunk_delay = 1.0 if tts_provider == "gtts" else 0.0
        logging.info(f"Preparando para generar audio en: {final_output_audio_path}")

        try:
            generate_audio_with_chunking(
                tts_engine=tts_engine,
                text_content=text_content,
                temp_dir=temp_dir,
                base_filename=base_audio_name,
                final_outputh_path=final_output_audio_path,
                output_format=output_extension,
                inter_chunk_delay=inter_chunk_delay
            )
        except Exception as e_chunk:
            logging.error(f"Error durante la generación de audio con fragmentación: {e_chunk}")
            raise HTTPException(status_code=500, detail=f"Error al procesar audio: {e_chunk}")

        if not final_output_audio_path.exists() or final_output_audio_path.stat().st_size == 0:
            logging.error(f"El archivo de audio no fue generado o está vacío: {final_output_audio_path}")
            raise HTTPException(status_code=500, detail="Error al generar el archivo de audio: el archivo no se creó o está vacío.")

        logging.info(f"Audio generado: {final_output_audio_path}")
        # background_tasks.add_task(cleanup_temp_dir_audio) # Comentado para que los archivos persistan
        return FileResponse(str(final_output_audio_path), media_type=media_type, filename=final_output_audio_filename)
    
    except ValueError as e: # Errores de create_engine
        logging.error(f"Error al crear el motor TTS: {e}")
        cleanup_temp_dir_audio()
        raise HTTPException(status_code=400, detail=f"Error de configuración del motor TTS: {e}")
    except FileNotFoundError as e: # Errores de PiperEngine si no encuentra ejecutable/modelo
        logging.error(f"Error de archivo no encontrado (TTS Engine): {e}")
        cleanup_temp_dir_audio()
        raise HTTPException(status_code=500, detail=f"Error de configuración del servidor TTS: {e}")
    except Exception as e:
        logging.error(f"Error inesperado durante la conversión de Texto a Audio: {e}", exc_info=True)
        cleanup_temp_dir_audio()
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {e}")



if __name__ == "__main__":
    # Este bloque permite ejecutar la aplicación con:
    # 1. `python -m src.main` desde el directorio `backend/`
    # 2. `python -m backend.src.main` desde la raíz del monorepo (read-me-a-book/)
    import uvicorn
    # La cadena de la aplicación para uvicorn.run puede necesitar ser 'backend.src.main:app'
    # si se ejecuta desde la raíz del monorepo y 'backend' está en PYTHONPATH.
    # Para `python -m backend.src.main`, Uvicorn infiere la app correctamente.
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)