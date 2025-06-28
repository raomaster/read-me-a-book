from ..interfaces import TextToSpeechInterface
from .gtts_engine import GttsEngine
from .piper_engine import PiperEngine
from typing import Optional
import logging


def create_engine(
    engine_type: str,
    lang: str,
    piper_voice_key: Optional[str] = None,
    piper_executable_path: Optional[str] = None,
    piper_voices_config: Optional[dict] = None
) -> TextToSpeechInterface:
    if engine_type == "gtts":
        return GttsEngine(lang=lang)
    elif engine_type == "piper":
        if not piper_voice_key or not piper_executable_path or not piper_voices_config:
            logging.error("Piper enfine requiere piper_voice_key, piper_executable_path y piper_voices_config")
            raise ValueError("Piper engine requires piper_voice_key, piper_executable_path and piper_voices_config")
        
        model_path = piper_voices_config.get(piper_voice_key)["model_path"]
        return PiperEngine(model_path=model_path, piper_executable_path=piper_executable_path)
    else:
        logging.error(f"Motor de texto no soportado: {engine_type}")
        raise ValueError(f"Unsupported text-to-speech engine: {engine_type}")
        
