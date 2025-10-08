from typing import Optional
import logging
from interfaces import TextToSpeechInterface
from .gtts_engine import GttsEngine
from .cloud_tts_engine import CloudTTSEngine

logger = logging.getLogger(__name__)

# Configuración de idiomas soportados
LANGUAGE_MAPPING = {
    'es': 'es-ES',
    'en': 'en-US', 
    'fr': 'fr-FR',
    'de': 'de-DE',
    'it': 'it-IT',
    'pt': 'pt-BR'
}

SUPPORTED_ENGINES = ['gtts', 'cloud_tts']

def create_engine(
    engine_type: str,
    lang: str = 'es',
    voice_name: Optional[str] = None
) -> TextToSpeechInterface:
    """
    Factory para crear engines de TTS.
    
    Args:
        engine_type: Tipo de engine ('gtts' o 'cloud_tts')
        lang: Código de idioma (ej: 'es', 'en')
        voice_name: Nombre de voz específico (solo para cloud_tts)
        
    Returns:
        TextToSpeechInterface: Instancia del engine solicitado
        
    Raises:
        ValueError: Si el engine_type no es soportado
    """
    if engine_type not in SUPPORTED_ENGINES:
        logger.error(f"Motor de TTS no soportado: {engine_type}")
        raise ValueError(f"Unsupported TTS engine: {engine_type}. Supported: {SUPPORTED_ENGINES}")
    
    if engine_type == "gtts":
        return GttsEngine(lang=lang)
    
    elif engine_type == "cloud_tts":
        cloud_lang = LANGUAGE_MAPPING.get(lang, 'es-ES')
        return CloudTTSEngine(lang=cloud_lang, voice_name=voice_name)
    
    # Este punto nunca debería alcanzarse debido a la validación anterior
    raise ValueError(f"Unsupported TTS engine: {engine_type}")