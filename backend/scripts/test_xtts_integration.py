#!/usr/bin/env python3
"""
Test script para verificar la integración de XTTS v2 con la aplicación
"""

import sys
import os
from pathlib import Path

# Agregar src al path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

# Imports absolutos
from engines.engine_factory import create_engine
from config import XTTS_CONFIG

def test_xtts_integration():
    """Prueba la integración de XTTS v2 con la aplicación"""
    
    print("🎵 PRUEBA DE INTEGRACIÓN XTTS v2")
    print("=" * 50)
    
    # Texto de prueba
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    
    print(f"Texto de prueba ({len(text)} caracteres): {text[:100]}...")
    
    # Crear archivo de referencia
    print("\n📝 Creando archivo de referencia...")
    try:
        from TTS.api import TTS
        tts_ref = TTS("tts_models/es/mai/tacotron2-DDC")
        tts_ref.tts_to_file(text="Hola, soy la voz de referencia para XTTS v2.", file_path="reference_voice_integration.wav")
        print("✅ Archivo de referencia creado: reference_voice_integration.wav")
        ref_file = "reference_voice_integration.wav"
    except Exception as e:
        print(f"❌ Error creando referencia: {e}")
        return False
    
    # Probar creación del engine XTTS
    print("\n🔧 Probando creación del engine XTTS...")
    try:
        xtts_engine = create_engine(
            engine_type="xtts",
            lang="es",
            xtts_speaker_wav=ref_file,
            xtts_speed=1.0,
            xtts_temperature=0.1
        )
        print("✅ Engine XTTS creado exitosamente")
    except Exception as e:
        print(f"❌ Error creando engine XTTS: {e}")
        return False
    
    # Probar generación de audio
    print("\n🎵 Probando generación de audio...")
    try:
        audio_bytes = xtts_engine.text_to_bytes(text)
        print(f"✅ Audio generado exitosamente: {len(audio_bytes)} bytes")
        
        # Guardar archivo de prueba
        output_file = "test_xtts_integration.wav"
        with open(output_file, "wb") as f:
            f.write(audio_bytes)
        print(f"✅ Archivo guardado: {output_file}")
        
        # Verificar que el archivo no está vacío
        file_size = os.path.getsize(output_file) / 1024  # KB
        print(f"📁 Tamaño del archivo: {file_size:.1f} KB")
        
        if file_size < 1:
            print("⚠️  Archivo muy pequeño, puede indicar un problema")
            return False
            
    except Exception as e:
        print(f"❌ Error generando audio: {e}")
        return False
    
    # Probar método text_to_speech
    print("\n💾 Probando método text_to_speech...")
    try:
        file_output = "test_xtts_integration_file.wav"
        xtts_engine.text_to_speech(text, file_output)
        print(f"✅ Archivo generado con text_to_speech: {file_output}")
        
        # Verificar que el archivo no está vacío
        file_size = os.path.getsize(file_output) / 1024  # KB
        print(f"📁 Tamaño del archivo: {file_size:.1f} KB")
        
    except Exception as e:
        print(f"❌ Error con text_to_speech: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ INTEGRACIÓN XTTS v2 EXITOSA")
    print("=" * 50)
    print("Archivos generados:")
    print("- test_xtts_integration.wav (text_to_bytes)")
    print("- test_xtts_integration_file.wav (text_to_speech)")
    print("- reference_voice_integration.wav (referencia)")
    print("\nXTTS v2 está listo para usar en la aplicación!")
    
    return True

if __name__ == "__main__":
    success = test_xtts_integration()
    if not success:
        print("\n❌ La integración falló. Revisa los errores arriba.")
        sys.exit(1) 