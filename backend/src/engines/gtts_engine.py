import io
import logging
from gtts import gTTS
from ..interfaces import TextToSpeechInterface

class GttsEngine(TextToSpeechInterface):
    def __init__(self, lang='es'):
        self.lang = lang
        logging.info(f"GttsEngine Inicializado con idioma: {self.lang}")

    def text_to_speech(self, text: str, output_path: str) -> None:
        tts = gTTS(text=text, lang=self.lang)
        tts.save(output_path)
        logging.info(f"Audio guardado en: {output_path}")

    def text_to_bytes(self, text: str) -> bytes:
        tts = gTTS(text=text, lang=self.lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
