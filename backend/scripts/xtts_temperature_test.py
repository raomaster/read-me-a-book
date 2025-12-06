#!/usr/bin/env python3
"""
XTTS v2 Test de Temperaturas - Ana Florence con diferentes temperaturas
Prueba diferentes temperaturas con el proceso de 3 chunks en paralelo
"""
from TTS.api import TTS
import time
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydub import AudioSegment

def download_reference_audio():
    """Descarga y convierte el audio de referencia completo (sin recorte especial)"""
    mp3_url = "https://ia800608.us.archive.org/4/items/amoryllanto_2502_librivox/amoryllanto_15_sinues_64kb.mp3"
    ref_wav = "reference_voice.wav"
    if not os.path.exists(ref_wav):
        print(f"🔽 Descargando y convirtiendo voz de referencia desde: {mp3_url}")
        subprocess.run([
            "python", "scripts/download_and_convert_reference.py", mp3_url, ref_wav
        ], check=True)
        print(f"✅ Archivo de referencia listo: {ref_wav}")
    else:
        print(f"✅ Archivo de referencia ya existe: {ref_wav}")
    return ref_wav

def split_text_into_3_chunks(text):
    """Divide el texto en exactamente 3 chunks para procesamiento paralelo"""
    # Dividir por puntos para aproximar oraciones
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    total_sentences = len(sentences)
    sentences_per_chunk = total_sentences // 3
    chunks = []
    for i in range(3):
        start_idx = i * sentences_per_chunk
        if i == 2:
            end_idx = total_sentences
        else:
            end_idx = (i + 1) * sentences_per_chunk
        chunk_sentences = sentences[start_idx:end_idx]
        chunk_text = '. '.join(chunk_sentences)
        if chunk_text and not chunk_text.endswith('.'):
            chunk_text += '.'
        chunks.append(chunk_text)
    return chunks

def process_chunk_parallel(chunk_data):
    """Procesa un chunk individual en paralelo"""
    chunk_id, chunk_text, ref_file, temperature = chunk_data
    try:
        print(f"🔄 Iniciando chunk {chunk_id} con temp={temperature}...")
        chunk_start = time.time()
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        output_file = f"xtts_temp{temperature}_chunk_{chunk_id}.wav"
        tts.tts_to_file(
            text=chunk_text,
            file_path=output_file,
            speaker_wav=ref_file,
            language="es",
            temperature=temperature,
            speed=1.2
        )
        chunk_time = time.time() - chunk_start
        file_size = os.path.getsize(output_file) / 1024
        print(f"✅ Chunk {chunk_id} (temp={temperature}) completado en {chunk_time:.2f}s")
        return {
            "chunk_id": chunk_id,
            "temperature": temperature,
            "output_file": output_file,
            "time": chunk_time,
            "size": file_size,
            "success": True
        }
    except Exception as e:
        print(f"❌ Error en chunk {chunk_id} (temp={temperature}): {e}")
        return {
            "chunk_id": chunk_id,
            "temperature": temperature,
            "error": str(e),
            "success": False
        }

def merge_audio_files(audio_files, temperature, output_file=None):
    if not output_file:
        output_file = f"xtts_temp{temperature}_final.wav"
    print(f"🔗 Uniendo archivos para temp={temperature}...")
    try:
        audio_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        combined = AudioSegment.from_wav(audio_files[0])
        for audio_file in audio_files[1:]:
            audio_segment = AudioSegment.from_wav(audio_file)
            combined += AudioSegment.silent(duration=100) + audio_segment
        combined.export(output_file, format="wav")
        final_size = os.path.getsize(output_file) / 1024
        print(f"✅ Audio unido: {output_file} ({final_size:.1f} KB)")
        return output_file
    except Exception as e:
        print(f"❌ Error uniendo audio para temp={temperature}: {e}")
        return None

