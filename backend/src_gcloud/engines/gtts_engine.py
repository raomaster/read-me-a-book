import io
import logging
from gtts import gTTS
from interfaces import TextToSpeechInterface

class GttsEngine(TextToSpeechInterface):
    """Engine para Google Text-to-Speech (gTTS)"""
    
    def __init__(self, lang: str = 'es'):
        self.lang = lang
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"GttsEngine inicializado con idioma: {self.lang}")

    def text_to_bytes(self, text: str) -> bytes:
        """Convierte texto a bytes de audio MP3"""
        try:
            tts = gTTS(text=text, lang=self.lang)
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            self.logger.error(f"Error en GttsEngine: {e}")
            raise