#!/usr/bin/env python3
"""
Piper Test de Modelos - es_AR-daniela-high y es_ES-carlfm-high
Genera audio con ambos modelos usando el mismo texto de prueba que XTTS para comparación.
Llama a Piper por subprocess usando la configuración de config.py.
"""
import os
import sys
import subprocess
from pathlib import Path
import time
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))
from config import PIPER_EXECUTABLE_PATH, PIPER_MODELS_BASE_DIR

MODELS = [
    {
        "lang": "es_AR",
        "name": "es_AR-daniela-high",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high",
        "desc": "Femenina, Argentina, alta calidad"
    },
    {
        "lang": "es_ES",
        "name": "es_ES-carlfm-high",
        "url_base": "https://huggingface.co/friyin/vits-piper-es_ES-carlfm-high/resolve/main",
        "desc": "Femenina, España, alta calidad"
    },
    {
        "lang": "es_MX",
        "name": "es_MX-ald-medium",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium",
        "desc": "Femenina, México, calidad media-alta"
    },
    {
        "lang": "es_MX",
        "name": "es_MX-claude-high",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high",
        "desc": "Masculina, México, alta calidad"
    },
    {
        "lang": "es_ES-mls_9972-low",
        "name": "es_ES-mls_9972-low",
        "url_base": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES-mls_9972-low",
        "desc": "Femenina, España, calidad baja-media"
    },
    {
        "lang": "es_MX",
        "name": "es_MX-laura-high",
        "url_base": "https://huggingface.co/HirCoir/Piper-TTS-Laura/resolve/main",
        "desc": "Femenina, México, alta calidad (Laura)"
    }
    # Puedes agregar más modelos aquí si encuentras otros de voz femenina
]

TEXT = (
    "La mesa donde escribo no es precisamente un escritorio, pero es bonita. "
    "La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. "
    "Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. "
    "Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, "
    "y parece que me estuviera diciendo: 'Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?'"
)

OUTPUT_DIR = "output_piper"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_if_missing(url, path):
    import urllib.request
    if not os.path.isfile(path):
        print(f"Descargando {os.path.basename(path)}...")
        urllib.request.urlretrieve(url, path)
        print(f"✔ Descargado: {path}")
    else:
        print(f"✔ Ya existe: {path}")

def run_piper(model_path, config_path, text, output_file):
    command = [
        PIPER_EXECUTABLE_PATH,
        "-m", model_path,
        "-c", config_path,
        "-f", output_file,
        "--no-split",
        "-"
    ]
    print(f"Ejecutando: {' '.join(str(x) for x in command)}")
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate(input=text.encode('utf-8'))
    if process.returncode != 0:
        print(f"❌ Error ejecutando Piper: {stderr.decode('utf-8', 'ignore')}")
        raise RuntimeError(f"Piper falló con código {process.returncode}")
    print(f"✅ Audio generado: {output_file} ({os.path.getsize(output_file)/1024:.1f} KB)")
    return output_file

def test_piper_model(model_info):
    lang = model_info["lang"]
    name = model_info["name"]
    url_base = model_info["url_base"]
    desc = model_info.get("desc", "")
    model_dir = os.path.join(PIPER_MODELS_BASE_DIR, lang)
    model_path = os.path.join(model_dir, f"{name}.onnx")
    config_path = os.path.join(model_dir, f"{name}.onnx.json")
    os.makedirs(model_dir, exist_ok=True)
    download_if_missing(f"{url_base}/{name}.onnx", model_path)
    download_if_missing(f"{url_base}/{name}.onnx.json", config_path)
    print(f"\n🔄 Probando modelo: {name} - {desc}")
    output_file = os.path.join(OUTPUT_DIR, f"{name}_output.wav")
    start = time.time()
    run_piper(model_path, config_path, TEXT, output_file)
    elapsed = time.time() - start
    print(f"⏱️ Tiempo de generación: {elapsed:.2f} segundos")
    return output_file

def main():
    print("🎯 Piper - Prueba de Modelos es_AR-daniela-high y es_ES-carlfm-high (subprocess)")
    print("Generando audio con el mismo texto de XTTS para comparación.")
    print("=" * 80)
    results = []
    for model in MODELS:
        output = test_piper_model(model)
        results.append(output)
    print("\nRESULTADOS:")
    for output in results:
        print(f"   ✅ {output}")

if __name__ == "__main__":
    main() 