import logging
import os
import json
import base64
from typing import Optional
from google.cloud import texttospeech
from google.oauth2 import service_account
from interfaces import TextToSpeechInterface

class CloudTTSEngine(TextToSpeechInterface):
    """Engine para Google Cloud Text-to-Speech"""
    
    def __init__(self, lang: str = 'es-ES', voice_name: Optional[str] = None):
        self.lang = lang
        self.voice_name = voice_name
        self.logger = logging.getLogger(self.__class__.__name__)
        
        try:
            # Resuelve credenciales desde variables de entorno en este orden:
            # 1) GCP_TTS_CREDENTIALS_JSON (JSON plano)
            # 2) GOOGLE_APPLICATION_CREDENTIALS_JSON (alias, JSON plano)
            # 3) GCP_TTS_CREDENTIALS_JSON_BASE64 (JSON en base64)
            # 4) GOOGLE_APPLICATION_CREDENTIALS (ruta a archivo)
            # 5) ADC por defecto (gcloud auth application-default login)
            creds = None

            json_env = os.getenv("GCP_TTS_CREDENTIALS_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            json_b64 = os.getenv("GCP_TTS_CREDENTIALS_JSON_BASE64")
            sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

            if json_env:
                try:
                    info = json.loads(json_env)
                    creds = service_account.Credentials.from_service_account_info(
                        info,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )
                except Exception as e:
                    # Evita romper si el JSON no es válido, continuará con otras opciones/ADC
                    self.logger.warning(f"No se pudo parsear GCP_TTS_CREDENTIALS_JSON: {e}")

            if creds is None and json_b64:
                try:
                    decoded = base64.b64decode(json_b64).decode("utf-8")
                    info = json.loads(decoded)
                    creds = service_account.Credentials.from_service_account_info(
                        info,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )
                except Exception as e:
                    self.logger.warning(f"No se pudo parsear GCP_TTS_CREDENTIALS_JSON_BASE64: {e}")

            if creds is None and sa_path and os.path.exists(sa_path):
                try:
                    creds = service_account.Credentials.from_service_account_file(
                        sa_path,
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )
                except Exception as e:
                    self.logger.warning(f"No se pudo cargar el archivo de credenciales: {e}")

            if creds is not None:
                self.client = texttospeech.TextToSpeechClient(credentials=creds)
            else:
                # Fallback a ADC (gcloud auth application-default login, o SA adjunta en Cloud Run/Functions)
                self.client = texttospeech.TextToSpeechClient()
                
            self.logger.info(f"CloudTTSEngine inicializado con idioma: {self.lang}")
        except Exception as e:
            self.logger.error(f"Error inicializando CloudTTSEngine: {e}")
            raise

    def text_to_bytes(self, text: str) -> bytes:
        """Convierte texto a bytes de audio MP3 usando Google Cloud TTS"""
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # NUEVO: si hay voice_name, derivar language_code del prefijo del nombre (ej. es-ES, es-US)
            resolved_lang = self.lang
            if self.voice_name:
                try:
                    parts = self.voice_name.split('-')
                    # Esperado: xx-YY-<Tier>-<...>
                    if len(parts) >= 2:
                        resolved_lang = f"{parts[0]}-{parts[1]}"
                except Exception:
                    pass

            voice = texttospeech.VoiceSelectionParams(
                language_code=resolved_lang,
                name=self.voice_name
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            return response.audio_content
        except Exception as e:
            self.logger.error(f"Error en CloudTTSEngine: {e}")
            raise