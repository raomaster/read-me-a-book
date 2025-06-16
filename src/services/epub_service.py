import logging
from pathlib import Path
import subprocess
from ..config import CALIBRE_PATH


def convert_text_to_epub(text: str, input_txt_path: Path, output_epub_path: Path, title: str) -> Path:
    """Convierte una cadena de texto en un archivo EPUB unsando Calibre CLI

    Args:
        text (str): Contenido de texto completo a convertir
        input_txt_path (Path): Ruta temporal donde se guardara el texto
        output_epub_path (Path): Ruta donde se guarda el EPUB convertido
        title (str): Titulo que se le asignara al libro (metadatos del EPUB)

    Returns:
        Path: Ruta del archivo EPUB generado
    """         
    ebook_convert_cmd = CALIBRE_PATH or "ebook-convert"


    # Guardamos el texto en un archivo temporal
    # utf-8 por que es texto en español
    with open(input_txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    try:
        command = [
            ebook_convert_cmd,
            str(input_txt_path),
            str(output_epub_path),
            "--title", title,
            "--authors", "ReadMeABook",
            "--enable-heuristics",
            "--remove-paragraph-spacing"
        ]

        logging.info(f"Ejecutando comando: {' '.join(command)}")
        subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8")
    
    except FileNotFoundError:
        # Este error ocurre si el sistema no puede encontrar el comando 'ebook-convert_cmd'
        raise RuntimeError(f"Comando '{ebook_convert_cmd}' no encontrado. Asegúrate de que Calibre esté instalado y que la ruta en tu archivo .env sea correcta.")
    
    except subprocess.CalledProcessError as e:
        # Este error ocurre si Calibre se ejecuta pero falla por alguna razón interna.
        # Imprimir 'e.stderr' es vital para depurar qué salió mal.
        error_message = f"Calibre falló al convertir el archivo. Error: {e.stderr}"
        print(f"ERROR: {error_message}")
        raise RuntimeError(error_message)
    
    logging.info(f"Archivo EPUB generado en: {output_epub_path}")
    return output_epub_path



