#!/usr/bin/env python3
"""
Test script with gruut-lang-es for better Spanish text processing
Run from backend directory: python scripts/test_with_gruut.py
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

def test_model_with_gruut(model_name, text, output_file, is_xtts=False, ref_file=None):
    """Prueba un modelo con texto normalizado por gruut"""
    start_time = time.time()
    
    try:
        print(f"🔄 Inicializando {model_name}...")
        tts = TTS(model_name)
        init_time = time.time() - start_time
        print(f"✅ {model_name} inicializado en {init_time:.2f}s")
        
        # Normalizar texto con gruut
        normalized_text = normalize_text_with_gruut(text)
        
        # Generar audio
        gen_start = time.time()
        if is_xtts and ref_file:
            tts.tts_to_file(
                text=normalized_text,
                file_path=output_file,
                speaker_wav=ref_file,
                language="es"
            )
        else:
            tts.tts_to_file(text=normalized_text, file_path=output_file)
        
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

print("🎵 PRUEBA CON GRUUT-LANG-ES - Mejor procesamiento de texto español")
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

# Probar modelos con gruut
models_to_test = [
    {
        "name": "Tacotron2 Español (con gruut)",
        "model": "tts_models/es/mai/tacotron2-DDC",
        "output": "test_tacotron2_gruut.wav",
        "is_xtts": False
    },
    {
        "name": "XTTS v2 (con gruut)",
        "model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "output": "test_xtts_gruut.wav",
        "is_xtts": True
    }
]

print(f"\n{'='*80}")
print("EJECUTANDO PRUEBAS CON GRUUT-LANG-ES")
print(f"{'='*80}")

for i, model_info in enumerate(models_to_test, 1):
    print(f"\n--- Prueba {i}: {model_info['name']} ---")
    
    result = test_model_with_gruut(
        model_name=model_info['model'],
        text=text,
        output_file=model_info['output'],
        is_xtts=model_info['is_xtts'],
        ref_file=ref_file if model_info['is_xtts'] else None
    )

print(f"\n{'='*80}")
print("PRUEBA CON GRUUT COMPLETADA")
print("Compara los archivos generados con gruut vs sin gruut")
print(f"{'='*80}") 