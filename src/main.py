from pypdf import PdfReader
import os
from gtts import gTTS
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


class PDFToAudioOCR:
    def __init__(self, pdf_path, output_txt_path, output_audio_path):
        self.pdf_path = pdf_path
        self.output_txt_path = output_txt_path
        self.output_audio_path = output_audio_path

    def read_pdf(self):
        with open(self.pdf_path, 'rb') as file:
            reader = PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        return text

    def clean_text(self, text):
        # Add any specific cleaning operations here
        return text.strip()

    def save_to_txt(self, text):
        with open(self.output_txt_path, 'w') as file:
            file.write(text)

    def text_to_speech(self, text):
        tts = gTTS(text=text, lang='es')
        tts.save(self.output_audio_path)

    def process(self):
        text = self.read_pdf()
        if text is not None:
            cleaned_text = self.clean_text(text)
            self.save_to_txt(cleaned_text)
            self.text_to_speech(cleaned_text)

if __name__ == "__main__":
    pdf_to_audio = PDFToAudioOCR('input.pdf', 'output.txt', 'output.mp3')
    pdf_to_audio.process()



