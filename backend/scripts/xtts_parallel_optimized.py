#!/usr/bin/env python3
"""
XTTS v2 Paralelo Ultra-Optimizado - Ana Florence con procesamiento paralelo
Genera chunks en paralelo y los une para máxima velocidad
"""
from TTS.api import TTS
import gruut
import time
import os
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydub import AudioSegment
import queue

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

def process_chunk_parallel(chunk_data):
    """Procesa un chunk individual en paralelo"""
    chunk_id, chunk_text, ref_file = chunk_data
    
    try:
        print(f"🔄 Iniciando chunk {chunk_id}...")
        chunk_start = time.time()
        
        # Crear TTS instance para este thread
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        
        output_file = f"xtts_parallel_chunk_{chunk_id}.wav"
        
        tts.tts_to_file(
            text=chunk_text,
            file_path=output_file,
            speaker_wav=ref_file,
            language="es",
            temperature=0.01,  # Ultra-conservador para velocidad
            speed=1.2          # Más rápido
        )
        
        chunk_time = time.time() - chunk_start
        file_size = os.path.getsize(output_file) / 1024
        
        print(f"✅ Chunk {chunk_id} completado en {chunk_time:.2f}s ({file_size:.1f} KB)")
        
        return {
            "chunk_id": chunk_id,
            "output_file": output_file,
            "time": chunk_time,
            "size": file_size,
            "success": True
        }
        
    except Exception as e:
        print(f"❌ Error en chunk {chunk_id}: {e}")
        return {
            "chunk_id": chunk_id,
            "error": str(e),
            "success": False
        }

def merge_audio_files(audio_files, output_file="xtts_parallel_merged.wav"):
    """Une todos los archivos de audio en orden"""
    print(f"🔗 Uniendo {len(audio_files)} archivos de audio...")
    
    try:
        # Cargar el primer archivo
        combined = AudioSegment.from_wav(audio_files[0])
        
        # Agregar los demás archivos
        for audio_file in audio_files[1:]:
            audio_segment = AudioSegment.from_wav(audio_file)
            # Agregar una pequeña pausa entre chunks (100ms)
            combined += AudioSegment.silent(duration=100) + audio_segment
        
        # Exportar archivo final
        combined.export(output_file, format="wav")
        
        final_size = os.path.getsize(output_file) / 1024
        print(f"✅ Audio unido: {output_file} ({final_size:.1f} KB)")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error uniendo audio: {e}")
        return None

def test_xtts_parallel_optimized():
    print("🚀 XTTS v2 PARALELO ULTRA-OPTIMIZADO - Ana Florence con procesamiento paralelo")
    print("=" * 90)
    
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
    
    # Preparar datos para procesamiento paralelo
    chunk_data = [(i+1, chunk, ref_file) for i, chunk in enumerate(chunks)]
    
    print(f"\n{'='*90}")
    print("EJECUTANDO XTTS v2 PARALELO ULTRA-OPTIMIZADO")
    print(f"{'='*90}")
    
    start_time = time.time()
    
    # Procesar chunks en paralelo
    results = []
    audio_files = []
    
    # Usar ThreadPoolExecutor para procesamiento paralelo
    # Máximo 3 threads para evitar sobrecarga
    max_workers = min(3, len(chunks))
    print(f"🔄 Procesando {len(chunks)} chunks en paralelo con {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todos los chunks para procesamiento
        future_to_chunk = {executor.submit(process_chunk_parallel, data): data for data in chunk_data}
        
        # Recolectar resultados conforme se completan
        for future in as_completed(future_to_chunk):
            result = future.result()
            results.append(result)
            
            if result['success']:
                audio_files.append(result['output_file'])
                print(f"📊 Chunk {result['chunk_id']} listo: {result['time']:.2f}s")
    
    # Ordenar archivos por chunk_id para unión correcta
    audio_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    
    # Unir todos los archivos de audio
    merge_start = time.time()
    final_audio = merge_audio_files(audio_files, "xtts_parallel_final.wav")
    merge_time = time.time() - merge_start
    
    total_time = time.time() - start_time
    
    # Calcular estadísticas
    successful_results = [r for r in results if r['success']]
    total_gen_time = sum(r['time'] for r in successful_results)
    
    print(f"\n{'='*90}")
    print("RESULTADOS PARALELOS ULTRA-OPTIMIZADOS")
    print(f"{'='*90}")
    print(f"📊 Chunks procesados: {len(successful_results)}/{len(chunks)}")
    print(f"📊 Tiempo total de generación: {total_gen_time:.2f}s")
    print(f"📊 Tiempo de unión: {merge_time:.2f}s")
    print(f"📊 Tiempo total: {total_time:.2f}s")
    print(f"📊 Velocidad promedio: {len(text)/total_time:.1f} caracteres/segundo")
    print(f"📊 Archivos generados: {len(audio_files)}")
    
    if final_audio:
        final_size = os.path.getsize(final_audio) / 1024
        print(f"📊 Archivo final: {final_audio} ({final_size:.1f} KB)")
    
    # Estimación para libros
    chars_per_second = len(text) / total_time
    book_estimate = 1000 / chars_per_second  # Para 1000 caracteres
    
    print(f"\n🎯 OPTIMIZACIÓN PARALELA COMPLETADA:")
    print(f"✅ Voz femenina: XTTS v2 (Ana Florence)")
    print(f"⚡ Velocidad: {total_time:.2f}s para {len(text)} caracteres")
    print(f"📚 Estimación: ~{book_estimate:.1f}s para una página (1000 caracteres)")
    print(f"🎧 Archivo final: {final_audio}")
    
    print(f"\n💡 MEJORAS PARALELAS APLICADAS:")
    print(f"   ✅ Procesamiento paralelo ({max_workers} workers)")
    print(f"   ✅ Audio de referencia ultra-corto (5 segundos)")
    print(f"   ⚡ Chunks pequeños (200 caracteres)")
    print(f"   🎯 Temperature ultra-conservadora (0.01)")
    print(f"   🚀 Speed aumentado (1.2)")
    print(f"   🌍 Voz femenina en español (Ana Florence)")
    print(f"   🔗 Unión automática de chunks")
    
    # Limpiar archivos temporales
    print(f"\n🧹 Limpiando archivos temporales...")
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"   🗑️ Eliminado: {audio_file}")
    
    if os.path.exists(ref_file):
        os.remove(ref_file)
        print(f"   🗑️ Eliminado: {ref_file}")

if __name__ == "__main__":
    test_xtts_parallel_optimized() 