def test_temperature_with_parallel_chunks(temperature, ref_file):
    print(f"\n{'='*80}")
    print(f"PRUEBA CON TEMPERATURA: {temperature}")
    print(f"{'='*80}")
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    print(f"📝 Texto de prueba ({len(text)} caracteres): {text[:80]}...")
    chunks = split_text_into_3_chunks(text)
    print(f"📦 Texto dividido en 3 chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"   Chunk {i}: {chunk[:50]}...")
    chunk_data = [(i+1, chunk, ref_file, temperature) for i, chunk in enumerate(chunks)]
    start_time = time.time()
    results = []
    audio_files = []
    max_workers = 3
    print(f"🔄 Procesando 3 chunks en paralelo con temp={temperature}...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(process_chunk_parallel, data): data for data in chunk_data}
        for future in as_completed(future_to_chunk):
            result = future.result()
            results.append(result)
            if result['success']:
                audio_files.append(result['output_file'])
                print(f"📊 Chunk {result['chunk_id']} listo: {result['time']:.2f}s")
    audio_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    merge_start = time.time()
    final_audio = merge_audio_files(audio_files, temperature)
    merge_time = time.time() - merge_start
    total_time = time.time() - start_time
    successful_results = [r for r in results if r['success']]
    total_gen_time = sum(r['time'] for r in successful_results)
    print(f"\n📊 RESULTADOS PARA TEMPERATURA {temperature}:")
    print(f"   📊 Chunks procesados: {len(successful_results)}/3")
    print(f"   📊 Tiempo total de generación: {total_gen_time:.2f}s")
    print(f"   📊 Tiempo de unión: {merge_time:.2f}s")
    print(f"   📊 Tiempo total: {total_time:.2f}s")
    print(f"   📊 Velocidad promedio: {len(text)/total_time:.1f} caracteres/segundo")
    print(f"   📊 Archivo final: {final_audio}")
    return {
        "temperature": temperature,
        "total_time": total_time,
        "gen_time": total_gen_time,
        "merge_time": merge_time,
        "final_audio": final_audio,
        "success": len(successful_results) == 3
    }

def test_xtts_temperature_comparison():
    print("🎯 XTTS v2 COMPARACIÓN DE TEMPERATURAS - Ana Florence")
    print("Procesamiento de 3 chunks en paralelo con diferentes temperaturas")
    print("=" * 90)
    ref_file = download_reference_audio()
    temperatures = [0.01, 0.03, 0.05, 0.07]
    print(f"\n{'='*90}")
    print("EJECUTANDO COMPARACIÓN DE TEMPERATURAS")
    print(f"{'='*90}")
    all_results = []
    for temperature in temperatures:
        result = test_temperature_with_parallel_chunks(temperature, ref_file)
        all_results.append(result)
        print(f"🧹 Limpiando archivos temporales para temp={temperature}...")
        for i in range(1, 4):
            temp_file = f"xtts_temp{temperature}_chunk_{i}.wav"
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"   🗑️ Eliminado: {temp_file}")
    print(f"\n{'='*90}")
    print("RESULTADOS COMPARATIVOS DE TEMPERATURAS")
    print(f"{'='*90}")
    print(f"{'Temperatura':<12} {'Tiempo Total':<12} {'Tiempo Gen':<12} {'Tiempo Unión':<12} {'Archivo':<30}")
    print("-" * 90)
    successful_results = [r for r in all_results if r['success']]
    for result in successful_results:
        print(f"{result['temperature']:<12} {result['total_time']:<12.2f}s {result['gen_time']:<12.2f}s {result['merge_time']:<12.2f}s {result['final_audio']:<30}")
    if successful_results:
        fastest = min(successful_results, key=lambda x: x['total_time'])
        slowest = max(successful_results, key=lambda x: x['total_time'])
        print(f"\n🎯 ANÁLISIS COMPLETADO:")
        print(f"⚡ Temperatura más rápida: {fastest['temperature']} ({fastest['total_time']:.2f}s)")
        print(f"🐌 Temperatura más lenta: {slowest['temperature']} ({slowest['total_time']:.2f}s)")
        print(f"📁 Archivos finales generados: {len(successful_results)}")
        print(f"\n💡 RECOMENDACIONES:")
        print(f"   🎯 Para máxima velocidad: Usar temp={fastest['temperature']}")
        print(f"   🎨 Para mejor calidad: Usar temp=0.05 o 0.07")
        print(f"   ⚖️ Para balance: Usar temp=0.03")
        print(f"\n📁 ARCHIVOS GENERADOS:")
        for result in successful_results:
            file_size = os.path.getsize(result['final_audio']) / 1024
            print(f"   ✅ {result['final_audio']} ({file_size:.1f} KB)")
    if os.path.exists(ref_file):
        print(f"\n🧹 Archivo de referencia conservado: {ref_file}")

if __name__ == "__main__":
    test_xtts_temperature_comparison() 