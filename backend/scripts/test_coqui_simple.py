#!/usr/bin/env python3
"""
Simple test script for Coqui TTS Community Version
Run from backend directory: python scripts/test_coqui_simple.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engines.xtts_engine import XttsEngine
import time

def test_coqui_tts():
    """Test Coqui TTS with different models"""
    
    text = "Hola, esto es una prueba de Coqui TTS. La voz suena natural y clara."
    
    print("🎵 PRUEBA DE COQUI TTS COMMUNITY VERSION")
    print("=" * 50)
    print(f"Texto: {text}")
    print()
    
    # Test 1: VITS Español (rápido)
    print("🔄 Probando VITS Español...")
    try:
        start_time = time.time()
        engine = XttsEngine(
            model_name="tts_models/es/css10/vits",
            speed=1.0
        )
        init_time = time.time() - start_time
        
        gen_start = time.time()
        engine.text_to_speech(text, "test_coqui_vits.wav")
        gen_time = time.time() - gen_start
        
        print(f"✅ VITS Español: Inicialización {init_time:.2f}s, Generación {gen_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error con VITS: {e}")
    
    print()
    
    # Test 2: Tacotron2 Español (medio)
    print("🔄 Probando Tacotron2 Español...")
    try:
        start_time = time.time()
        engine = XttsEngine(
            model_name="tts_models/es/mai/tacotron2-DDC",
            speed=1.0
        )
        init_time = time.time() - start_time
        
        gen_start = time.time()
        engine.text_to_speech(text, "test_coqui_tacotron2.wav")
        gen_time = time.time() - gen_start
        
        print(f"✅ Tacotron2: Inicialización {init_time:.2f}s, Generación {gen_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error con Tacotron2: {e}")
    
    print()
    
    # Test 3: XTTS v2 (lento pero alta calidad)
    print("🔄 Probando XTTS v2 (puede tardar)...")
    try:
        start_time = time.time()
        engine = XttsEngine(
            model_name="tts_models/multilingual/multi-dataset/xtts_v2",
            speaker_wav="reference_voice.wav",
            language="es",
            speed=1.0,
            temperature=0.1
        )
        init_time = time.time() - start_time
        
        gen_start = time.time()
        engine.text_to_speech(text, "test_coqui_xtts.wav")
        gen_time = time.time() - gen_start
        
        print(f"✅ XTTS v2: Inicialización {init_time:.2f}s, Generación {gen_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error con XTTS v2: {e}")
    
    print()
    print("=" * 50)
    print("✅ PRUEBA COMPLETADA")
    print("Archivos generados:")
    print("  - test_coqui_vits.wav")
    print("  - test_coqui_tacotron2.wav") 
    print("  - test_coqui_xtts.wav")
    print("Escucha los archivos para comparar calidad de audio")

if __name__ == "__main__":
    test_coqui_tts() 