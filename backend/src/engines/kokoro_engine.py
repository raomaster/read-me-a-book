import io
import logging
import soundfile as sf
import numpy as np
from kokoro import KPipeline
from ..interfaces import TextToSpeechInterface

class KokoroEngine(TextToSpeechInterface):
    def __init__(self, voice='ef_dora', lang_code='e'):
        """
        Inicializa el engine de Kokoro TTS
        
        Args:
            voice (str): Voz a usar según el idioma:
                - Español (e): 'ef_dora', 'em_alex', 'em_santa'
                - American English (a): 'af_heart', 'af_bella', 'af_nicole', etc.
                - British English (b): 'bf_alice', 'bf_emma', 'bf_isabella', etc.
                - Japanese (j): 'jf_alpha', 'jf_gongitsune', 'jf_nezumi', etc.
                - Mandarin Chinese (z): 'zf_xiaobei', 'zf_xiaoni', 'zf_xiaoxiao', etc.
                - French (f): 'ff_siwis'
                - Hindi (h): 'hf_alpha', 'hf_beta', 'hm_omega', 'hm_psi'
                - Italian (i): 'if_sara', 'im_nicola'
                - Brazilian Portuguese (p): 'pf_dora', 'pm_alex', 'pm_santa'
            lang_code (str): Código de idioma según documentación oficial
        """
        self.voice = voice
        self.lang_code = lang_code
        self.pipeline = None
        self._initialize_pipeline()
        logging.info(f"KokoroEngine inicializado con voz: {self.voice}, idioma: {self.lang_code}")

    def _initialize_pipeline(self):
        """Inicializa el pipeline de Kokoro"""
        try:
            self.pipeline = KPipeline(lang_code=self.lang_code)
            logging.info(f"Pipeline de Kokoro inicializado correctamente")
        except Exception as e:
            logging.error(f"Error al inicializar pipeline de Kokoro: {e}")
            raise

    def text_to_speech(self, text: str, output_path: str) -> None:
        """
        Convierte texto a voz y guarda el audio en un archivo
        
        Args:
            text (str): Texto a convertir
            output_path (str): Ruta donde guardar el archivo de audio
        """
        try:
            if self.pipeline is None:
                self._initialize_pipeline()
            
            if self.pipeline is None:
                raise RuntimeError("No se pudo inicializar el pipeline de Kokoro")
            
            generator = self.pipeline(text, voice=self.voice)
            for i, (gs, ps, audio) in enumerate(generator):
                # Guardar audio como WAV
                sf.write(output_path, audio, 24000)
                break  # Solo tomamos el primer resultado
            
            logging.info(f"Audio de Kokoro guardado en: {output_path}")
            
        except Exception as e:
            logging.error(f"Error en Kokoro text_to_speech: {e}")
            raise

    def text_to_bytes(self, text: str) -> bytes:
        """
        Convierte texto a voz y devuelve el audio como bytes
        
        Args:
            text (str): Texto a convertir
            
        Returns:
            bytes: Audio en formato WAV como bytes
        """
        try:
            if self.pipeline is None:
                self._initialize_pipeline()
            
            if self.pipeline is None:
                raise RuntimeError("No se pudo inicializar el pipeline de Kokoro")
            
            generator = self.pipeline(text, voice=self.voice)
            for i, (gs, ps, audio) in enumerate(generator):
                # Convertir audio a bytes WAV
                buffer = io.BytesIO()
                sf.write(buffer, audio, 24000, format='WAV')
                buffer.seek(0)
                return buffer.read()
            
            raise RuntimeError("No se generó audio")
            
        except Exception as e:
            logging.error(f"Error en Kokoro text_to_bytes: {e}")
            raise 