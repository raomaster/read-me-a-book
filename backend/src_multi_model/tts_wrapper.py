import os, sys

# Add Tortoise TTS to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "external", "tortoise-tts")))


class TTSWrapper:
    """
    Initializes the Tortoise TTS engine with a given voice and preset.

    :param voice: Voice name to use (default: 'random')
    :param preset: Quality preset ('ultra_fast', 'fast', 'standard', 'high_quality')
    """
    def __init__(self, engine="tortoise", voice='random', preset='fast'):
        """
        Initializes the TTSWrapper with the specified voice and preset.

        :param voice: Voice name to use (default: 'random')
        :param preset: Quality preset ('ultra_fast', 'fast', 'standard', 'high_quality')
        :param engine: Engine to use ('tortoise', 'coqui')
        """
        self.preset = preset
        self.voice = voice
        self.engine = engine.lower()

        if self.engine == "tortoise":
            from tortoise.api import TextToSpeech
            self.tts = TextToSpeech()
        elif self.engine == "coqui":
            from TTS.api import TTS as CoquiTTS
            from TTS.tts.configs.xtts_config import XttsConfig, XttsAudioConfig
            from torch.serialization import safe_globals
            from TTS.config.shared_configs import BaseDatasetConfig
            from TTS.tts.models.xtts import XttsArgs

            with safe_globals([XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs]):
                self.tts = CoquiTTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
        
        elif self.engine == "coqui-modern":
            import torch
            from TTS.api import TTS as CoquiModernTTS
            # from coqui_tts.inference import TTS as CoquiModernTTS
            device = "cuda" if torch.cuda.is_available() else "cpu"

            # List available 🐸TTS models
            print(f"Models: {CoquiModernTTS().list_models()}")
            print(f"Speakers:  {CoquiModernTTS().speakers}")

            self.tts = CoquiModernTTS(
                model_name="tts_models/multilingual/multi-dataset/xtts_v2"
            ).to(device)
        else:
            raise ValueError(f"Unknown engine: {self.engine}")


    def generate_audio(self, text, output_path="./output.wav"):
        """
        Generates audio from the given text and saves it to the specified output path.

        :param text: Text to generate audio from
        :param output_path: Path to save the generated audio
        """ 

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if self.engine == "tortoise":
            audio = self.tts.tts(text=text, voice=self.voice, preset=self.preset)
            self.tts.save_audio(audio, output_path)
        elif self.engine == "coqui":
            self.tts.tts_to_file(text=text, file_path=output_path, language="es", speaker_wav=self.voice, speed=1.05)
        elif self.engine == "coqui-modern":
            self.tts.tts_to_file(text=text, file_path=output_path, language="es", speaker_wav=self.voice, split_sentences=True,
            speed=1.0,
            temperature=0.1,
            emotion=None)    # Algunos modelos permiten esto (ver documentación).

        
        print(f"✅ Audio saved to {output_path}")
