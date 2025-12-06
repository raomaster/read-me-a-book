#!/usr/bin/env python3
"""
Script para investigar y arreglar el problema con modelos de Hugging Face
"""

import sys
import os
from TTS.api import TTS

def check_tts_version():
    """Verifica la versión de coqui-tts"""
    try:
        import TTS
        print(f"📦 Versión de coqui-tts: {TTS.__version__}")
        return TTS.__version__
    except:
        print("❌ No se pudo obtener la versión de coqui-tts")
        return None

def check_huggingface_hub():
    """Verifica la instalación de huggingface_hub"""
    try:
        import huggingface_hub
        print(f"📦 Versión de huggingface_hub: {huggingface_hub.__version__}")
        return huggingface_hub.__version__
    except ImportError:
        print("❌ huggingface_hub no está instalado")
        return None

def test_model_download(model_name):
    """Prueba la descarga de un modelo específico"""
    print(f"\n🔍 Probando descarga de: {model_name}")
    
    try:
        # Intentar diferentes métodos de inicialización
        print("Método 1: Inicialización directa")
        tts = TTS(model_name)
        print(f"✅ {model_name} descargado exitosamente!")
        return True
    except Exception as e1:
        print(f"❌ Error método 1: {e1}")
        
        try:
            print("Método 2: Con progress_bar=True")
            tts = TTS(model_name, progress_bar=True)
            print(f"✅ {model_name} descargado con progress_bar!")
            return True
        except Exception as e2:
            print(f"❌ Error método 2: {e2}")
            
            try:
                print("Método 3: Con parámetros específicos")
                tts = TTS(model_name, gpu=False)
                print(f"✅ {model_name} descargado con gpu=False!")
                return True
            except Exception as e3:
                print(f"❌ Error método 3: {e3}")
                return False

def test_huggingface_models():
    """Prueba diferentes modelos de Hugging Face"""
    
    print("🎯 INVESTIGANDO MODELOS DE HUGGING FACE")
    print("=" * 60)
    
    # Verificar versiones
    print("📋 Verificando versiones...")
    tts_version = check_tts_version()
    hf_version = check_huggingface_hub()
    
    # Lista de modelos para probar
    models = [
        "coqui/XTTS-v2",
        "coqui/XTTS-v1.1",
        "facebook/fastspeech2-es-css10",
        "microsoft/speecht5_tts"
    ]
    
    print(f"\n🔍 Probando {len(models)} modelos...")
    
    results = {}
    for model in models:
        success = test_model_download(model)
        results[model] = success
    
    # Resumen
    print(f"\n📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    working_models = [m for m, s in results.items() if s]
    failed_models = [m for m, s in results.items() if not s]
    
    print(f"✅ Modelos que funcionan: {len(working_models)}")
    for model in working_models:
        print(f"  - {model}")
    
    print(f"\n❌ Modelos que fallan: {len(failed_models)}")
    for model in failed_models:
        print(f"  - {model}")
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES")
    print("=" * 60)
    
    if working_models:
        print("✅ Algunos modelos funcionan. Puedes usar:")
        for model in working_models:
            print(f"  - {model}")
    else:
        print("❌ Ningún modelo funciona. Posibles soluciones:")
        print("1. Actualizar coqui-tts: pip install --upgrade coqui-tts")
        print("2. Instalar huggingface_hub: pip install huggingface_hub")
        print("3. Verificar conexión a internet")
        print("4. Usar modelos locales en lugar de Hugging Face")

if __name__ == "__main__":
    test_huggingface_models() 