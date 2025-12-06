#!/usr/bin/env python3
"""
Test script for XTTS v2 engine
Simple test to verify the engine works correctly
"""

import sys
import os
import logging
from pathlib import Path

try:
    # Test basic imports first
    import soundfile
    import numpy as np
    print("✓ Basic audio libraries imported successfully")
    
    # Test TTS import (using the standard import from documentation)
    from TTS.api import TTS
    print("✓ TTS library imported successfully")
    
    # Test our custom modules - use absolute imports from src directory
    from engines.xtts_engine import XttsEngine
    from config import XTTS_CONFIG
    print("✓ Custom modules imported successfully")
    
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print("Make sure you're running from the src directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def test_xtts_engine():
    """Test XTTS engine with long text"""
    
    print("=== Testing XTTS v2 Engine ===")
    
    # Test text - longer text to test chunking and processing
    test_text = """
    La inteligencia artificial ha revolucionado la forma en que interactuamos con la tecnología. 
    Desde asistentes virtuales hasta sistemas de reconocimiento de voz, la IA está presente en 
    nuestra vida cotidiana. Los modelos de lenguaje como XTTS v2 representan un avance significativo 
    en la síntesis de voz, permitiendo generar audio de alta calidad que suena natural y expresivo.
    
    Este motor de texto a voz puede procesar textos largos de manera eficiente, dividiendo el 
    contenido en fragmentos manejables y manteniendo la coherencia en la entonación y el ritmo. 
    Es especialmente útil para la creación de audiolibros, donde la calidad del audio y la 
    naturalidad de la voz son fundamentales para la experiencia del usuario.
    
    La tecnología detrás de XTTS v2 utiliza redes neuronales avanzadas y técnicas de aprendizaje 
    profundo para analizar el contexto del texto y generar una voz que no solo reproduce las 
    palabras, sino que también captura las emociones y la intención del mensaje original.
    """
    
    try:
        # Initialize engine with default settings
        print("Initializing XTTS engine...")
        engine = XttsEngine(
            language="es",
            speed=1.0,
            temperature=0.1
        )
        print("✓ Engine initialized successfully")
        
        # Test text_to_bytes
        print(f"Generating audio for text (length: {len(test_text)} characters)...")
        audio_bytes = engine.text_to_bytes(test_text)
        print(f"✓ Audio generated successfully: {len(audio_bytes)} bytes")
        
        # Save test audio
        backend_dir = Path(__file__).parent.parent
        output_path = backend_dir / "outputs" / "test_xtts_long_output.wav"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        
        print(f"✓ Audio saved to: {output_path}")
        
        # Test text_to_speech
        print("Testing text_to_speech method...")
        file_output_path = backend_dir / "outputs" / "test_xtts_long_file.wav"
        engine.text_to_speech(test_text, str(file_output_path))
        print(f"✓ File output saved to: {file_output_path}")
        
        print("\n=== All tests passed! ===")
        print(f"✓ Text length: {len(test_text)} characters")
        print(f"✓ Audio bytes generated: {len(audio_bytes)} bytes")
        print(f"✓ Files saved: {output_path.name}, {file_output_path.name}")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        logging.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_xtts_engine()
    sys.exit(0 if success else 1) 