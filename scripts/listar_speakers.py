import pprint
from TTS.api import TTS as CoquiModernTTS

try:
    tts = CoquiModernTTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2")
    print("Listado de speakers y sus idiomas para el modelo XTTS-v2:")

    print("Speakers disponibles:")
    for speaker in tts.speakers:
        print(f"Speaker ID: '{speaker}'")
        pprint.pprint(speaker)
    print("Idiomas disponibles:")
    print(tts.languages)
except Exception as e:
    print(f"Ocurrió un error al cargar el modelo o acceder a los speakers: {e}")
    print("Asegúrate de tener la librería TTS instalada (`pip install TTS`) y conexión a internet la primera vez para descargar el modelo.")