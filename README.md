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
```

---

### 🧰 Instalar dependencias de Tortoise TTS (sin deepspeed)

Para instalar solo las dependencias necesarias de Tortoise TTS (ignorando `deepspeed`):

```bash
python scripts/install_tortoise_deps.py
```

---

### 📌 Requisitos adicionales en Windows

Para que la instalación de Coqui TTS funcione correctamente en Windows, necesitas herramientas de compilación:

1. Instala [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Durante la instalación, marca la opción:

   ✅ **Desarrollo de escritorio con C++**

Esto instalará:
- MSVC v143 (compilador)
- Windows 10 SDK
- Herramientas de línea de comandos

Una vez instalado, **reinicia la terminal** y continúa con la instalación.

---

### 🗣️ Instalar dependencias de Coqui TTS

```bash
pip install -r requirements.txt
```



## 🔧 Instalación automática de dependencias

Este repositorio incluye scripts para instalar automáticamente las dependencias requeridas por `coqui-ai-TTS`.

### En Unix/macOS

```bash
bash scripts/install_requirements.sh
```

Asegúrate de darle permisos de ejecución si es necesario:

```bash
chmod +x scripts/install_requirements.sh
```

### En Windows PowerShell

```powershell
scripts\install_requirements.ps1
```

Ambos scripts instalarán las dependencias listadas en `scripts/requirements.txt`.
