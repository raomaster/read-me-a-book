#!/usr/bin/env python3
"""
Script para explorar modelos con voces femeninas más rápidos
"""
from TTS.api import TTS
import time

def explore_models():
    print("🔍 EXPLORANDO MODELOS CON VOCES FEMENINAS")
    print("=" * 60)
    
    # Lista de modelos a explorar (priorizando voces femeninas)
    models_to_explore = [
        # Modelos multilingües con voces femeninas
        "tts_models/multilingual/multi-dataset/your_tts",
        "tts_models/multilingual/multi-dataset/xtts_v2",
        
        # Modelos en español específicos
        "tts_models/es/css10/vits",
        "tts_models/es/mai/tacotron2-DDC",
        "tts_models/es/css10/fastspeech2",
        
        # Modelos en otros idiomas que podrían funcionar
        "tts_models/en/ljspeech/tacotron2-DDC",
        "tts_models/en/ljspeech/vits",
        "tts_models/en/vctk/vits",
        "tts_models/en/ljspeech/fastspeech2",
        
        # Modelos en portugués (cercano al español)
        "tts_models/pt/cv/vits",
        "tts_models/pt/cv/tacotron2-DDC",
    ]
    
    results = []
    
    for model_name in models_to_explore:
        print(f"\n--- Explorando: {model_name} ---")
        
        try:
            start_time = time.time()
            tts = TTS(model_name)
            init_time = time.time() - start_time
            
            print(f"✅ Modelo cargado en {init_time:.2f}s")
            
            # Verificar información del modelo
            model_info = {
                "name": model_name,
                "init_time": init_time,
                "has_speakers": False,
                "speakers": None,
                "languages": None,
                "is_female": False,
                "female_speakers": []
            }
            
            # Verificar speakers
            if hasattr(tts, 'speakers') and tts.speakers:
                model_info["has_speakers"] = True
                model_info["speakers"] = tts.speakers
                print(f"🎤 Speakers: {tts.speakers}")
                
                # Buscar voces femeninas
                female_keywords = ['female', 'woman', 'girl', 'lady', 'f', 'woman', 'mujer', 'fem']
                female_speakers = []
                
                for speaker in tts.speakers:
                    speaker_lower = str(speaker).lower()
                    if any(keyword in speaker_lower for keyword in female_keywords):
                        female_speakers.append(speaker)
                
                if female_speakers:
                    model_info["is_female"] = True
                    model_info["female_speakers"] = female_speakers
                    print(f"👩 Voces femeninas encontradas: {female_speakers}")
            
            # Verificar idiomas
            if hasattr(tts, 'languages') and tts.languages:
                model_info["languages"] = tts.languages
                print(f"🌍 Idiomas: {tts.languages}")
            
            # Probar generación rápida
            print("🧪 Probando generación...")
            test_start = time.time()
            
            if model_info["is_female"] and model_info["female_speakers"]:
                # Probar con voz femenina
                speaker = model_info["female_speakers"][0]
                tts.tts_to_file(
                    text="Hola, esto es una prueba de voz femenina.",
                    file_path=f"test_{model_name.replace('/', '_')}.wav",
                    speaker=speaker
                )
            else:
                # Probar sin speaker específico
                tts.tts_to_file(
                    text="Hola, esto es una prueba.",
                    file_path=f"test_{model_name.replace('/', '_')}.wav"
                )
            
            gen_time = time.time() - test_start
            model_info["gen_time"] = gen_time
            model_info["total_time"] = init_time + gen_time
            
            print(f"✅ Audio generado en {gen_time:.2f}s")
            print(f"📊 Tiempo total: {model_info['total_time']:.2f}s")
            
            results.append(model_info)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "name": model_name,
                "error": str(e),
                "init_time": 0,
                "gen_time": 0,
                "total_time": 0,
                "is_female": False
            })
    
    # Mostrar resumen
    print(f"\n{'='*60}")
    print("RESUMEN DE MODELOS CON VOCES FEMENINAS")
    print(f"{'='*60}")
    
    female_models = [r for r in results if r.get("is_female", False) and "error" not in r]
    
    if female_models:
        print(f"\n✅ Modelos con voces femeninas encontrados ({len(female_models)}):")
        print(f"{'Modelo':<40} {'Tiempo':<10} {'Voces Femeninas':<20}")
        print("-" * 80)
        
        for model in sorted(female_models, key=lambda x: x["total_time"]):
            print(f"{model['name']:<40} {model['total_time']:<10.2f}s {str(model['female_speakers'][:2]):<20}")
    else:
        print("❌ No se encontraron modelos con voces femeninas específicas")
    
    # Mostrar todos los modelos por velocidad
    working_models = [r for r in results if "error" not in r]
    if working_models:
        print(f"\n📊 Todos los modelos por velocidad:")
        print(f"{'Modelo':<40} {'Tiempo':<10} {'Tiene Speakers':<15}")
        print("-" * 80)
        
        for model in sorted(working_models, key=lambda x: x["total_time"]):
            has_speakers = "Sí" if model.get("has_speakers", False) else "No"
            print(f"{model['name']:<40} {model['total_time']:<10.2f}s {has_speakers:<15}")

if __name__ == "__main__":
    explore_models() 