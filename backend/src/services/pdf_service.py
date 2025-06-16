import logging
from pathlib import Path
import re 
from collections import defaultdict

from pdf2image import convert_from_path
from ..config import TESSERACT_PATH, POPPLER_PATH
import pytesseract
import fitz

# --- Constantes para la limpieza de texto ---
# Número mínimo de veces que un texto candidato a encabezado/pie de página debe aparecer para ser eliminado.
MIN_REPETITIONS_FOR_HEADER_FOOTER = 3
# Longitud mínima (en palabras) del texto acompañante para ser considerado en el conteo de frecuencia.
MIN_WORDS_FOR_CANDIDATE_TEXT = 1
# Longitud máxima (en palabras) del texto acompañante.
MAX_WORDS_FOR_CANDIDATE_TEXT = 10


if TESSERACT_PATH is not None:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def _clean_extracted_text_for_epub(text: str) -> str:
    """Limpia el texto extraído, intentando eliminar encabezados/pies de página."""
    if not text:
        return ""
    
    lines = text.splitlines()
    
    # --- Primera Pasada: Análisis de Frecuencia de Candidatos a Encabezado/Pie de Página ---
    header_candidate_counts = defaultdict(int)
    footer_candidate_counts = defaultdict(int)

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Candidato a encabezado: "NUMERO TEXTO"
        match_header = re.match(r'^(\d+)\s+(.+)', line_stripped)
        if match_header:
            text_part = match_header.group(2).strip()
            num_words = len(text_part.split())
            if MIN_WORDS_FOR_CANDIDATE_TEXT <= num_words <= MAX_WORDS_FOR_CANDIDATE_TEXT:
                header_candidate_counts[text_part.lower()] += 1
        
        # Candidato a pie de página: "TEXTO NUMERO"
        # Usamos una expresión regular que no sea codiciosa para el texto,
        # y que no confunda un número al final de una frase normal con un pie de página.
        match_footer = re.match(r'(.+?)\s+(\d+)$', line_stripped)
        if match_footer:
            text_part = match_footer.group(1).strip()
            num_words = len(text_part.split())
            if MIN_WORDS_FOR_CANDIDATE_TEXT <= num_words <= MAX_WORDS_FOR_CANDIDATE_TEXT:
                footer_candidate_counts[text_part.lower()] += 1

    # Identificar textos que se repiten lo suficiente para ser considerados encabezados/pies de página
    repetitive_header_texts = {
        text for text, count in header_candidate_counts.items() 
        if count >= MIN_REPETITIONS_FOR_HEADER_FOOTER
    }
    repetitive_footer_texts = {
        text for text, count in footer_candidate_counts.items()
        if count >= MIN_REPETITIONS_FOR_HEADER_FOOTER
    }

    logging.debug(f"Textos repetitivos de encabezado identificados: {repetitive_header_texts}")
    logging.debug(f"Textos repetitivos de pie de página identificados: {repetitive_footer_texts}")

    # --- Segunda Pasada: Limpieza de Líneas ---
    cleaned_lines = []
    for line in lines:
        line_stripped = line.strip()

        if not line_stripped:
            cleaned_lines.append(line) 
            continue

        # Eliminar líneas que son solo un número (número de página probable)
        if re.fullmatch(r'\d+', line_stripped):
            logging.debug(f"PDF Service: Eliminando línea solo con números: '{line_stripped}'")
            continue
        
        # Eliminar encabezados repetitivos identificados
        match_header = re.match(r'^(\d+)\s+(.+)', line_stripped)
        if match_header and match_header.group(2).strip().lower() in repetitive_header_texts:
            logging.debug(f"PDF Service: Eliminando encabezado repetitivo: '{line_stripped}'")
            continue
        
        # Eliminar pies de página repetitivos identificados
        match_footer = re.match(r'(.+?)\s+(\d+)$', line_stripped)
        if match_footer and match_footer.group(1).strip().lower() in repetitive_footer_texts:
            logging.debug(f"PDF Service: Eliminando pie de página repetitivo: '{line_stripped}'")
            continue
        
        cleaned_lines.append(line)
    
    return _normalize_text_spacing("\n".join(cleaned_lines))

