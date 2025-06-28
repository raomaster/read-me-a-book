import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from pathlib import Path
import logging
import struct
import platform # Importar platform para detectar el SO
import uuid
import asyncio # Importar asyncio para asyncio.sleep

from pydantic import BaseModel, Field # Para generar nombres de directorio únicos

from src.utils.text_splitter import split_text_into_chunks # New import for text splitting

from .services.pdf_service import extract_text_from_pdf
from .services.epub_service import convert_text_to_epub
from .services.audio_service import extract_text_from_epub
from .engines.engine_factory import create_engine
from .interfaces import TextToSpeechInterface # Contrato
from .config import PIPER_EXECUTABLE_PATH, PIPER_VOICES_CONFIG, OUTPUTS_DIR, STREAMING_CONFIG, COMPLETE_AUDIO_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Configuración específica para Windows: usar ProactorEventLoop para subprocessos
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    logging.info("Asyncio event loop policy set to WindowsProactorEventLoopPolicy.")

# --- Constantes ---
PDF_MEDIA_TYPE = "application/pdf"
EPUB_MEDIA_TYPE = "application/epub+zip"
MP3_MEDIA_TYPE = "audio/mpeg"
WAV_MEDIA_TYPE = "audio/wav"

TTS_PROVIDERS: List[str] = ["gtts", "piper"]
# SUPPORTED_LANGUAGES: List[str] = ["es", "en"] # Already defined in config.py if needed
SUPPORTED_LANGUAGES: List[str] = ["es", "en"]

# Asegurarse de que el directorio de salidas principal exista
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# --- Modelos de Pydantic ---
class TextToAudioRequest(BaseModel):
    text: str = Field(..., description="El texto a convertir en audio.", min_length=1)

# --- Funciones Auxiliares ---
def save_upload_file_to_temp_sync(upload_file: UploadFile, temp_dir: Path) -> Path:
    """Guarda un UploadFile en un directorio temporal y devuelve la ruta."""
    # Manejar caso donde filename puede ser None
    if upload_file.filename is None:
        filename = f"upload_{uuid.uuid4().hex[:8]}"
    else:
        filename = upload_file.filename
    temp_file_path = temp_dir / filename
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

def create_wav_header(sample_rate: int, channels: int = 1, sample_width: int = 2) -> bytes:
    """
    Genera un encabezado WAV de 44 bytes para streaming de datos PCM.
    Usa un tamaño de datos de placeholder máximo, ya que la longitud final es desconocida.
    """
    byte_rate = sample_rate * channels * sample_width
    block_align = channels * sample_width
    bits_per_sample = sample_width * 8
    max_size = 2**31 - 1  # Placeholder para un tamaño de archivo/datos muy grande

    header = bytearray()
    header.extend(b'RIFF')
    header.extend(struct.pack('<I', max_size))
    header.extend(b'WAVE')
    header.extend(b'fmt ')
    header.extend(struct.pack('<I', 16))  # Tamaño del sub-chunk fmt (16 para PCM)
    header.extend(struct.pack('<H', 1))   # Formato de audio (1 para PCM)
    header.extend(struct.pack('<H', channels))
    header.extend(struct.pack('<I', sample_rate))
    header.extend(struct.pack('<I', byte_rate))
    header.extend(struct.pack('<H', block_align))
    header.extend(struct.pack('<H', bits_per_sample))
    header.extend(b'data')
    header.extend(struct.pack('<I', max_size))
    return bytes(header)

def generate_audio_chunk_simple(tts_engine: TextToSpeechInterface, chunk: str, chunk_index: int) -> bytes:
    """
    Genera audio para un chunk con reintentos configurados.
    """
    for attempt in range(STREAMING_CONFIG["max_retries"]):
        try:
            return tts_engine.text_to_bytes(chunk)
        except Exception as e:
            logging.error(f"Error al generar chunk de audio {chunk_index + 1} (intento {attempt + 1}): {e}")
            if attempt == STREAMING_CONFIG["max_retries"] - 1:
                logging.error(f"Falló la generación del chunk {chunk_index + 1} después de {STREAMING_CONFIG['max_retries']} intentos")
                raise  # Re-lanzar la excepción después de todos los reintentos
    
    # Este punto nunca se debería alcanzar, pero por seguridad
    raise RuntimeError(f"No se pudo generar audio para el chunk {chunk_index + 1}")

app = FastAPI(
    title="Read Me a Book API",
    description="API para convertir documentos en audiolibros",
    version="1.0.1"
)

