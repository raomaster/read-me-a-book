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
        
        print(f"✅ Audio saved to {output_path}")
