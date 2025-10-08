import logging
from typing import Optional
from engines import create_engine

class TTSService:
    """Servicio principal para Text-to-Speech con fallback automático"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_audio(
        self, 
        text: str, 
        provider: str = 'gtts',
        lang: str = 'es',
        voice_name: Optional[str] = None
    ) -> bytes:
        """
        Genera audio usando el factory pattern con fallback automático.
        
        Args:
            text: Texto a convertir
            provider: Proveedor TTS ('gtts' o 'cloud_tts')
            lang: Código de idioma
            voice_name: Nombre de voz específico
            
        Returns:
            bytes: Audio en formato MP3
            
        Raises:
            Exception: Si todos los proveedores fallan
        """
        # Validar entrada
        if not text or not text.strip():
            raise ValueError("El texto no puede estar vacío")
            
        if len(text) > 5000:
            raise ValueError("El texto no puede exceder 5000 caracteres")
        try:
            # Intentar con el proveedor principal
            engine = create_engine(
                engine_type=provider,
                lang=lang,
                voice_name=voice_name
            )
            
            self.logger.info(f"Generando audio con {provider} para {len(text)} caracteres")
            return engine.text_to_bytes(text)
            
        except Exception as e:
            self.logger.warning(f"Error con {provider}: {e}")
            
            # Fallback a gTTS si el proveedor principal falla
            if provider != 'gtts':
                self.logger.info("Intentando fallback a gTTS")
                try:
                    fallback_engine = create_engine(
                        engine_type='gtts',
                        lang=lang
                    )
                    return fallback_engine.text_to_bytes(text)
                except Exception as fallback_error:
                    self.logger.error(f"Error en fallback gTTS: {fallback_error}")
                    raise fallback_error
            else:
                raise e