# Configuración de CORS
# Durante desarrollo permitimos cualquier origen para facilitar pruebas en red local
origins = ["*"]

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
    background_tasks: BackgroundTasks, # Necesario para la tarea de limpieza
    file: UploadFile = File(..., description="Archivo EPUB a convertir"),
    tts_provider: str = Query("piper", enum=TTS_PROVIDERS, description="Motor de texto a voz a usar"),
    lang: str = Query("es", enum=SUPPORTED_LANGUAGES, description="Idioma para TTS (principalmente para gTTS)"),
    piper_voice_key: Optional[str] = Query(None, description=f"Clave de voz de Piper (requerido si tts_provider es 'piper'). Disponibles: {list(PIPER_VOICES_CONFIG.keys())}")
):
    """
    Recibe un archivo EPUB, extrae su texto y lo convierte en un archivo de audio
    usando el proveedor de TTS especificado. El archivo se guarda en outputs/<uuid>/
    y se devuelve para descarga.
    """
    if file.content_type != EPUB_MEDIA_TYPE:
        raise HTTPException(status_code=400, detail="El archivo debe ser un EPUB.")

    validate_tts_parameters(tts_provider, piper_voice_key, PIPER_VOICES_CONFIG)

    # Crear un subdirectorio único dentro de OUTPUTS_DIR para esta solicitud
    output_uuid = str(uuid.uuid4())
    output_dir = OUTPUTS_DIR / output_uuid
    output_dir.mkdir(parents=True, exist_ok=True)

    def cleanup_temp_dir():
        try:
            shutil.rmtree(output_dir)
            logging.info(f"Directorio temporal {output_dir} y su contenido eliminados.")
        except Exception as e:
            logging.error(f"Error al eliminar el directorio temporal {output_dir}: {e}")

    try:
        # Guardar el EPUB subido en el directorio de salida
        input_epub_path = save_upload_file_to_temp_sync(file, output_dir)

        try:
            logging.info(f"Extrayendo texto del EPUB: {input_epub_path}")
            text_content = extract_text_from_epub(input_epub_path)

            if not text_content or not text_content.strip():
                cleanup_temp_dir()
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del EPUB o el EPUB está vacío.")

            # Guardar el texto extraído
            text_file_path = output_dir / "texto_extraido.txt"
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            logging.info(f"Texto extraído guardado en: {text_file_path}")

            logging.info(f"Creando motor TTS: {tts_provider} para idioma/voz: {lang if tts_provider=='gtts' else piper_voice_key}")
            tts_engine: TextToSpeechInterface = create_engine(
                engine_type=tts_provider,
                lang=lang,
                piper_voice_key=piper_voice_key,
                piper_executable_path=PIPER_EXECUTABLE_PATH,
                piper_voices_config=PIPER_VOICES_CONFIG
            )

            # Generar el audio completo usando chunks más grandes
            logging.info("Generando audio completo con chunks grandes...")
            
            # Dividir el texto en chunks más grandes para mejor calidad
            chunks = split_text_into_chunks(text_content, COMPLETE_AUDIO_CONFIG["chunk_size"])
            logging.info(f"Texto dividido en {len(chunks)} chunks de ~{COMPLETE_AUDIO_CONFIG['chunk_size']} caracteres")
            
            # Generar audio para cada chunk y concatenar
            audio_chunks = []
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                logging.info(f"Procesando chunk {i+1}/{len(chunks)} ({len(chunk)} caracteres)")
                
                # Reintentos para cada chunk usando configuración
                for attempt in range(COMPLETE_AUDIO_CONFIG["max_retries"]):
                    try:
                        chunk_audio = generate_audio_chunk_simple(tts_engine, chunk, i)
                        audio_chunks.append(chunk_audio)
                        break  # Éxito, continuar al siguiente chunk
                    except Exception as e:
                        logging.error(f"Error al generar chunk de audio {i+1} (intento {attempt + 1}): {e}")
                        if attempt == COMPLETE_AUDIO_CONFIG["max_retries"] - 1:
                            logging.error(f"Falló la generación del chunk {i+1} después de {COMPLETE_AUDIO_CONFIG['max_retries']} intentos")
                            raise  # Re-lanzar la excepción después de todos los reintentos
                
                # Delay entre chunks si es necesario
                if COMPLETE_AUDIO_CONFIG["gtts_delay"] > 0 and tts_provider == "gtts" and i < len(chunks) - 1:
                    await asyncio.sleep(COMPLETE_AUDIO_CONFIG["gtts_delay"])
            
            # Concatenar todos los chunks de audio
            audio_bytes = b''.join(audio_chunks)
            
            # Determinar extensión y media type
            audio_extension = "mp3" if tts_provider == "gtts" else "wav"
            media_type = MP3_MEDIA_TYPE if tts_provider == "gtts" else WAV_MEDIA_TYPE
            
            # Guardar el archivo de audio
            audio_filename = f"audio.{audio_extension}"
            audio_file_path = output_dir / audio_filename
            with open(audio_file_path, "wb") as f:
                f.write(audio_bytes)
            
            logging.info(f"Audio generado exitosamente: {len(audio_bytes)} bytes")
            logging.info(f"Archivo guardado en: {audio_file_path}")

            # Devolver el archivo de audio usando FileResponse
            return FileResponse(
                path=audio_file_path,
                media_type=media_type,
                filename=audio_filename,
                background=background_tasks.add_task(cleanup_temp_dir)
            )

        except ValueError as e:  # Errores de create_engine
            logging.error(f"Error al crear el motor TTS: {e}")
            cleanup_temp_dir()
            raise HTTPException(status_code=400, detail=f"Error de configuración del motor TTS: {e}")
        except FileNotFoundError as e:  # Errores de PiperEngine si no encuentra ejecutable/modelo
            logging.error(f"Error de archivo no encontrado (TTS Engine): {e}")
            cleanup_temp_dir()
            raise HTTPException(status_code=500, detail=f"Error de configuración del servidor TTS: {e}")
        except Exception as e:
            logging.error(f"Error inesperado durante la conversión EPUB a Audio: {e}")
            cleanup_temp_dir()
            raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {e}")
    except Exception as e:  # Captura errores que puedan ocurrir antes del bloque try interno
        cleanup_temp_dir()
        logging.error(f"Error general antes del procesamiento principal en epub_to_audio: {e}")
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado al configurar: {e}")

