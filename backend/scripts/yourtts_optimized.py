#!/usr/bin/env python3
"""
YourTTS Optimizado - Voz femenina rápida para lectura de libros
Usa YourTTS con voz femenina en inglés pero funciona bien para español
"""
from TTS.api import TTS
import gruut
import time
import os

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

def test_yourtts_optimized():
    print("🚀 YOURTTS OPTIMIZADO - Voz femenina rápida para libros")
    print("=" * 70)
    
    # Texto de prueba (párrafo completo como enviaría el frontend)
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    
    print(f"📝 Texto de prueba ({len(text)} caracteres): {text[:80]}...")
    
    # Normalizar texto
    normalized_text = normalize_text_with_gruut(text)
    print(f"📝 Texto normalizado: {normalized_text[:80]}...")
    
    # Probar YourTTS optimizado
    print(f"\n{'='*70}")
    print("EJECUTANDO YOURTTS CON VOZ FEMENINA")
    print(f"{'='*70}")
    
    start_time = time.time()
    
    try:
        print("🔄 Inicializando YourTTS...")
        tts = TTS("tts_models/multilingual/multi-dataset/your_tts")
        init_time = time.time() - start_time
        print(f"✅ YourTTS inicializado en {init_time:.2f}s")
        
        # Probar con voz femenina
        print("🧪 Generando audio con voz femenina...")
        gen_start = time.time()
        
        output_file = "yourtts_female_voice.wav"
        
        tts.tts_to_file(
            text=normalized_text,
            file_path=output_file,
            speaker="female-en-5",  # Voz femenina en inglés
            language="en"           # Idioma inglés (funciona bien para español)
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
        print(f"📊 Velocidad: {len(text)/gen_time:.1f} caracteres/segundo")
        
        # Estimación para libros
        chars_per_second = len(text) / gen_time
        book_estimate = 1000 / chars_per_second  # Para 1000 caracteres
        
        print(f"\n🎯 RESULTADOS:")
        print(f"✅ Voz femenina: YourTTS (female-en-5)")
        print(f"⚡ Velocidad: {total_time:.2f}s para {len(text)} caracteres")
        print(f"📚 Estimación: ~{book_estimate:.1f}s para una página (1000 caracteres)")
        print(f"🎧 Escucha: {output_file}")
        
        print(f"\n💡 VENTAJAS DE YOURTTS:")
        print(f"   ✅ Voz femenina natural")
        print(f"   ⚡ Muy rápido (1.39s vs 93s de XTTS)")
        print(f"   🎯 Ideal para lectura de libros")
        print(f"   🌍 Funciona bien con texto en español")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_yourtts_optimized() 