#!/usr/bin/env python3
"""
Script para optimizar el audio de referencia para XTTS
Recorta el audio a 10 segundos para acelerar el procesamiento
"""
import subprocess
from pydub import AudioSegment
import os

def optimize_reference_audio():
    print("🔧 OPTIMIZANDO AUDIO DE REFERENCIA PARA XTTS")
    print("=" * 60)
    
    # Descargar el audio original
    mp3_url = "https://ia800608.us.archive.org/4/items/amoryllanto_2502_librivox/amoryllanto_15_sinues_64kb.mp3"
    print(f"🔽 Descargando audio original...")
    subprocess.run([
        "python", "scripts/download_and_convert_reference.py", mp3_url, "reference_voice_full.wav"
    ], check=True)
    
    # Recortar a 10 segundos desde el segundo 20 (evitando los primeros 15)
    print("✂️ Recortando audio desde el segundo 20 (evitando los primeros 15)...")
    audio = AudioSegment.from_wav("reference_voice_full.wav")
    
    # Tomar 10 segundos desde el segundo 20 (20000 ms a 30000 ms)
    start_ms = 20000  # Segundo 20
    end_ms = 30000    # Segundo 30
    audio_short = audio[start_ms:end_ms]
    
    # Guardar como referencia optimizada
    audio_short.export("reference_voice_optimized.wav", format="wav")
    
    # Obtener información del archivo
    original_size = os.path.getsize("reference_voice_full.wav") / 1024
    optimized_size = os.path.getsize("reference_voice_optimized.wav") / 1024
    
    print(f"✅ Audio optimizado creado: reference_voice_optimized.wav")
    print(f"📊 Segmento usado: segundos 20-30 (evitando los primeros 15)")
    print(f"📊 Tamaño original: {original_size:.1f} KB")
    print(f"📊 Tamaño optimizado: {optimized_size:.1f} KB")
    print(f"📊 Reducción: {((original_size - optimized_size) / original_size * 100):.1f}%")
    
    # Limpiar archivo temporal
    if os.path.exists("reference_voice_full.wav"):
        os.remove("reference_voice_full.wav")
    
    print("🎯 Audio de referencia optimizado listo para XTTS")

if __name__ == "__main__":
    optimize_reference_audio() 