#!/usr/bin/env python3
"""
XTTS v2 Ultra-Optimizado - Ana Florence para máxima velocidad
Optimizado para lectura de libros en español con voz femenina
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

def create_ultra_short_reference():
    """Crear audio de referencia ultra-corto (5 segundos)"""
    print("🔧 Creando audio de referencia ultra-corto (5 segundos)...")
    
    # Descargar el audio original
    mp3_url = "https://ia800608.us.archive.org/4/items/amoryllanto_2502_librivox/amoryllanto_15_sinues_64kb.mp3"
    subprocess.run([
        "python", "scripts/download_and_convert_reference.py", mp3_url, "reference_voice_full.wav"
    ], check=True)
    
    # Recortar a solo 5 segundos desde el segundo 25
    from pydub import AudioSegment
    audio = AudioSegment.from_wav("reference_voice_full.wav")
    
    # Tomar 5 segundos desde el segundo 25 (25000 ms a 30000 ms)
    start_ms = 25000  # Segundo 25
    end_ms = 30000    # Segundo 30
    audio_ultra_short = audio[start_ms:end_ms]
    
    # Guardar como referencia ultra-optimizada
    audio_ultra_short.export("reference_voice_ultra_short.wav", format="wav")
    
    # Limpiar archivo temporal
    if os.path.exists("reference_voice_full.wav"):
        os.remove("reference_voice_full.wav")
    
    print("✅ Audio de referencia ultra-corto creado: reference_voice_ultra_short.wav")

def split_text_into_small_chunks(text, max_chars=200):
    """Divide el texto en chunks muy pequeños para máxima velocidad"""
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

def test_xtts_ultra_optimized():
    print("🚀 XTTS v2 ULTRA-OPTIMIZADO - Ana Florence para velocidad máxima")
    print("=" * 80)
    
    # Texto de prueba (párrafo completo)
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    
    print(f"📝 Texto de prueba ({len(text)} caracteres): {text[:80]}...")
    
    # Crear audio de referencia ultra-corto
    create_ultra_short_reference()
    
    ref_file = "reference_voice_ultra_short.wav"
    
    # Normalizar texto
    normalized_text = normalize_text_with_gruut(text)
    print(f"📝 Texto normalizado: {normalized_text[:80]}...")
    
    # Dividir en chunks muy pequeños
    chunks = split_text_into_small_chunks(normalized_text, max_chars=200)
    print(f"📦 Texto dividido en {len(chunks)} chunks pequeños:")
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i}: {chunk[:50]}...")
    
    # Probar XTTS ultra-optimizado
    print(f"\n{'='*80}")
    print("EJECUTANDO XTTS v2 ULTRA-OPTIMIZADO")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        print("🔄 Inicializando XTTS v2...")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        init_time = time.time() - start_time
        print(f"✅ XTTS v2 inicializado en {init_time:.2f}s")
        
        # Procesar cada chunk con parámetros ultra-optimizados
        all_audio_files = []
        total_gen_time = 0
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n--- Procesando chunk {i}/{len(chunks)} ---")
            print(f"📝 Chunk: {chunk}")
            
            chunk_start = time.time()
            output_file = f"xtts_ultra_chunk_{i}.wav"
            
            tts.tts_to_file(
                text=chunk,
                file_path=output_file,
                speaker_wav=ref_file,
                language="es",
                temperature=0.01,  # Ultra-conservador para velocidad
                speed=1.2          # Más rápido
            )
            
            chunk_time = time.time() - chunk_start
            total_gen_time += chunk_time
            
            file_size = os.path.getsize(output_file) / 1024
            all_audio_files.append(output_file)
            
            print(f"✅ Chunk {i} generado: {output_file}")
            print(f"⏱️  Tiempo del chunk: {chunk_time:.2f}s")
            print(f"📁 Tamaño: {file_size:.1f} KB")
        
        total_time = time.time() - start_time
        
        print(f"\n{'='*80}")
        print("RESULTADOS ULTRA-OPTIMIZADOS")
        print(f"{'='*80}")
        print(f"📊 Tiempo de inicialización: {init_time:.2f}s")
        print(f"📊 Tiempo total de generación: {total_gen_time:.2f}s")
        print(f"📊 Tiempo total: {total_time:.2f}s")
        print(f"📊 Velocidad promedio: {len(text)/total_gen_time:.1f} caracteres/segundo")
        print(f"📊 Archivos generados: {len(all_audio_files)}")
        
        for file in all_audio_files:
            print(f"  ✅ {file}")
        
        # Estimación para libros
        chars_per_second = len(text) / total_gen_time
        book_estimate = 1000 / chars_per_second  # Para 1000 caracteres
        
        print(f"\n🎯 OPTIMIZACIÓN COMPLETADA:")
        print(f"✅ Voz femenina: XTTS v2 (Ana Florence)")
        print(f"⚡ Velocidad: {total_time:.2f}s para {len(text)} caracteres")
        print(f"📚 Estimación: ~{book_estimate:.1f}s para una página (1000 caracteres)")
        print(f"🎧 Archivos: {len(all_audio_files)} chunks generados")
        
        print(f"\n💡 MEJORAS APLICADAS:")
        print(f"   ✅ Audio de referencia ultra-corto (5 segundos)")
        print(f"   ⚡ Chunks pequeños (200 caracteres)")
        print(f"   🎯 Temperature ultra-conservadora (0.01)")
        print(f"   🚀 Speed aumentado (1.2)")
        print(f"   🌍 Voz femenina en español (Ana Florence)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_xtts_ultra_optimized() 