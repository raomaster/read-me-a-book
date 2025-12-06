#!/usr/bin/env python3
"""
Test script for XTTS v2 engine
"""

import sys
import os
import logging

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from engines.xtts_engine import XttsEngine

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_xtts_engine():
    """Test the XTTS engine with a simple text."""
    
    # Test text
    test_text = "Hola, esto es una prueba del motor XTTS v2. ¿Cómo te va?"
    
    try:
        # Initialize XTTS engine (will use default HuggingFace model)
        print("Initializing XTTS v2 engine...")
        engine = XttsEngine(
            language="es",
            speed=1.0,
            temperature=0.1
        )
        
        # Test text_to_bytes method
        print("Testing text_to_bytes method...")
        audio_bytes = engine.text_to_bytes(test_text)
        print(f"Generated audio: {len(audio_bytes)} bytes")
        
        # Test text_to_speech method
        print("Testing text_to_speech method...")
        output_path = "test_xtts_output.wav"
        engine.text_to_speech(test_text, output_path)
        print(f"Audio saved to: {output_path}")
        
        print("✅ XTTS engine test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing XTTS engine: {e}")
        logging.error(f"Error testing XTTS engine: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = test_xtts_engine()
    sys.exit(0 if success else 1) 