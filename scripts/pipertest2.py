import os
from piper_onnx import Piper
import sounddevice as sd
import urllib

MODEL_DIR="models"
MODEL_LANG="es_MX"
MODEL_NAME="es_MX-claude-high"
MODEL_URL_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high"

MODEL_PATH = os.path.join(MODEL_DIR, MODEL_LANG, f"{MODEL_NAME}.onnx")
CONFIG_PATH = os.path.join(MODEL_DIR, MODEL_LANG, f"{MODEL_NAME}.onnx.json")


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

MODEL_PATH="models/es_MX/es_MX-claude-high.onnx"
CONFIG_PATH="models/es_MX/es_MX-claude-high.onnx.json"

with open(CONFIG_PATH, 'r', encoding='utf-8') as fp:
    piper = Piper(MODEL_PATH, fp)
# piper = Piper(MODEL_PATH, CONFIG_PATH)
# piper = Piper(MODEL_PATH, open(CONFIG_PATH, 'r', encoding='utf-8'))

texto_prueba="""
    —¡Veinte grados más a babor! —exclamó en voz alta el teniente de guardia en el puente de mando de la corbeta General Baquedano.
    —¡Veinte grados más a babor! —repitió, como un eco, el timonel, mientras sus callosas manos daban vigorosas vueltas a las cabillas de la rueda del timón.
    Una ráfaga del noroeste recostó a la nave hasta hundirle la escoba de babor entre las grandes olas, cuyos negros lomos pasaban rodando hacia la oscuridad de la noche;
    el ulular del viento aumentó entre las jarcias, el velamen hizo crujir la envergadura, y el esbelto buque—escuela de la Armada de Chile, blanco como un albatros, puso proa
    rumbo al sur, empujado a doce millas por hora por la noroestada que pegaba por la aleta de estribor.
    """
samples, sample_rate = piper.create(texto_prueba, "es-CL-CatalinaNeural")
sd.play(samples, sample_rate)
print('Playing...')
sd.wait()