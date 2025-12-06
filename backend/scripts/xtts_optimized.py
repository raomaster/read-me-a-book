#!/usr/bin/env python3
"""
XTTS Optimizado - Versión rápida para lectura de libros
Usa audio de referencia corto y chunks de texto pequeños
"""
from TTS.api import TTS
import gruut
import time
import os
import subprocess

def normalize_text_with_gruut(text):
    """Normaliza el texto usando gruut-lang-es"""
    try:
        normalized_text = text.replace("¿", "").replace("¡", "")
        sentences = list(gruut.sentences(normalized_text, lang="es"))
        normalized_sentences = []
        for sentence in sentences:
            sentence_text = " ".join([word.text for word in sentence])
            normalized_sentences.append(sentence_text)
        return " ".join(normalized_sentences)
    except Exception as e:
        print(f"⚠️ Error en normalización: {e}")
        return text

def split_text_into_chunks(text, max_chars=800):
    """Divide el texto en chunks de párrafos para procesamiento de frontend"""
    sentences = list(gruut.sentences(text, lang="es"))
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence_text = " ".join([word.text for word in sentence])
        
        if len(current_chunk) + len(sentence_text) <= max_chars:
            current_chunk += sentence_text + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence_text + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def test_xtts_optimized():
    print("🚀 XTTS OPTIMIZADO - Versión rápida para lectura de libros")
    print("=" * 70)
    
    # Texto de prueba (párrafo completo como enviaría el frontend)
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    
    print(f"📝 Texto de prueba ({len(text)} caracteres): {text[:80]}...")
    
    # Crear audio de referencia optimizado
    print(f"\n🔧 Creando audio de referencia optimizado...")
    subprocess.run(["python", "scripts/optimize_xtts_reference.py"], check=True)
    
    ref_file = "reference_voice_optimized.wav"
    
    # Normalizar texto
    normalized_text = normalize_text_with_gruut(text)
    print(f"📝 Texto normalizado: {normalized_text[:80]}...")
    
    # Dividir en chunks
    chunks = split_text_into_chunks(normalized_text, max_chars=800)
    print(f"📦 Texto dividido en {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i}: {chunk[:60]}...")
    
    # Probar XTTS optimizado
    print(f"\n{'='*70}")
    print("EJECUTANDO XTTS OPTIMIZADO")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        print("🔄 Inicializando XTTS...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        init_time = time.time() - start_time
        print(f"✅ XTTS inicializado en {init_time:.2f}s")
        
        # Procesar cada chunk
        all_audio_files = []
        total_gen_time = 0
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- Procesando chunk {i}/{len(chunks)} ---")
            print(f"📝 Chunk: {chunk}")
            
            chunk_start = time.time()
            output_file = f"xtts_optimized_chunk_{i}.wav"
            
            tts.tts_to_file(
                text=chunk,
                file_path=output_file,
                speaker_wav=ref_file,
                language="es",
                temperature=0.05,  # Conservador para velocidad
                speed=1.0
            )
            
            chunk_time = time.time() - chunk_start
            total_gen_time += chunk_time
            
            file_size = os.path.getsize(output_file) / 1024
            all_audio_files.append(output_file)
            
            print(f"✅ Chunk {i} generado: {output_file}")
            print(f"⏱️  Tiempo del chunk: {chunk_time:.2f}s")
            print(f"📁 Tamaño: {file_size:.1f} KB")
        
        total_time = time.time() - start_time
        
        print(f"\n{'='*70}")
        print("RESULTADOS DE OPTIMIZACIÓN")
        print(f"{'='*70}")
        print(f"📊 Tiempo de inicialización: {init_time:.2f}s")
        print(f"📊 Tiempo total de generación: {total_gen_time:.2f}s")
        print(f"📊 Tiempo total: {total_time:.2f}s")
        print(f"📊 Velocidad promedio: {len(text)/total_gen_time:.1f} caracteres/segundo")
        print(f"📊 Archivos generados: {len(all_audio_files)}")
        
        for file in all_audio_files:
            print(f"  ✅ {file}")
        
        print(f"\n🎯 Optimización completada!")
        print(f"💡 Para un libro de 1000 caracteres: ~{1000/(len(text)/total_gen_time):.1f} segundos")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_xtts_optimized() 