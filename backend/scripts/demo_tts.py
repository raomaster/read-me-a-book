#!/usr/bin/env python3
"""
Script para probar diferentes opciones de TTS en español
Optimizado para CPU y compatible con AMD graphics
"""

import os
import time
import torch

# Configurar para usar solo CPU si es necesario
if os.getenv('CPU_ONLY'):
    torch.set_num_threads(4)  # Limitar threads para mejor rendimiento

def test_coqui_xtts():
    """Probar Coqui TTS XTTS-v2"""
    print("🎤 Probando Coqui TTS XTTS-v2...")
    try:
        from TTS.api import TTS
        
        # Cargar modelo
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", 
                  device="cpu")
        
        # Texto de prueba
        texto = "Hola, soy una voz generada por inteligencia artificial usando XTTS versión 2."
        
        # Necesitas un archivo de referencia de voz (3-10 segundos)
        # Si no tienes uno, el modelo usará una voz por defecto
        start_time = time.time()
        
        tts.tts_to_file(
            text=texto,
            language="es",
            file_path="output_xtts.wav"
        )
        
        end_time = time.time()
        print(f"✅ XTTS-v2 completado en {end_time - start_time:.2f} segundos")
        print(f"📁 Archivo guardado: output_xtts.wav")
        
    except Exception as e:
        print(f"❌ Error con XTTS-v2: {e}")

def test_bark():
    """Probar Bark TTS"""
    print("\n🐕 Probando Bark TTS...")
    try:
        from bark import SAMPLE_RATE, generate_audio, preload_models
        from scipy.io.wavfile import write as write_wav
        
        # Precargar modelos (puede tardar la primera vez)
        print("Descargando modelos de Bark (primera vez)...")
        preload_models()
        
        # Texto con prompt para español
        texto = "♪ [es] ¡Hola! Soy una voz generada con Bark. ¿Qué tal sueno?"
        
        start_time = time.time()
        audio_array = generate_audio(texto)
        write_wav("output_bark.wav", SAMPLE_RATE, audio_array)
        end_time = time.time()
        
        print(f"✅ Bark completado en {end_time - start_time:.2f} segundos")
        print(f"📁 Archivo guardado: output_bark.wav")
        
    except Exception as e:
        print(f"❌ Error con Bark: {e}")

def test_piper():
    """Probar Piper TTS (alternativa ligera)"""
    print("\n🪈 Probando Piper TTS...")
    try:
        # Piper es muy eficiente en CPU
        import subprocess
        
        # Descargar modelo español si no existe
        if not os.path.exists("es_ES-davefx-medium.onnx"):
            print("Descargando modelo Piper para español...")
            subprocess.run([
                "wget", 
                "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx"
            ])
            subprocess.run([
                "wget",
                "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json"
            ])
        
        # Usar piper
        texto = "Hola, esta es una prueba de Piper TTS en español."
        
        start_time = time.time()
        result = subprocess.run([
            "echo", f'"{texto}"', "|", 
            "piper", "--model", "es_ES-davefx-medium.onnx", 
            "--output_file", "output_piper.wav"
        ], shell=True, capture_output=True)
        end_time = time.time()
        
        if result.returncode == 0:
            print(f"✅ Piper completado en {end_time - start_time:.2f} segundos")
            print(f"📁 Archivo guardado: output_piper.wav")
        else:
            print("❌ Piper no está instalado o hubo un error")
            
    except Exception as e:
        print(f"❌ Error con Piper: {e}")

def install_requirements():
    """Instalar dependencias necesarias"""
    print("📦 Instalando dependencias...")
    
    requirements = [
        "torch>=1.9.0",
        "torchaudio", 
        "TTS",
        "bark",
        "scipy",
        "numpy"
    ]
    
    for req in requirements:
        try:
            subprocess.run(["pip", "install", req], check=True)
            print(f"✅ {req} instalado")
        except:
            print(f"❌ Error instalando {req}")

if __name__ == "__main__":
    print("🎵 Probador de TTS en Español")
    print("=" * 40)
    
    # Verificar si torch funciona
    print(f"🔧 PyTorch versión: {torch.__version__}")
    print(f"💻 Dispositivo: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    
    # Crear directorio para outputs
    os.makedirs("tts_outputs", exist_ok=True)
    os.chdir("tts_outputs")
    
    # Probar cada TTS
    test_coqui_xtts()
    test_bark()
    test_piper()
    
    print("\n🎯 Pruebas completadas!")
    print("📁 Revisa los archivos .wav generados para comparar calidad")
    print("\n💡 Recomendaciones:")
    print("- XTTS-v2: Mejor calidad, necesita audio de referencia")
    print("- Bark: Buena calidad, más lento")  
    print("- Piper: Más rápido, calidad decente")