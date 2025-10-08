#!/usr/bin/env python3
"""
Test script for XTTS v2 TTS engine - Updated for Coqui TTS Community Version
Run from backend directory: python scripts/test_xtts_simple.py
"""

from TTS.api import TTS
import time
import os
import subprocess

def test_model_with_timing(model_name, text, output_file, is_xtts=False, ref_file=None, needs_speaker=False):
    """Prueba un modelo y mide el tiempo de generación"""
    start_time = time.time()
    
    try:
        print(f"🔄 Inicializando {model_name}...")
        tts = TTS(model_name)
        init_time = time.time() - start_time
        print(f"✅ {model_name} inicializado en {init_time:.2f}s")
        
        # Mostrar el texto que va a procesar
        print(f"📝 Texto a procesar: {text[:100]}...")
        
        # Generar audio
        gen_start = time.time()
        if is_xtts and ref_file:
            tts.tts_to_file(
                text=text,
                file_path=output_file,
                speaker_wav=ref_file,
                language="es"
            )
        elif needs_speaker:
            # Para modelos multi-speaker como YourTTS
            tts.tts_to_file(
                text=text,
                file_path=output_file,
                speaker="female-en-5",  # Speaker válido para YourTTS
                language="es"    # Idioma inglés (YourTTS no soporta español)
            )
        else:
            tts.tts_to_file(text=text, file_path=output_file)
        
        gen_time = time.time() - gen_start
        total_time = time.time() - start_time
        
        # Obtener tamaño del archivo
        file_size = os.path.getsize(output_file) / 1024  # KB
        
        print(f"✅ Audio generado: {output_file}")
        print(f"⏱️  Tiempo de inicialización: {init_time:.2f}s")
        print(f"⏱️  Tiempo de generación: {gen_time:.2f}s")
        print(f"⏱️  Tiempo total: {total_time:.2f}s")
        print(f"📁 Tamaño del archivo: {file_size:.1f} KB")
        
        return {
            "success": True,
            "init_time": init_time,
            "gen_time": gen_time,
            "total_time": total_time,
            "file_size": file_size,
            "output_file": output_file
        }
        
    except Exception as e:
        print(f"❌ Error con {model_name}: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Texto de prueba
text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'

print("🎵 COMPARACIÓN DE MODELOS TTS - Coqui TTS Community Version")
print("=" * 70)
print(f"Texto de prueba ({len(text)} caracteres): {text[:100]}...")

# Descargar y convertir el archivo de referencia antes de las pruebas
mp3_url = "https://ia800608.us.archive.org/4/items/amoryllanto_2502_librivox/amoryllanto_15_sinues_64kb.mp3"
ref_wav = "reference_voice.wav"
print(f"\n🔽 Descargando y convirtiendo voz de referencia desde: {mp3_url}")
subprocess.run([
    "python", "scripts/download_and_convert_reference.py", mp3_url, ref_wav
], check=True)
print(f"✅ Archivo de referencia listo: {ref_wav}")

# Crear archivo de referencia para XTTS (ya no es necesario, solo usar el descargado)
ref_file = ref_wav

# Lista de modelos a probar - Solo modelos compatibles con Coqui TTS Community
models_to_test = [
    # Modelos locales - Funcionan bien
    {
        "name": "VITS Español Local",
        "model": "tts_models/es/css10/vits",
        "output": "test_vits_local.wav",
        "is_xtts": False
    },
    {
        "name": "XTTS v2 Local",
        "model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "output": "test_xtts_v2_local.wav",
        "is_xtts": True
    },
    # Modelos adicionales compatibles
    {
        "name": "Tacotron2 Español",
        "model": "tts_models/es/mai/tacotron2-DDC",
        "output": "test_tacotron2_es.wav",
        "is_xtts": False
    },
    {
        "name": "YourTTS Multilingual",
        "model": "tts_models/multilingual/multi-dataset/your_tts",
        "output": "test_yourtts.wav",
        "is_xtts": False,
        "needs_speaker": True
    }
]

# Resultados de las pruebas
results = []

print(f"\n{'='*70}")
print("EJECUTANDO PRUEBAS DE MODELOS COMPATIBLES")
print(f"{'='*70}")

for i, model_info in enumerate(models_to_test, 1):
    print(f"\n--- Prueba {i}: {model_info['name']} ---")
    
    result = test_model_with_timing(
        model_name=model_info['model'],
        text=text,
        output_file=model_info['output'],
        is_xtts=model_info['is_xtts'],
        ref_file=ref_file if model_info['is_xtts'] else None,
        needs_speaker=model_info.get('needs_speaker', False)
    )
    
    result['name'] = model_info['name']
    result['model'] = model_info['model']
    results.append(result)

# XTTS v2: batería de pruebas de clonado - Solo temperature
xtts_params_list = [
    {"temperature": 0.01, "speed": 1.0},  # Muy conservador
    {"temperature": 0.03, "speed": 1.0},  # Conservador
    {"temperature": 0.05, "speed": 1.0},  # El que funcionó bien
    {"temperature": 0.07, "speed": 1.0},  # Ligeramente más expresivo
]

for idx, params in enumerate(xtts_params_list, 1):
    output_file = f"xtts_temp{params['temperature']}_speed{params['speed']}.wav"
    print(f"\n--- Prueba XTTS Clonado {idx}: temperature={params['temperature']}, speed={params['speed']} ---")
    print(f"📝 Texto a procesar: {text[:100]}...")
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        tts.tts_to_file(
            text=text,
            file_path=output_file,
            speaker_wav=ref_file,
            language="es",
            temperature=params["temperature"],
            speed=params["speed"]
        )
        print(f"✅ Audio generado: {output_file}")
    except Exception as e:
        print(f"❌ Error en prueba XTTS Clonado {idx}: {e}")

# Mostrar resumen comparativo
print(f"\n{'='*70}")
print("RESUMEN COMPARATIVO")
print(f"{'='*70}")

successful_results = [r for r in results if r['success']]

if successful_results:
    print(f"\n✅ Modelos exitosos ({len(successful_results)}/{len(models_to_test)}):")
    print(f"{'Modelo':<25} {'Inicialización':<12} {'Generación':<12} {'Total':<10} {'Tamaño':<10}")
    print("-" * 85)
    
    for result in successful_results:
        print(f"{result['name']:<25} {result['init_time']:<12.2f} {result['gen_time']:<12.2f} {result['total_time']:<10.2f} {result['file_size']:<10.1f} KB")
    
    # Encontrar el más rápido
    fastest = min(successful_results, key=lambda x: x['total_time'])
    print(f"\n🏆 Más rápido: {fastest['name']} ({fastest['total_time']:.2f}s)")
    
    # Encontrar el más lento
    slowest = max(successful_results, key=lambda x: x['total_time'])
    print(f"🐌 Más lento: {slowest['name']} ({slowest['total_time']:.2f}s)")

else:
    print("❌ Ningún modelo funcionó correctamente")

# Mostrar errores
failed_results = [r for r in results if not r['success']]
if failed_results:
    print(f"\n❌ Modelos que fallaron ({len(failed_results)}):")
    for result in failed_results:
        print(f"- {result['name']}: {result['error']}")

print(f"\n📁 Archivos generados:")
for result in results:
    if result['success']:
        print(f"  ✅ {result['output_file']}")
    else:
        print(f"  ❌ {result['name']} - Falló")

print(f"\n{'='*70}")
print("COMPARACIÓN COMPLETADA")
print("Escucha los archivos generados para comparar calidad de audio")
print("Los modelos de Hugging Face externos no son compatibles con esta versión")
print(f"{'='*70}") 