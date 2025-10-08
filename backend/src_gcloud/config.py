import os
from dataclasses import dataclass
from typing import Optional, List

try:
    from dotenv import load_dotenv
    # Solo cargar .env cuando estamos en entorno local y no dentro de Cloud Functions/Run
    _env = os.getenv("ENVIRONMENT", os.getenv("ENVIROMENT", "production"))
    _is_cloud = bool(os.getenv("K_SERVICE") or os.getenv("FUNCTION_TARGET"))
    if not _is_cloud and _env == "local":
        load_dotenv()
except ImportError:
    # .env no presente en producción
    pass

@dataclass
class Config:
    # Corregimos los nombres de variables y ponemos producción por defecto
    environment: str = os.getenv("ENVIRONMENT", os.getenv("ENVIROMENT", "production"))
    google_cloud_project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "readme-a-book")
    firestore_project_id: str = os.getenv("FIRESTORE_PROJECT_ID", "readme-a-book")
    allowed_client_ids: List[str] = list(filter(None, os.getenv("ALLOWED_CLIENT_IDS", "").split(",")))
    default_language: str = os.getenv("DEFAULT_LANGUAGE", os.getenv("DEFAULT_LANTGUAGE", "es-ES"))
    max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", 5000))
    default_tts_provider: str = os.getenv("DEFAULT_TTS_PROVIDER", "google")
    audio_cache_max_age: int = int(os.getenv("AUDIO_CACHE_MAX_AGE", 3600))
    user_collection: str = os.getenv("USER_COLLECTION", "users")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def is_local(self) -> bool:
        return self.environment == 'local'
    
    @property
    def is_production(self) -> bool:
        return self.environment == 'production'

config = Config()