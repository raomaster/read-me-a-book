import datetime
import subprocess
from TTS.api import TTS as CoquiTTS
import time
import soundfile as sf
import torch
import torchaudio
from transformers import pipeline, AutoModelForCTC, AutoTokenizer, BarkModel, AutoProcessor
from bark import generate_audio, preload_models
from kokoro import KPipeline
import numpy as np


# ANSI escape codes para colores
COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"

class Logger:
    def info(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {COLOR_GREEN}[INFO]{COLOR_RESET} {message}")

    def warning(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {COLOR_YELLOW}[WARNING]{COLOR_RESET} {message}")

    def error(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {COLOR_RED}[ERROR]{COLOR_RESET} {message}")

log = Logger()

def generar_audio_coqui_tts(texto = "", archivo_salida="./output/audio_coqui.wav", archivo_sample="" ):
    """
    Genera audio con TTS Coqui.
    """
    starte_time = time.time()
    log.info("🚀 Generando audio con CoquiTTS...")

    tts = CoquiTTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    
    try:
        # Si se proporciona un archivo de sample, se utiliza para la generación
        if archivo_sample != "":
            log.info("⚙️ - Procesando archivo de sample...")

            tts.tts_to_file(text=texto, file_path=archivo_salida, speaker_wav=archivo_sample, language="es", split_sentences=True)
            end_time = time.time()
            generation_time = end_time - starte_time
            log.info(f"Tiempo de ejecución: {generation_time:2f} segundos")
        else:
            # Si no se proporciona un archivo de sample, se intenta generar con el speaker por defecto
            speakers = CoquiTTS.speakers
            log.info("⚙️ - Utilizando speaker por defecto...")

            if speakers:
                speaker = speakers[0]
                #tts.tts_to_file(text=texto, file_path=archivo_salida, speaker=speaker, language="es", split_sentences=True)
                audio = tts.synthesizer.sav (text=texto, speaker=speaker, language="es", split_sentences=True)
                audio.save(archivo_salida)
                end_time = time.time()
                generation_time = end_time - starte_time
                log.info(f"✅ Tiempo de ejecución: {generation_time:2f} segundos")
            else:
                log.warning("No se encontraron speakers disponibles.")
                return None
        return generation_time

    except Exception as e:
        log.error(f"❌ Error al generar el audio: {str(e)}")
        log.error(f"❌ Error: {e}")
        return None

    
def generar_audio_espeak_tts(texto = "", archivo_salida="./output/audio_espeak.wav"):
    start_time = time.time()
    log.info("🚀-- Generando audio con espeak...")

    try:
        comando = ["espeak-ng", "-v", "es", "-w", archivo_salida, texto]
        subprocess.run(comando, check=True)
        end_time = time.time()
        generation_time = end_time - start_time
        log.info(f"✅ Tiempo de ejecución: {generation_time:2f} segundos")
        return generation_time
    except FileExistsError as e:
        log.error(f"❌ Error al generar el audio: {str(e)}")
        return None
    except subprocess.CalledProcessError as e:
        log.error(f"❌ Error al generar el audio: {str(e)}")
        return None
    except Exception as e:
        log.error(f"❌ Error al generar el audio: {e}")
        return None
    
def generar_audio_huggingface_tts(texto = "", archivo_salida = "./output/audio_huggingface.wav",
                                    model_name = "suno/bark"):
    start_time = time.time()
    log.info("🚀 Generando audio con huggingface...")
    try:
        # processor: AutoProcessor.from_pretrained(model_name, cache_dir = local_model_path)
        # model = AutoModelForTextToSpeech.from_pretrained(model_name, cache_dir = local_model_path)
        # model = AutoModelForCTC.from_pretrained(model_name)
        # tokenizer = AutoTokenizer.from_pretrained(model_name)
        tts = pipeline("text-to-speech", model=model_name)
        

        speach = tts(texto)

        # Save to audio file
        sampling_rate = speach["sampling_rate"]
        torchaudio.save(archivo_salida, torch.from_numpy(speach["audio"]), sampling_rate, format="WAV")
        end_time = time.time()
        generation_time = end_time - start_time
        log.info(f"✅ Tiempo de ejecución: {generation_time:2f} segundos")
        return generation_time
    except FileExistsError as e:
        log.error(f"❌ Error al generar el audio: {str(e)}")
        return None
    except Exception as e:
        log.error(f"❌ Error general: {e}")
        log.error(f"❌ Error: {e}")
        return None
    

def generar_audio_bark(texto="", archivo_salida="./output/audio_bark.wav"):
    start_time = time.time()
    log.info("🚀 Generando audio con Bark...")
    try:
        preload_models(text_use_gpu=False, coarse_use_gpu=False, fine_use_gpu=False, codec_use_gpu=False)
        audio_array = generate_audio(
            texto,
            history_prompt="es_speaker_0",
            text_temp=0.7,
            waveform_temp=0.5,
            output_full=False
        )
        sf.write(archivo_salida, audio_array, 24000)
        end_time = time.time()
        log.info(f"✅ Tiempo de ejecución Bark: {end_time - start_time:.2f} segundos")
        return end_time - start_time
    except Exception as e:
        log.error(f"❌ Error Bark: {e}")
        return None

def generar_audio_kokoro(texto="", archivo_salida="./output/audio_kokoro.wav"):
    start_time = time.time()
    log.info("🚀 Generando audio con Kokoro...")
    try:
        pipeline = KPipeline(lang_code='e')
        generator = pipeline(texto, voice='ef_dora')
        for i, (gs, ps, audio) in enumerate(generator):
            sf.write(archivo_salida, audio, 24000)
            
        end_time = time.time()
        log.info(f"✅ Tiempo de ejecución Kokoro: {end_time - start_time:.2f} segundos")
        return end_time - start_time
    except Exception as e:
        log.error(f"❌ Error Kokoro: {e}")
        return None
    
if __name__ == "__main__":
    texto_prueba="""
    —¡Veinte grados más a babor! —exclamó en voz alta el teniente de guardia en el puente de mando de la corbeta General Baquedano.
    —¡Veinte grados más a babor! —repitió, como un eco, el timonel, mientras sus callosas manos daban vigorosas vueltas a las cabillas de la rueda del timón.
    Una ráfaga del noroeste recostó a la nave hasta hundirle la escoba de babor entre las grandes olas, cuyos negros lomos pasaban rodando hacia la oscuridad de la noche;
    el ulular del viento aumentó entre las jarcias, el velamen hizo crujir la envergadura, y el esbelto buque—escuela de la Armada de Chile, blanco como un albatros, puso proa
    rumbo al sur, empujado a doce millas por hora por la noroestada que pegaba por la aleta de estribor.
    """

    sample_audio = "samples/spanish_sample.wav"
    log.info("-- Iniciandobenchmark de generación de Audio   by Rick...")

    coqui_time = generar_audio_coqui_tts(texto=texto_prueba, archivo_sample="")

    """coqui_time = generar_audio_coqui_tts(texto=texto_prueba, archivo_sample=sample_audio)
    espeak_time = generar_audio_espeak_tts(texto=texto_prueba)
    huggingface_time = generar_audio_huggingface_tts(texto=texto_prueba)
    bark_time = generar_audio_bark(texto=texto_prueba)
    kokoro_time = generar_audio_kokoro(texto=texto_prueba)

    if coqui_time is not None:
        log.info(f"✅ Tiempo de ejecución Coqui: {coqui_time:2f} segundos")
    if espeak_time is not None:
        log.info(f"✅ Tiempo de ejecución Espeak: {espeak_time:2f} segundos")
    if huggingface_time is not None:
        log.info(f"✅ Tiempo de ejecución Huggingface: {huggingface_time:2f} segundos")
    if bark_time is not None:
        log.info(f"⏱️ Tiempo Bark: {bark_time:.2f} s")
    if kokoro_time is not None:
        log.info(f"⏱️ Tiempo Kokoro: {kokoro_time:.2f} s") """

    log.info("-- Fin del benchmark de generación de Audio   by Rick...")