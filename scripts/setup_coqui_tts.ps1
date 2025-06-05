# Activar entorno Conda (ajusta el nombre si es necesario)
conda activate tts-env

# Instalar Coqui TTS desde el repositorio moderno
pip install --no-deps git+https://github.com/idiap/coqui-ai-TTS.git@main

# Instalar todas las dependencias desde requirements.txt
pip install -r requirements.txt