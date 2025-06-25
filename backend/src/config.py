import os
from pathlib import Path
from dotenv import load_dotenv

# Directorio base (equivalente a ./../)
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar archivo .env
load_dotenv(BASE_DIR / '.env')

TESSERACT_PATH = os.getenv("TESSERACT_CMD_PATH")
CALIBRE_PATH = os.getenv("CALIBRE_EBOOK_CONVERT_PATH")
POPPLER_PATH = os.getenv("POPPLER_PATH")


# Configuración de Piper
PIPER_EXECUTABLE_PATH_FROM_ENV = os.getenv("PIPER_EXECUTABLE_PATH")
PIPER_DEFAULT_EXECUTABLE_PATH = "piper"  # Valor por defecto si no está en .env
PIPER_EXECUTABLE_PATH = PIPER_EXECUTABLE_PATH_FROM_ENV or PIPER_DEFAULT_EXECUTABLE_PATH

PIPER_MODELS_BASE_DIR = BASE_DIR / "models"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Definición interna de voces para facilitar la construcción de rutas con Path
_PIPER_VOICES_CONFIG_RAW = {
    "es_MX-claude-high": {
        "model_path_relative": Path("es_MX") / "es_MX-claude-high.onnx",
        "description": "Voz Claude en Español (México) - Alta calidad"
    },
    "es_MX-ald-medium": {
        "model_path_relative": Path("es_MX") / "es_MX-ald-medium.onnx",
        "description": "Voz Claude en Español (México) - Alta calidad"
    },
    "es_ES-mls_9972-low": {
        "model_path_relative": Path("es_ES-mls_9972-low") / "es_ES-mls_9972-low.onnx",
        "description": "Voz MLS en Español (España) - Baja calidad"
    }
}

PIPER_VOICES_CONFIG = {
    key: {"model_path": str(PIPER_MODELS_BASE_DIR / value["model_path_relative"]), "description": value["description"]}
    for key, value in _PIPER_VOICES_CONFIG_RAW.items()
}

# Configuraciones de Streaming
STREAMING_CONFIG = {
    "chunk_size": 500,      # Tamaño máximo de cada chunk de texto
    "max_retries": 3,       # Máximo número de reintentos por chunk
    "timeout": 30,          # Timeout en segundos para generar audio
    "gtts_delay": 1.0,      # Delay entre chunks para gTTS (rate limiting)
    "piper_delay": 0.0,     # Delay entre chunks para Piper
}