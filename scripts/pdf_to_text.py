import logging
import sys
from pathlib import Path
from tqdm import tqdm
from pypdf import PdfReader
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PdfToText:
    def __init__(self, pdf_path: str, output_path: str, start_page: int = 0, end_page: int = None):
        self.pdf_path = Path(pdf_path)
        self.output_path = Path(output_path)
        self.start_page = start_page
        self.end_page = end_page    
        logger.info(f"📄 PDF de entrada: {self.pdf_path}")
        logger.info(f"📄 Texto de salida: {self.output_path}")
        logger.info(f"✅ Páginas: desde {start_page} hasta {end_page if end_page else 'fin'}")
    
    def extract_text_from_pdf(self):
        """
        Extracts text from a PDF.

        This function reads the PDF file at the provided path using pypdf,
        then extracts the text from each page. The extracted text is saved
        to the specified output path.

        :return: None
        """
        pdf = PdfReader(self.pdf_path)
        text = []

        start_page = int(self.start_page) - 1 # Convert to 0-indexed 
        end_page = int(self.end_page) - 1

        for page_number in tqdm(range(start_page, end_page + 1), desc="Extracting text from PDF"):
            page = pdf.pages[page_number]
            text_page = page.extract_text()
            if text_page is not None:
                text.append(text_page)
            else:
                print("No se pudo extraer texto de la página", page_number + 1)
        return '\n'.join(text)
        # page_number = int(self.start_page) - 1
        # page = pdf.pages[page_number]
        # text_page = page.extract_text()

        # """ with open(self.output_path, "w", encoding="utf-8") as f:
        #     f.write("\n".join(text)) """
        
        # if text_page is not None:
        #     print("Texto de la página", page_number + 1, ":", text_page)
        # else:
        #     print("No se pudo extraer texto de la página", page_number + 1)

        # return text

    def clean_text(self, text: str):
        """
        Cleans the text by removing empty lines and preserving
        only paragraphs with double spacing.

        :param text: Text to clean
        :return: Cleaned text
        """
        # Eliminar saltos de línea y espacios en blanco innecesarios
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # Eliminar caracteres de tabulación y reemplazarlos por espacios
        text = re.sub(r'\t', ' ', text)

        # Normalizar la indentación (reemplazar espacios de indentación por tabuladores)
        text = re.sub(r'^ +', '', text, flags=re.MULTILINE)

        # Eliminar espacios en blanco al principio y al final del texto
        text = text.strip()

        return text
    
    def save_text(self, text: str):
        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(text)
            logger.info(f"✅ Text saved to {self.output_path}")
        except Exception as e:
            logger.error(f"Error saving text to {self.output_path}: {e}")

    def run(self):
        """
        Extracts text from a PDF and saves it to a plain text file.

        This method first extracts raw text from all pages of the specified
        PDF file in `pdf_path` and stores it in a list. It then applies the
        `clean_text` function to clean the extracted text and saves the cleaned
        text to the file specified in `output_path`.

        :return: None
        """
        try:
                
            # Extract raw text from the PDF
            raw_text = self.extract_text_from_pdf()
            logger.info("✅ Text extracted from PDF")
            logger.info(f"Text {raw_text}")
            # Clean the extracted text
            final_text = self.clean_text(raw_text)
            logger.info("✅ Text cleaned")
            print(final_text)
            # Save the cleaned text to the output file
            self.save_text(final_text)
            logger.info(f"✅ Text saved to {self.output_path}")


        except Exception as e:
            logger.error(f"❌ Error general: {e}")

    

if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        print("Usage: python pdf_to_text.py <input_pdf> <output_text> [start_page] [end_page]")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_text = sys.argv[2]
    start_page = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    end_page = int(sys.argv[4]) if len(sys.argv) > 4 else None

    logger.info("🚀 Ejecutando extracción de PDF a texto...")

    pdf_to_text = PdfToText(input_pdf, output_text, start_page, end_page)

    pdf_to_text.run()

    logger.info("✅ Extracción de PDF a texto completada.")
