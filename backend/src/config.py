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
    "es_AR-daniela-high": {
        "model_path_relative": Path("es_AR") / "es_AR-daniela-high.onnx",
        "description": "Voz Daniela en Español (Argentina) - Femenina, alta calidad"
    },
    "es_ES-carlfm-high": {
        "model_path_relative": Path("es_ES") / "es_ES-carlfm-high.onnx",
        "description": "Voz Carlfm en Español (España) - Femenina, alta calidad"
    },
    "es_MX-claude-high": {
        "model_path_relative": Path("es_MX") / "es_MX-claude-high.onnx",
        "description": "Voz Claude en Español (México) - Masculina, alta calidad"
    },
    "es_MX-ald-medium": {
        "model_path_relative": Path("es_MX") / "es_MX-ald-medium.onnx",
        "description": "Voz Ald en Español (México) - Femenina, calidad media-alta"
    },
    "es_MX-laura-high": {
        "model_path_relative": Path("es_MX") / "es_MX-laura-high.onnx",
        "description": "Voz Laura en Español (México) - Femenina, alta calidad"
    },
    "es_ES-mls_9972-low": {
        "model_path_relative": Path("es_ES-mls_9972-low") / "es_ES-mls_9972-low.onnx",
        "description": "Voz MLS en Español (España) - Femenina, calidad baja-media"
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

# Configuraciones para Audio Completo (no streaming)
COMPLETE_AUDIO_CONFIG = {
    "chunk_size": 500,      # Chunks más pequeños para mejor rendimiento y más logs de progreso
    "max_retries": 3,       # Máximo número de reintentos por chunk
    "timeout": 60,          # Timeout más largo para archivos grandes
    "gtts_delay": 0.5,      # Delay reducido entre chunks para gTTS
    "piper_delay": 0.0,     # Sin delay para Piper (local)
}

# Configuración de XTTS v2
XTTS_CONFIG = {
    "default_speed": 1.0,           # Velocidad de habla por defecto
    "default_temperature": 0.1,     # Temperatura de muestreo por defecto
    "default_language": "es",       # Idioma por defecto
    "sample_rate": 24000,           # Frecuencia de muestreo de XTTS v2
    "supported_languages": ["es", "en", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu"]
}