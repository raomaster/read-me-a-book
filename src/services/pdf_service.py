import logging
from pathlib import Path

from pdf2image import convert_from_path
from src.config import TESSERACT_PATH
import pytesseract
import fitz

if TESSERACT_PATH is not None:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def extract_text_from_pdf(pdf_path: Path)-> str:
    """Extrae texto desde un archivo PDF utilizando Tesseract OCR.
    Revisa si es neceario usar OCR o no

    Args:
        pdf_path (Path): path del pdf
    """
    text_result = ""

    try:
        # doc = fitz.open(pdf_path)
        with fitz.open(pdf_path) as doc:
            text_test = ""
            # Revisamos por defecto 2 paginas o el total de paginas (lo que sea menor)
            pages_to_check = min(2, doc.page_count)

            for page_number in range(pages_to_check):
                page = doc.load_page(page_number)
                text_page = page.get_text()
                text_test += text_page

            if len(text_test.strip()) < 150:
                # Entonces son imagenes
                logging.info(f"INFO: PDF '{pdf_path.name}' detectado como imagen. Iniciando OCR.")
                # Cerramos el documento de fitz antes del proceso de OCR que usa otra librería
                # El 'with' se encargará de esto automáticamente, pero al hacerlo explícito
                # liberamos el recurso antes.
                # Nota: pdf2image trabaja con la ruta, no con el objeto 'doc' abierto.
                doc.close() 

                images = convert_from_path(pdf_path)
                text_parts = []
                for i, image in enumerate(images):
                    logging.info(f"INFO: Procesando página {i+1}/{len(images)} con OCR...")
                    text_parts.append(pytesseract.image_to_string(image, lang='spa'))
                text_result = "\n\n".join(text_parts)

            else:
                logging.info(f"INFO: PDF '{pdf_path.name}' detectado como texto.")
                # Ya tenemos hemos extraido el texto inicial (ejemplo las primeras 2 paginas)
                text_temp = "".join(doc[i].get_text() for i in range(pages_to_check, doc.page_count))
                text_result = text_test + text_temp            

    except Exception as e:
        logging.error(f"Error al extraer texto del PDF: {e}")
        # Re-lanzamos una excepción más específica para que el endpoint la maneje
        raise RuntimeError(f"Falló el procesamiento del PDF '{pdf_path.name}': {e}") from e

    return text_result
