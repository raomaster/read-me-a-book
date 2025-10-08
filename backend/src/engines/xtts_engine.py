import logging
import os
import tempfile
import io
from typing import Optional
import numpy as np
import soundfile as sf
from ..interfaces import TextToSpeechInterface
from ..config import XTTS_CONFIG

try:
    from TTS.api import TTS
    import torch
    XTTS_AVAILABLE = True
    logging.info("Coqui TTS Community dependencies loaded successfully")
except ImportError as e:
    XTTS_AVAILABLE = False
    logging.warning(f"Coqui TTS dependencies not available: {e}")
    logging.warning("Install with: pip install coqui-tts torch torchaudio")


class XttsEngine(TextToSpeechInterface):
    """
    XTTS v2 Engine - Updated for Coqui TTS Community Version
    Compatible with Python Docker images without conda
    """
    
    def __init__(
        self,
        speaker_wav: Optional[str] = None,
        language: Optional[str] = None,
        speed: Optional[float] = None,
        temperature: Optional[float] = None,
        device: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        Initialize XTTS v2 engine.
        
        Args:
            speaker_wav: Path to speaker reference audio file (optional for default voice)
            language: Language code (es, en, fr, de, etc.) - uses config default if None
            speed: Speech speed multiplier (0.5 to 2.0) - uses config default if None
            temperature: Sampling temperature (0.1 to 1.0) - uses config default if None
            device: Device to use (cuda, cpu, or auto)
            model_name: Specific model to use (defaults to XTTS v2)
        """
        if not XTTS_AVAILABLE:
            raise ImportError(
                "Coqui TTS dependencies not available. "
                "Install with: pip install coqui-tts torch torchaudio"
            )
        
        self.speaker_wav = speaker_wav
        self.language = language or XTTS_CONFIG["default_language"]
        self.speed = speed or XTTS_CONFIG["default_speed"]
        self.temperature = temperature or XTTS_CONFIG["default_temperature"]
        
        # Use CPU by default, or specified device
        if device is None:
            self.device = "cpu"
        else:
            self.device = device
            
        logging.info(f"Initializing Coqui TTS engine on device: {self.device}")
        
        # Initialize TTS model
        try:
            # Use specified model or default to XTTS v2
            model_to_use = model_name or "tts_models/multilingual/multi-dataset/xtts_v2"
            
            self.tts = TTS(
                model_name=model_to_use,
                progress_bar=False,
                gpu=False if self.device == "cpu" else True
            )
            logging.info(f"Coqui TTS model '{model_to_use}' loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize Coqui TTS model: {e}")
            raise
        
        # XTTS v2 default sample rate from config
        self.sample_rate = XTTS_CONFIG["sample_rate"]
        
        logging.info(f"Coqui TTS engine initialized successfully")

    def _generate_empty_wav(self) -> bytes:
        """Generate a small silent WAV file as fallback."""
        logging.debug(f"Generating empty WAV with sample rate: {self.sample_rate} Hz")
        wav_buffer = io.BytesIO()
        silent_data = np.zeros(int(self.sample_rate * 0.1), dtype=np.int16)  # 0.1 seconds
        sf.write(wav_buffer, silent_data, samplerate=self.sample_rate, subtype='PCM_16', format='WAV')
        wav_buffer.seek(0)
        return wav_buffer.read()

    def text_to_speech(self, text: str, output_path: str) -> None:
        """Convert text to speech and save to file."""
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"Directorio de salida creado: {output_dir}")

        try:
            # Check if this is an XTTS model that needs speaker reference
            is_xtts_model = "xtts" in self.tts.model_name.lower()
            
            if is_xtts_model and self.speaker_wav:
                # Generate audio with XTTS parameters
                self.tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    language=self.language,
                    speaker_wav=self.speaker_wav,
                    speed=self.speed,
                    temperature=self.temperature,
                    split_sentences=False
                )
            else:
                # Generate audio with standard parameters
                self.tts.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speed=self.speed
                )
            
            logging.info(f"Audio generado con Coqui TTS y guardado en: {output_path}")
            
        except Exception as e:
            logging.error(f"Error durante la generación de audio con Coqui TTS: {e}")
            raise

    def text_to_bytes(self, text: str) -> bytes:
        """Generate audio and return as bytes."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # Check if this is an XTTS model that needs speaker reference
                is_xtts_model = "xtts" in self.tts.model_name.lower()
                
                if is_xtts_model and self.speaker_wav:
                    # Generate audio with XTTS parameters
                    self.tts.tts_to_file(
                        text=text,
                        file_path=tmp_path,
                        language=self.language,
                        speaker_wav=self.speaker_wav,
                        speed=self.speed,
                        temperature=self.temperature,
                        split_sentences=False
                    )
                else:
                    # Generate audio with standard parameters
                    self.tts.tts_to_file(
                        text=text,
                        file_path=tmp_path,
                        speed=self.speed
                    )
                
                # Read the generated audio file
                with open(tmp_path, "rb") as f:
                    audio_bytes = f.read()
                
                logging.info(f"Audio generado exitosamente con Coqui TTS: {len(audio_bytes)} bytes")
                return audio_bytes
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logging.error(f"Error al generar audio con Coqui TTS a bytes: {e}", exc_info=True)
            return self._generate_empty_wav()

                

