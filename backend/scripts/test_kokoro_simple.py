#!/usr/bin/env python3
"""
Simple test script for Kokoro TTS en español
Run from backend directory: python scripts/test_kokoro_simple.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

def test_kokoro_tts():
    """Test Kokoro TTS con voces en español"""
    
    text = 'La mesa donde escribo no es precisamente un escritorio, pero es bonita. La he puesto debajo de la ventana. Encima coloqué un florero con rosas que corté del jardín, tempranito. Son preciosas; hay dos color té y cuatro blancas como nieve. Al lado está el retrato de papá. Lo estoy mirando. Tiene sus ojos fijos en mí, sus ojos claros, medio grises, medio verdes, y parece que me estuviera diciendo: "Patricia, Patricia, ¿quieres venir a mirar lo que resultó del trabajo de ayer?"'
    
    print("🎵 PRUEBA DE KOKORO TTS EN ESPAÑOL")
    print("=" * 50)
    print(f"Texto: {text}")
    print()
    
    # Voces en español según documentación oficial
    voces_espanol = [
        ('ef_dora', 'Femenina'),
        ('em_alex', 'Masculina'),
        ('em_santa', 'Masculina')
    ]
    
    resultados = []
    
    for voz, genero in voces_espanol:
        print(f"🔄 Probando voz {voz} ({genero})...")
        try:
            from kokoro import KPipeline
            import soundfile as sf
            
            start_time = time.time()
            pipeline = KPipeline(lang_code='e')
            init_time = time.time() - start_time
            
            gen_start = time.time()
            generator = pipeline(text, voice=voz)
            for i, (gs, ps, audio) in enumerate(generator):
                sf.write(f"test_kokoro_{voz}.wav", audio, 24000)
                break
            gen_time = time.time() - gen_start
            
            print(f"✅ Voz {voz} ({genero}): Inicialización {init_time:.2f}s, Generación {gen_time:.2f}s")
            print(f"✅ Audio generado: test_kokoro_{voz}.wav")
            resultados.append((voz, genero, True, gen_time))
            
        except Exception as e:
            print(f"❌ Error con voz {voz}: {e}")
            resultados.append((voz, genero, False, None))
        
        print()
    
    print("=" * 50)
    print("✅ PRUEBA COMPLETADA")
    print("📊 RESULTADOS:")
    for voz, genero, exito, tiempo in resultados:
        if exito:
            print(f"  ✅ {voz} ({genero}): {tiempo:.2f}s")
        else:
            print(f"  ❌ {voz} ({genero}): Error")
    
    print()
    print("🎵 Archivos generados:")
    for voz, genero, exito, _ in resultados:
        if exito:
            print(f"  - test_kokoro_{voz}.wav")
    print("🎧 Escucha los archivos para comparar calidad de audio")

if __name__ == "__main__":
    test_kokoro_tts() 