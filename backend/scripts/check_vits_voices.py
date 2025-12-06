#!/usr/bin/env python3
"""
Script para verificar qué voces están disponibles en VITS español
"""
from TTS.api import TTS

def check_vits_voices():
    print("🔍 Verificando voces disponibles en VITS Español...")
    
    try:
        tts = TTS("tts_models/es/css10/vits")
        
        print(f"✅ VITS Español cargado correctamente")
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
            
        # Probar generación de audio
        print("\n🧪 Probando generación de audio...")
        tts.tts_to_file(
            text="Hola, esto es una prueba de VITS español.",
            file_path="test_vits_voice.wav"
        )
        print("✅ Audio generado: test_vits_voice.wav")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_vits_voices() 