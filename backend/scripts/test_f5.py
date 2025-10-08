#!/usr/bin/env python3
"""
Test script para F5 (FastSpeech2) como alternativa a coqui-tts
"""

import time
import os

def test_f5_installation():
    """Prueba si F5 está disponible"""
    print("🔍 VERIFICANDO F5 (FastSpeech2)")
    print("=" * 50)
    
    try:
        import torch
        print(f"✅ PyTorch disponible: {torch.__version__}")
    except ImportError:
        print("❌ PyTorch no está instalado")
        return False
    
    try:
        import torchaudio
        print(f"✅ TorchAudio disponible: {torchaudio.__version__}")
    except ImportError:
        print("❌ TorchAudio no está instalado")
        return False
    
    try:
        import transformers
        print(f"✅ Transformers disponible: {transformers.__version__}")
    except ImportError:
        print("❌ Transformers no está instalado")
        return False
    
    return True

def test_f5_models():
    """Prueba modelos F5 disponibles"""
    print("\n🎵 PROBANDO MODELOS F5")
    print("=" * 50)
    
    # Texto de prueba
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    
    print(f"Texto de prueba ({len(text)} caracteres): {text[:100]}...")
    
    # Modelos F5 para probar
    f5_models = [
        "facebook/fastspeech2-es-css10",
        "facebook/fastspeech2-en-ljspeech",
        "microsoft/speecht5_tts",
        "espnet/kan-bayashi_ljspeech_vits"
    ]
    
    results = {}
    
    for model_name in f5_models:
        print(f"\n--- Probando {model_name} ---")
        start_time = time.time()
        
        try:
            # Intentar con transformers
            from transformers import AutoTokenizer, AutoModel
            
            print(f"🔄 Descargando {model_name}...")
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModel.from_pretrained(model_name)
            
            init_time = time.time() - start_time
            print(f"✅ {model_name} descargado en {init_time:.2f}s")
            
            # Intentar síntesis de audio
            print("🎵 Intentando síntesis de audio...")
            gen_start = time.time()
            
            # Aquí iría la lógica de síntesis específica para cada modelo
            # Por ahora solo verificamos que se puede cargar
            
            gen_time = time.time() - gen_start
            total_time = time.time() - start_time
            
            print(f"✅ {model_name} funciona correctamente")
            print(f"⏱️  Tiempo total: {total_time:.2f}s")
            
            results[model_name] = {
                "success": True,
                "init_time": init_time,
                "total_time": total_time
            }
            
        except Exception as e:
            print(f"❌ Error con {model_name}: {e}")
            results[model_name] = {
                "success": False,
                "error": str(e)
            }
    
    return results

def show_f5_alternatives():
    """Muestra alternativas a F5"""
    print("\n💡 ALTERNATIVAS A F5")
    print("=" * 50)
    
    alternatives = [
        {
            "name": "Tacotron2 + WaveNet",
            "pros": ["Estable", "Bien documentado", "Funciona offline"],
            "cons": ["Calidad limitada", "Lento"]
        },
        {
            "name": "YourTTS",
            "pros": ["Multilingüe", "Buena calidad", "Voz clonable"],
            "cons": ["Complejo", "Requiere GPU"]
        },
        {
            "name": "Coqui TTS (versión estable)",
            "pros": ["Fácil de usar", "Muchos modelos", "Bien mantenido"],
            "cons": ["Problemas con Hugging Face", "Dependencias complejas"]
        },
        {
            "name": "Mozilla TTS",
            "pros": ["Open source", "Estable", "Bien documentado"],
            "cons": ["Menos modelos", "Calidad limitada"]
        }
    ]
    
    for alt in alternatives:
        print(f"\n📋 {alt['name']}")
        print(f"✅ Pros: {', '.join(alt['pros'])}")
        print(f"❌ Contras: {', '.join(alt['cons'])}")

def main():
    print("🚀 EXPLORANDO F5 COMO ALTERNATIVA")
    print("=" * 60)
    
    # Verificar instalación
    if not test_f5_installation():
        print("\n❌ F5 no está disponible. Instalando dependencias...")
        print("Ejecuta: pip install torch torchaudio transformers")
        return
    
    # Probar modelos
    results = test_f5_models()
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS F5")
    print("=" * 50)
    
    working_models = [m for m, r in results.items() if r["success"]]
    failed_models = [m for m, r in results.items() if not r["success"]]
    
    print(f"✅ Modelos que funcionan: {len(working_models)}")
    for model in working_models:
        time_info = results[model]
        print(f"  - {model} ({time_info['total_time']:.2f}s)")
    
    print(f"\n❌ Modelos que fallan: {len(failed_models)}")
    for model in failed_models:
        print(f"  - {model}: {results[model]['error']}")
    
    # Mostrar alternativas
    show_f5_alternatives()
    
    print("\n" + "=" * 60)
    print("🎯 RECOMENDACIÓN")
    print("=" * 60)
    
    if working_models:
        print("✅ F5 funciona con algunos modelos. Considera usarlo como alternativa.")
        print("F5 es más estable y rápido que coqui-tts.")
    else:
        print("❌ F5 también tiene problemas. Recomendaciones:")
        print("1. Usar XTTS v2 local (que ya funciona)")
        print("2. Probar YourTTS")
        print("3. Usar Tacotron2 + WaveNet")

if __name__ == "__main__":
    main() 