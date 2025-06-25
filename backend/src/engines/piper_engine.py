import logging
import os
import json
import subprocess
import time
import tempfile
import io
import numpy as np
import soundfile as sf
from ..interfaces import TextToSpeechInterface


class PiperEngine(TextToSpeechInterface):
    def __init__(self, model_path: str, piper_executable_path: str):
        if not os.path.exists(piper_executable_path):
            logging.error(f"Piper ejecutable no encontrado en: {piper_executable_path}")
            raise FileNotFoundError(f"Piper ejecutable no encontrado en: {piper_executable_path}")
        if not os.path.exists(model_path):
            logging.error(f"Modelo de voz de Piper no encontrado en: {model_path}")
            raise FileNotFoundError(f"Modelo de voz de Piper no encontrado en: {model_path}")

        self.model_path = model_path
        self.piper_executable_path = piper_executable_path
        self.sample_rate = 16000  # Default sample rate, common for many TTS models

        # Leer la configuración del modelo para obtener la frecuencia de muestreo correcta
        config_path = model_path + ".json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "audio" in config and "sample_rate" in config["audio"]:
                    self.sample_rate = config["audio"]["sample_rate"]
                    logging.info(f"Frecuencia de muestreo para {os.path.basename(model_path)} establecida en {self.sample_rate} Hz desde el archivo de configuración.")
                else:
                    logging.warning(f"Archivo de configuración {config_path} encontrado, pero 'sample_rate' no especificado. Usando el valor por defecto de {self.sample_rate} Hz.")
        else:
            logging.warning(f"Archivo de configuración {config_path} no encontrado. Usando la frecuencia de muestreo por defecto de {self.sample_rate} Hz. Esto podría causar audio distorsionado.")

        logging.info(
            f"PiperEngine Inicializado con modelo: {self.model_path} y ejecutable: {self.piper_executable_path}"
        )

    def _generate_empty_wav(self) -> bytes:
        """Genera un pequeño archivo WAV silencioso."""
        logging.debug(f"Generating empty WAV with sample rate: {self.sample_rate} Hz")
        wav_buffer = io.BytesIO()
        silent_data = np.zeros(int(self.sample_rate * 0.1), dtype=np.int16) # 0.1 seconds of silence
        sf.write(wav_buffer, silent_data, samplerate=self.sample_rate, subtype='PCM_16', format='WAV')
        wav_buffer.seek(0)
        return wav_buffer.read()

    def text_to_speech(self, text: str, output_path: str) -> None:
        # Implementa la conversión de texto a voz usando Piper
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Directorio de salida creado: {output_dir}")

        try:
            command = [
                self.piper_executable_path,
                "--model", self.model_path,
                "--output_file", output_path
            ]
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            _, stderr_bytes = process.communicate(input=text.encode('utf-8'))

            if process.returncode != 0:
                raise Exception(f"Proceso Piper finalizó con código {process.returncode}: {stderr_bytes.decode('utf-8', 'ignore')}")
            
            logging.info(f"Audio generado con Piper y guardado en: {output_path}")

        except Exception as e:
            logging.error(f"Excepción durante la generación de audio con Piper: {e}")
            raise
    
    def text_to_bytes(self, text: str) -> bytes:
        # --- Implementación Robusta con Archivo Temporal ---
        tmp_wav_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav_file:
                tmp_wav_path = tmp_wav_file.name

            command = [
                self.piper_executable_path,
                "--model", self.model_path,
                "--output_file", tmp_wav_path
            ]
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            _, stderr_bytes = process.communicate(input=text.encode('utf-8'))

            if process.returncode != 0:
                stderr_decoded = stderr_bytes.decode('utf-8', errors='ignore').strip()
                error_message = f"Piper process exited with non-zero code {process.returncode} for text: '{text[:50]}...'"
                if stderr_decoded:
                    error_message += f" Stderr: {stderr_decoded}"
                logging.error(error_message)
                return self._generate_empty_wav()

            if not os.path.exists(tmp_wav_path) or os.path.getsize(tmp_wav_path) == 0:
                logging.error(f"Piper process succeeded (code 0) but output WAV file is missing or empty: {tmp_wav_path}. Text: '{text[:50]}...'")
                return self._generate_empty_wav()

            with open(tmp_wav_path, "rb") as f:
                audio_bytes = f.read()

            return audio_bytes

        except Exception as e:
            logging.error(f"Error al generar audio con Piper a bytes (método de archivo temporal): {e}", exc_info=True)
            return self._generate_empty_wav()
        finally:
            if tmp_wav_path and os.path.exists(tmp_wav_path):
                os.remove(tmp_wav_path)
