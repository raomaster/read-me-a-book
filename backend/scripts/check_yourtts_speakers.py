#!/usr/bin/env python3
"""
Script para verificar qué speakers están disponibles en YourTTS
"""
from TTS.api import TTS

def check_yourtts_speakers():
    print("🔍 Verificando speakers disponibles en YourTTS...")
    
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/your_tts")
        
        # Intentar obtener información del modelo
        print(f"✅ YourTTS cargado correctamente")
        print(f"📋 Información del modelo: {tts.model_name}")
        
        # Verificar si tiene atributo speakers
        if hasattr(tts, 'speakers'):
            print(f"🎤 Speakers disponibles: {tts.speakers}")
        else:
            print("❌ No se encontró información de speakers")
            
        # Verificar si tiene atributo languages
        if hasattr(tts, 'languages'):
            print(f"🌍 Idiomas disponibles: {tts.languages}")
        else:
            print("❌ No se encontró información de idiomas")
            
        # Intentar con speaker por defecto
        print("\n🧪 Probando con speaker por defecto...")
        tts.tts_to_file(
            text="Hola, esto es una prueba.",
            file_path="test_yourtts_default.wav",
            language="es"
        )
        print("✅ Funcionó sin especificar speaker")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_yourtts_speakers() 