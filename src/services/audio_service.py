from pathlib import Path

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup




def extract_text_from_epub(epub_file: Path) -> str:
    """
    Extrae todo el contenido de texto de un archivo EPUB

    Args:
        epub_file (Path): Ruta al archivo EPUB


    Returns:
        str: Texto con todo el contenido del EPUB
    """
    book = epub.read_epub(str(epub_file))
    text_parts = []
    # EPUB es un conjunto de "items" los cuales leeremos
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        # Usamos BeautifulSoup para parsear el contenido HTML de cada capitulo
        soup = BeautifulSoup(item.get_content(), 'html.parser')

        # Eliminamos estos tags que no contienen texto
        for tag in soup(['script', 'style']):
            tag.decompose()

        # Extraemos texto, usamos el separador de salto de linea y strip para eliminar espacion innecesarios
        text_temp = soup.get_text(separator='\n', trip=True)
        text_parts.append(text_temp)
    
    return "\n\n".join(text_parts)
    


def generate_audio_from_text(text: str, output_file: Path) -> Path:
    """Metodo que deberia generar el audio en base al engine que se seleccione

    Args:
        text (str): _description_
        output_file (Path): _description_

    Returns:
        Path: _description_
    """