def extract_text_from_pdf(pdf_path: Path)-> str:
    """Extrae texto desde un archivo PDF utilizando Tesseract OCR.
    Revisa si es neceario usar OCR o no

    Args:
        pdf_path (Path): path del pdf
    """
    text_result = ""

    try:
        with fitz.open(pdf_path) as doc:
            text_test = ""
            pages_to_check = min(2, doc.page_count)

            for page_number in range(pages_to_check):
                page = doc.load_page(page_number)
                text_page = page.get_text()
                text_test += text_page

            if len(text_test.strip()) < 150 and doc.page_count > 0: # Asegurarse que haya páginas
                logging.info(f"INFO: PDF '{pdf_path.name}' detectado como imagen o con muy poco texto. Iniciando OCR.")
                
                convert_kwargs = {}
                if POPPLER_PATH:
                    convert_kwargs['poppler_path'] = POPPLER_PATH
                
                # Asegurarse de que el PDF no esté vacío antes de intentar convertir
                if doc.page_count == 0:
                    logging.warning(f"PDF '{pdf_path.name}' no tiene páginas. No se puede procesar con OCR.")
                    text_result = ""
                else:
                    images = convert_from_path(pdf_path, **convert_kwargs)
                    text_parts = []
                    for i, image in enumerate(images):
                        logging.info(f"INFO: Procesando página {i+1}/{len(images)} con OCR...")
                        text_parts.append(pytesseract.image_to_string(image, lang='spa'))
                    text_result = "\n\n".join(text_parts)

            elif doc.page_count > 0: # Si hay texto y páginas
                logging.info(f"INFO: PDF '{pdf_path.name}' detectado como texto.")
                text_temp = "".join(doc[i].get_text() for i in range(pages_to_check, doc.page_count))
                text_result = text_test + text_temp
            else: # PDF sin páginas
                logging.warning(f"PDF '{pdf_path.name}' no tiene páginas. No se extrajo texto.")
                text_result = ""          

    except Exception as e:
        logging.error(f"Error al extraer texto del PDF '{pdf_path.name}': {e}")
        raise RuntimeError(f"Falló el procesamiento del PDF '{pdf_path.name}': {e}") from e

    cleaned_text_result = _clean_extracted_text_for_epub(text_result)
    
    if text_result and not cleaned_text_result and len(text_result.strip()) > 0 :
        logging.warning(f"El texto estaba presente en '{pdf_path.name}' pero quedó vacío después de la limpieza. Longitud original: {len(text_result)}")
    elif not text_result and pdf_path.exists() and pdf_path.stat().st_size > 0 : # Si el archivo existe y tiene tamaño pero no se extrajo texto
        logging.warning(f"No se extrajo texto de '{pdf_path.name}' (posiblemente vacío o formato no textual).")
    elif not text_result: # Si no se extrajo texto y el archivo podría no existir o ser 0 bytes
        logging.info(f"No se extrajo texto de '{pdf_path.name}'.")
    else:
        logging.info(f"Texto de '{pdf_path.name}' limpiado. Longitud original: {len(text_result)}, Longitud limpiada: {len(cleaned_text_result)}")

    return cleaned_text_result

def _normalize_text_spacing(text: str) -> str:
    """Normaliza saltos de línea y espacios para formar párrafos."""
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    paragraph_marker = "[[PARA_BREAK_MARKER_PDF_SERVICE]]"
    text = re.sub(r'\n\s*\n+', paragraph_marker, text)
    
    # Convertir saltos de línea simples restantes en espacios. Aquí "palabra-\nparte" se convierte en "palabra- parte".
    text = text.replace('\n', ' ')
    
    # Intentar desguionizar palabras que fueron divididas y ahora tienen un guion seguido de espacio.
    text = re.sub(r'([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+)-\s+([a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+)', r'\1\2', text)
    
    text = text.replace(paragraph_marker, '\n\n')
    text = re.sub(r' +', ' ', text)
    return text.strip()
