#!/bin/bash

# Activar conda (ajusta la ruta según tu sistema)
source ~/anaconda3/etc/profile.d/conda.sh
conda activate tts-env

# Instalar Coqui TTS desde el repositorio moderno
pip install --no-deps git+https://github.com/idiap/coqui-ai-TTS.git@main

# Instalar todas las dependencias desde requirements.txt
pip install -r requirements.txt