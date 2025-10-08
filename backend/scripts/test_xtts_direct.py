#!/usr/bin/env python3
"""
Test script directo para XTTS v2 - sin usar imports de la aplicación
"""

import time
import os
from TTS.api import TTS

def test_xtts_direct():
    """Prueba XTTS v2 directamente"""
    
    print("🎵 PRUEBA DIRECTA DE XTTS v2")
    print("=" * 50)
    
    # Texto de prueba
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    
    print(f"Texto de prueba ({len(text)} caracteres): {text[:100]}...")
    
    # Crear archivo de referencia
    print("\n📝 Creando archivo de referencia...")
    try:
        tts_ref = TTS("tts_models/es/mai/tacotron2-DDC")
        tts_ref.tts_to_file(text="Hola, soy la voz de referencia para XTTS v2.", file_path="reference_voice_direct.wav")
        print("✅ Archivo de referencia creado: reference_voice_direct.wav")
        ref_file = "reference_voice_direct.wav"
    except Exception as e:
        print(f"❌ Error creando referencia: {e}")
        return False
    
    # Probar XTTS v2 directamente
    print("\n🔧 Probando XTTS v2 directamente...")
    start_time = time.time()
    
    try:
        # Inicializar XTTS v2
        print("🔄 Inicializando XTTS v2...")
        tts_xtts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        init_time = time.time() - start_time
        print(f"✅ XTTS v2 inicializado en {init_time:.2f}s")
        
        # Generar audio
        print("🎵 Generando audio...")
        gen_start = time.time()
        
        tts_xtts.tts_to_file(
            text=text,
            file_path="test_xtts_direct.wav",
            speaker_wav=ref_file,
            language="es",
            speed=1.0,
            temperature=0.1
        )
        
        gen_time = time.time() - gen_start
        total_time = time.time() - start_time
        
        print(f"✅ Audio generado: test_xtts_direct.wav")
        print(f"⏱️  Tiempo de inicialización: {init_time:.2f}s")
        print(f"⏱️  Tiempo de generación: {gen_time:.2f}s")
        print(f"⏱️  Tiempo total: {total_time:.2f}s")
        
        # Verificar archivo
        file_size = os.path.getsize("test_xtts_direct.wav") / 1024  # KB
        print(f"📁 Tamaño del archivo: {file_size:.1f} KB")
        
        if file_size < 1:
            print("⚠️  Archivo muy pequeño, puede indicar un problema")
            return False
            
    except Exception as e:
        print(f"❌ Error con XTTS v2: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ PRUEBA DIRECTA EXITOSA")
    print("=" * 50)
    print("Archivos generados:")
    print("- test_xtts_direct.wav (XTTS v2)")
    print("- reference_voice_direct.wav (referencia)")
    print(f"\nXTTS v2 funciona correctamente!")
    print(f"Tiempo total: {total_time:.2f}s")
    print(f"Tamaño del archivo: {file_size:.1f} KB")
    
    return True

if __name__ == "__main__":
    success = test_xtts_direct()
    if not success:
        print("\n❌ La prueba falló. Revisa los errores arriba.")
        exit(1) 