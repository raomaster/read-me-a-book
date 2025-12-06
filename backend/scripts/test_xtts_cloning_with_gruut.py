#!/usr/bin/env python3
"""
Test script for XTTS cloning with gruut text normalization
Run from backend directory: python scripts/test_xtts_cloning_with_gruut.py
"""

from TTS.api import TTS
import gruut
import time
import os
import subprocess

def normalize_text_with_gruut(text):
    """Normaliza el texto usando gruut-lang-es (solo normalización básica)"""
    try:
        # Limpiar caracteres problemáticos manualmente
        normalized_text = text.replace("¿", "").replace("¡", "")
        
        # Usar gruut solo para división de oraciones
        sentences = list(gruut.sentences(normalized_text, lang="es"))
        
        # Reconstruir el texto sin procesamiento fonético
        normalized_sentences = []
        for sentence in sentences:
            sentence_text = " ".join([word.text for word in sentence])
            normalized_sentences.append(sentence_text)
        
        final_text = " ".join(normalized_sentences)
        
        print(f"📝 Texto original: {text[:100]}...")
        print(f"📝 Texto normalizado: {final_text[:100]}...")
        
        return final_text
        
    except Exception as e:
        print(f"⚠️ Error en normalización gruut: {e}")
        print("📝 Usando texto original sin normalizar")
        return text

# Texto de prueba
text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'

print("🎵 XTTS CLONADO CON GRUUT - Pruebas de calidad y naturalidad")
print("=" * 80)
print(f"Texto de prueba ({len(text)} caracteres): {text[:100]}...")

# Descargar y convertir el archivo de referencia
mp3_url = "https://ia800608.us.archive.org/4/items/amoryllanto_2502_librivox/amoryllanto_15_sinues_64kb.mp3"
ref_wav = "reference_voice.wav"
print(f"\n🔽 Descargando y convirtiendo voz de referencia desde: {mp3_url}")
subprocess.run([
    "python", "scripts/download_and_convert_reference.py", mp3_url, ref_wav
], check=True)
print(f"✅ Archivo de referencia listo: {ref_wav}")

ref_file = ref_wav

# Normalizar texto con gruut
normalized_text = normalize_text_with_gruut(text)

# XTTS v2: batería de pruebas de clonado con texto normalizado
xtts_params_list = [
    {"temperature": 0.01, "speed": 1.0, "description": "Muy conservador"},
    {"temperature": 0.03, "speed": 1.0, "description": "Conservador"},
    {"temperature": 0.05, "speed": 1.0, "description": "Balanceado (el que funcionó bien)"},
    {"temperature": 0.07, "speed": 1.0, "description": "Ligeramente expresivo"},
    {"temperature": 0.1, "speed": 1.0, "description": "Más expresivo"},
]

print(f"\n{'='*80}")
print("EJECUTANDO PRUEBAS DE CLONADO XTTS CON TEXTO NORMALIZADO")
print(f"{'='*80}")

for idx, params in enumerate(xtts_params_list, 1):
    output_file = f"xtts_gruut_temp{params['temperature']}_speed{params['speed']}.wav"
    print(f"\n--- Prueba XTTS Clonado {idx}: {params['description']} ---")
    print(f"📊 Parámetros: temperature={params['temperature']}, speed={params['speed']}")
    
    start_time = time.time()
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        init_time = time.time() - start_time
        
        gen_start = time.time()
        tts.tts_to_file(
            text=normalized_text,
            file_path=output_file,
            speaker_wav=ref_file,
            language="es",
            temperature=params["temperature"],
            speed=params["speed"]
        )
        gen_time = time.time() - gen_start
        total_time = time.time() - start_time
        
        # Obtener tamaño del archivo
        file_size = os.path.getsize(output_file) / 1024  # KB
        
        print(f"✅ Audio generado: {output_file}")
        print(f"⏱️  Tiempo de inicialización: {init_time:.2f}s")
        print(f"⏱️  Tiempo de generación: {gen_time:.2f}s")
        print(f"⏱️  Tiempo total: {total_time:.2f}s")
        print(f"📁 Tamaño del archivo: {file_size:.1f} KB")
        
    except Exception as e:
        print(f"❌ Error en prueba XTTS Clonado {idx}: {e}")

print(f"\n{'='*80}")
print("PRUEBAS DE CLONADO COMPLETADAS")
print("Archivos generados:")
for params in xtts_params_list:
    output_file = f"xtts_gruut_temp{params['temperature']}_speed{params['speed']}.wav"
    print(f"  ✅ {output_file} - {params['description']}")
print("\n🎧 Escucha los archivos para comparar calidad y naturalidad")
print("🔍 Busca el que tenga mejor balance entre naturalidad y claridad")
print(f"{'='*80}") 