@app.post(
    "/text_to_audio",
    summary="Convierte texto a un libro de audio",
    tags=["Text to Audio"]
)
async def text_to_audio( # Removed background_tasks parameter as it's not used for streaming
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

    try:
        logging.info(f"Creando motor TTS: {tts_provider}")
        tts_engine: TextToSpeechInterface = create_engine(
            engine_type=tts_provider,
            lang=lang,
            piper_voice_key=piper_voice_key,
            piper_executable_path=PIPER_EXECUTABLE_PATH, # Ensure these are passed
            piper_voices_config=PIPER_VOICES_CONFIG # Ensure these are passed
        )

        # output_extension = "mp3" if tts_provider == "gtts" else "wav" # Removed: variable is unused
        media_type = MP3_MEDIA_TYPE if tts_provider == "gtts" else WAV_MEDIA_TYPE

        # Generator function to stream audio chunks
        async def audio_stream_generator():
            chunks = split_text_into_chunks(text_content, STREAMING_CONFIG["chunk_size"])
            inter_chunk_delay = STREAMING_CONFIG["gtts_delay"] if tts_provider == "gtts" else STREAMING_CONFIG["piper_delay"]
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Para Piper, necesitamos añadir el encabezado WAV al principio del stream
                if tts_provider == "piper" and i == 0:
                    # Asumimos que el motor tiene una propiedad 'sample_rate'
                    sample_rate = getattr(tts_engine, 'sample_rate', 16000)
                    yield create_wav_header(sample_rate)

                # Reintentos para cada chunk usando configuración
                for attempt in range(STREAMING_CONFIG["max_retries"]):
                    try:
                        audio_chunk = generate_audio_chunk_simple(tts_engine, chunk, i)
                        yield audio_chunk
                        break  # Éxito, continuar al siguiente chunk
                    except Exception as e:
                        logging.error(f"Error al generar chunk de audio {i+1} (intento {attempt + 1}): {e}")
                        if attempt == STREAMING_CONFIG["max_retries"] - 1:
                            logging.error(f"Falló la generación del chunk {i+1} después de {STREAMING_CONFIG['max_retries']} intentos")
                            break  # Fallar después de todos los reintentos
                
                if inter_chunk_delay > 0 and i < len(chunks) - 1:
                    await asyncio.sleep(inter_chunk_delay)
        # Return StreamingResponse
        return StreamingResponse(audio_stream_generator(), media_type=media_type)
    
    except ValueError as e: # Errores de create_engine
        logging.error(f"Error al crear el motor TTS: {e}")
        raise HTTPException(status_code=400, detail=f"Error de configuración del motor TTS: {e}")
    except FileNotFoundError as e: # Errores de PiperEngine si no encuentra ejecutable/modelo
        logging.error(f"Error de archivo no encontrado (TTS Engine): {e}")
        raise HTTPException(status_code=500, detail=f"Error de configuración del servidor TTS: {e}")
    except Exception as e:
        logging.error(f"Error inesperado durante la conversión de Texto a Audio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ocurrió un error inesperado: {e}")



if __name__ == "__main__":
    # Este bloque permite ejecutar la aplicación con:
    # 1. `python -m src.main` desde el directorio `backend/`
    # 2. `python -m backend.src.main` desde la raíz del monorepo (read-me-a-book/)
    import uvicorn
    # La cadena de la aplicación para uvicorn.run puede necesitar ser 'backend.src.main:app'
    # si se ejecuta desde la raíz del monorepo y 'backend' está en PYTHONPATH.
    # Para `python -m backend.src.main`, Uvicorn infiere la app correctamente.
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)