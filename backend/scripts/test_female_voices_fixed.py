#!/usr/bin/env python3
"""
Script para probar voces femeninas con errores corregidos
"""
from TTS.api import TTS
import time

def test_female_voices():
    print("👩 PROBANDO VOCES FEMENINAS - Errores corregidos")
    print("=" * 60)
    
    # Modelos con voces femeninas que necesitan parámetros específicos
    models_to_test = [
        {
            "name": "YourTTS (female-en-5)",
            "model": "tts_models/multilingual/multi-dataset/your_tts",
            "speaker": "female-en-5",
            "language": "en"
        },
        {
            "name": "YourTTS (female-pt-4)",
            "model": "tts_models/multilingual/multi-dataset/your_tts",
            "speaker": "female-pt-4",
            "language": "pt-br"
        },
        {
            "name": "XTTS v2 (Ana Florence)",
            "model": "tts_models/multilingual/multi-dataset/xtts_v2",
            "speaker": "Ana Florence",
            "language": "es"
        },
        {
            "name": "VCTK (p225 - femenina)",
            "model": "tts_models/en/vctk/vits",
            "speaker": "p225",
            "language": "en"
        }
    ]
    
    results = []
    
    for model_info in models_to_test:
        print(f"\n--- Probando: {model_info['name']} ---")
        
        try:
            start_time = time.time()
            tts = TTS(model_info['model'])
            init_time = time.time() - start_time
            
            print(f"✅ Modelo cargado en {init_time:.2f}s")
            
            # Probar generación con parámetros correctos
            print("🧪 Probando generación...")
            test_start = time.time()
            
            output_file = f"test_{model_info['name'].replace(' ', '_').replace('(', '').replace(')', '')}.wav"
            
            if "xtts" in model_info['model']:
                # XTTS necesita speaker_wav, pero usaremos speaker interno
                tts.tts_to_file(
                    text="Hola, esto es una prueba de voz femenina en español.",
                    file_path=output_file,
                    speaker=model_info['speaker'],
                    language=model_info['language']
                )
            else:
                # Otros modelos
                tts.tts_to_file(
                    text="Hello, this is a female voice test.",
                    file_path=output_file,
                    speaker=model_info['speaker'],
                    language=model_info['language']
                )
            
            gen_time = time.time() - test_start
            total_time = init_time + gen_time
            
            print(f"✅ Audio generado: {output_file}")
            print(f"⏱️  Tiempo de generación: {gen_time:.2f}s")
            print(f"⏱️  Tiempo total: {total_time:.2f}s")
            
            results.append({
                "name": model_info['name'],
                "total_time": total_time,
                "gen_time": gen_time,
                "output_file": output_file,
                "success": True
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "name": model_info['name'],
                "error": str(e),
                "success": False
            })
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print("RESUMEN DE VOCES FEMENINAS")
    print(f"{'='*60}")
    
    successful = [r for r in results if r['success']]
    
    if successful:
        print(f"\n✅ Voces femeninas funcionando ({len(successful)}):")
        print(f"{'Modelo':<35} {'Tiempo':<10} {'Archivo':<20}")
        print("-" * 70)
        
        for result in sorted(successful, key=lambda x: x["total_time"]):
            print(f"{result['name']:<35} {result['total_time']:<10.2f}s {result['output_file']:<20}")
        
        fastest = min(successful, key=lambda x: x["total_time"])
        print(f"\n🏆 Más rápida: {fastest['name']} ({fastest['total_time']:.2f}s)")
    
    failed = [r for r in results if not r['success']]
    if failed:
        print(f"\n❌ Fallaron ({len(failed)}):")
        for result in failed:
            print(f"- {result['name']}: {result['error']}")

if __name__ == "__main__":
    test_female_voices() 