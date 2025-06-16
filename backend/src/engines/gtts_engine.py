import logging
from cv2 import log
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
