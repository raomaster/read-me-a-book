from ..interfaces import TextToSpeechInterface
from .gtts_engine import GttsEngine
from .piper_engine import PiperEngine
from .xtts_engine import XttsEngine
from .kokoro_engine import KokoroEngine
from ..config import XTTS_CONFIG
from typing import Optional
import logging


def create_engine(
    engine_type: str,
    lang: str,
    piper_voice_key: Optional[str] = None,
    piper_executable_path: Optional[str] = None,
    piper_voices_config: Optional[dict] = None,
    xtts_speaker_wav: Optional[str] = None,
    xtts_speed: Optional[float] = None,
    xtts_temperature: Optional[float] = None,
    kokoro_voice: Optional[str] = None
) -> TextToSpeechInterface:
    if engine_type == "gtts":
        return GttsEngine(lang=lang)
    elif engine_type == "piper":
        if not piper_voice_key or not piper_executable_path or not piper_voices_config:
            logging.error("Piper enfine requiere piper_voice_key, piper_executable_path y piper_voices_config")
            raise ValueError("Piper engine requires piper_voice_key, piper_executable_path and piper_voices_config")
        
        if piper_voice_key not in piper_voices_config:
            logging.error(f"Clave de voz de Piper inválida: '{piper_voice_key}'")
            raise ValueError(f"Invalid Piper voice key: '{piper_voice_key}'")
            
        model_path = piper_voices_config[piper_voice_key]["model_path"]
        return PiperEngine(model_path=model_path, piper_executable_path=piper_executable_path)
    elif engine_type == "xtts":
        return XttsEngine(
            speaker_wav=xtts_speaker_wav,
            language=lang,
            speed=xtts_speed or XTTS_CONFIG["default_speed"],
            temperature=xtts_temperature or XTTS_CONFIG["default_temperature"]
        )
    elif engine_type == "kokoro":
        # Mapeo de idiomas a códigos de Kokoro según documentación oficial
        lang_mapping = {
            "es": "e",      # Spanish
            "en": "a",      # American English (por defecto)
            "en-gb": "b",   # British English
            "ja": "j",      # Japanese
            "zh": "z",      # Mandarin Chinese
            "fr": "f",      # French
            "hi": "h",      # Hindi
            "it": "i",      # Italian
            "pt": "p",      # Brazilian Portuguese
        }
        
        if lang not in lang_mapping:
            logging.warning(f"Idioma '{lang}' no soportado por Kokoro, usando 'es' por defecto")
            lang_code = "e"
            default_voice = "ef_dora"
        else:
            lang_code = lang_mapping[lang]
            # Voces por defecto según idioma
            default_voices = {
                "e": "ef_dora",   # Spanish
                "a": "af_heart",  # American English (mejor calidad)
                "b": "bf_emma",   # British English (mejor calidad)
                "j": "jf_alpha",  # Japanese
                "z": "zf_xiaobei", # Mandarin Chinese
                "f": "ff_siwis",  # French
                "h": "hf_alpha",  # Hindi
                "i": "if_sara",   # Italian
                "p": "pf_dora",   # Brazilian Portuguese
            }
            default_voice = default_voices.get(lang_code, "ef_dora")
        
        voice = kokoro_voice or default_voice
        return KokoroEngine(voice=voice, lang_code=lang_code)
    else:
        logging.error(f"Motor de texto no soportado: {engine_type}")
        raise ValueError(f"Unsupported text-to-speech engine: {engine_type}")
        
