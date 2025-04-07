# 📚 read-me-a-book

**read-me-a-book** es una herramienta local para convertir cualquier texto o capítulo de libro en un archivo de audio de alta calidad, utilizando modelos de texto a voz (TTS) avanzados como Tortoise TTS y Coqui TTS. Ideal para crear tus propios audiolibros en casa, sin depender de servicios externos ni pagar suscripciones.

---

## 🚀 Características

- 🎙️ Conversión de texto a voz con calidad tipo narrador profesional
- 💻 Funciona 100% localmente (ideal para quienes cuidan su privacidad)
- 🧠 Compatible con GPU AMD (vía ONNX + DirectML) o solo CPU
- 📁 Entrada en `.txt` y salida en `.wav` o `.mp3`
- 🔁 Soporte para scripts automatizados por lotes

---

## ⚙️ Tecnologías utilizadas

- [Tortoise TTS](https://github.com/neonbjb/tortoise-tts) – para calidad ultra realista (modo CPU)
- [Coqui TTS](https://github.com/coqui-ai/TTS) – para rapidez y aceleración por GPU AMD
- [ONNX Runtime (DirectML)](https://onnxruntime.ai/) – permite usar tu tarjeta gráfica AMD

---

## 🧰 Requisitos

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Anaconda o Miniconda)
- Python 3.10 (se instala automáticamente con Conda)
- Git
- (Opcional) ffmpeg si quieres convertir `.wav` a `.mp3`

---

## 📦 Instalación (usando Conda)

```bash
git clone https://github.com/tu-usuario/read-me-a-book.git
cd read-me-a-book

# Crear entorno conda
conda create -n read-me-a-book python=3.10 -y
conda activate read-me-a-book

# Instalar PyTorch (versión CPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Instalar dependencias del motor TTS
pip install -r external/tortoise-tts/requirements.txt