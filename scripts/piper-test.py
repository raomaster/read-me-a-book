import os

import urllib
from piper import PiperVoice
import soundfile as sf

MODEL_DIR="models/es_MX"
MODEL_NAME="es_MX-claude-high"
MODEL_URL_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high"

MODEL_PATH = os.joinpath(MODEL_DIR, f"{MODEL_NAME}.onnx")
CONFIG_PATH = os.joinpath(MODEL_DIR, f"{MODEL_NAME}.onnx.json")


# Crear carpeta si no existe
# pip install piper-tts soundfile
os.makedirs(MODEL_DIR, exist_ok=True)

# Descargar si no existe el modelo
def download_if_missing(url, path):
    if not os.path.isfile(path):
        print(f"Descargando {os.path.basename(path)}...")
        urllib.request.urlretrieve(url, path)
        print(f"✔ Descargado: {path}")
    else:
        print(f"✔ Ya existe: {path}")

download_if_missing(f"{MODEL_URL_BASE}/{MODEL_NAME}.onnx", MODEL_PATH)
download_if_missing(f"{MODEL_URL_BASE}/{MODEL_NAME}.onnx.json", CONFIG_PATH)

# Cargar voz

voice = PiperVoice(MODEL_PATH, CONFIG_PATH)

# Generar audio
audio = voice.generate_audio("Hola, ¿que tal?", "output.wav")