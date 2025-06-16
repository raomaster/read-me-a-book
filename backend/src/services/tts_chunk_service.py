from ast import List
import logging
from pathlib import Path
from time import time
from pydub import AudioSegment
from src.interfaces import TextToSpeechInterface


def generate_audio_with_chunking(
        tts_engine: TextToSpeechInterface,
        text_content: str,
        temp_dir: Path,
        base_filename: str,
        final_outputh_path: Path,
        output_format: str,
        inter_chunk_delay: float = 0.0
) -> None:
    """Gener audio usando el engine correspondientes, dividiendo el texto en fragmentos

    Args:
        tts_engine (TextToSpeechInterface): Engine que implemente la interfaz
        text_content (str): todo el texto
        temp_dir (Path): dirección tempora.
        base_filename (str): _description_
        final_outputh_path (Path): _description_
        outp (_type_): _description_
        inter_chunk_delay (float, optional): _description_. Defaults to 0.0.
    """

    # Ajustar max_length. El valor original de 45000 era muy alto, causando lentitud.
    # Si valores más bajos (ej. ~2000) resultaron en fragmentos percibidos como muy pequeños,
    # se prueba un valor intermedio para balancear rendimiento y tamaño de fragmento.
    text_chunk = _split_text_into_chunks(text_content, max_length=5000)

    if not text_chunk:
        logging.warning("No se pudo dividir el texto en fragmentos")
        raise ValueError("No se pudo dividir el texto en fragmentos")
    
    logging.info(f"Texto dividido en {len(text_chunk)} fragmentos")

    temp_chunk_files: List[Path] = []
    try:

        for i, chunk in enumerate(text_chunk):
            chunk_filename = f"{base_filename}_part_{i}.{output_format}"
            chunk_audio_path = temp_dir / chunk_filename
            logging.info(f"Generando fragmento de audio {i+1}/{len(text_chunk)}")
            tts_engine.text_to_speech(chunk, str(chunk_audio_path))
            if not chunk_audio_path.exists() or chunk_audio_path.stat().st_size == 0:
                raise RuntimeError(f"Fallo al generar el fragmento de audio {i+1}.")
            
            temp_chunk_files.append(chunk_audio_path)
            if inter_chunk_delay > 0.0:
                logging.debug(f"Esperando {inter_chunk_delay}s despues de tener texto.")
                time.sleep(inter_chunk_delay)
        
        if not temp_chunk_files:
            logging.error("No se generaron fragmentos de audio a pesar de tener texto")
            raise RuntimeError("No se puedieron generar fragmentos de audio.")
        # Si se generaron fragmentos de audio, entonces los unimos todos en uno
        logging.info("Uniendo fragmentos de audio")
        # Partimos con un audio vacio
        combined_audio = AudioSegment.empty()
        for chunk_path in temp_chunk_files:
            segment = AudioSegment.from_file(str(chunk_path), format=output_format)
            combined_audio += segment
        combined_audio.export(str(final_outputh_path), format=output_format)

        logging.info(f"Audio compelto unido y guardado en: {final_outputh_path}")
          
    except Exception as e:
        logging.error(f"No se pudo generar el audio: {e}")
    finally:
        logging.debug(f"Limpiando {len(temp_chunk_files)} archivos temporales")
        for chunk_file_to_delete in temp_chunk_files:
            if chunk_file_to_delete.exists():
                try:
                    chunk_file_to_delete.unlink(missing_ok=True)
                except Exception as e_clean:
                    logging.warning(f"Error eliminando fragmento temporal {chunk_file_to_delete}: {e_clean}")


def _split_text_into_chunks(text: str, max_length: int) -> list[str]:
    """Divide el texto en fragmentos intentando respetar finales de oración/párrafo

    Args:
        text (str): Texto completo
        max_length (int): Máximo largo de cada fragmento


    Returns:
        list[str]: Lista de fragmentos
    """
    chunks = []
    current_pos = 0
    text_length = len(text)

    if not text.strip():
        return []

    while current_pos < text_length:
        if text_length - current_pos < max_length:
            chunks.append(text[current_pos:])
            break
        else:
            chunk_candidate = text[current_pos:current_pos + max_length]
            last_break = -1

            # Posibles finales de texto o párrafo
            delimeters = ['\n\n', '. ', '.\n', '! ', '!\n', '? ', '?\n', '\n', ' ']

            for delim in delimeters:
                pos = chunk_candidate.rfind(delim)
                if pos != -1:
                    if pos + len(delim) > max_length // 10 or len(chunk_candidate) < max_length // 5 :
                        last_break = pos + len(delim)
                        break
            if last_break != -1 and last_break > 0:
                chunks.append(text[current_pos : current_pos + last_break])
                current_pos += last_break
            else: 
                chunks.append(text[current_pos : current_pos + max_length])
                current_pos += max_length
    return [c.strip() for c in chunks if c.strip()]
