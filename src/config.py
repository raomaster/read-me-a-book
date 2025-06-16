import os
from pathlib import Path
from dotenv import load_dotenv

# Directorio base (equivalente a ./../)
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar archivo .env
load_dotenv(BASE_DIR / '.env')

TESSERACT_PATH = os.getenv("TESSERACT_CMD_PATH")
CALIBRE_PATH = os.getenv("CALIBRE_EBOOK_CONVERT_PATH")