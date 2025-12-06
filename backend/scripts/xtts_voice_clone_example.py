#!/usr/bin/env python3
"""
Example script demonstrating voice cloning with XTTS v2
"""

import sys
import os
import logging
import argparse

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from engines.xtts_engine import XttsEngine

# Configure logging
logging.basicConfig(level=logging.INFO)

def voice_clone_example(speaker_wav_path: str, output_dir: str = "outputs"):
    """
    Example of voice cloning with XTTS v2.
    
    Args:
        speaker_wav_path: Path to speaker reference audio file
        output_dir: Directory to save generated audio files
    """
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Test texts in different languages
    test_texts = {
        "es": "Hola, mi nombre es XTTS v2. Soy un motor de síntesis de voz que puede clonar cualquier voz usando solo una muestra de audio corta. ¿Te gusta cómo sueno?",
        "en": "Hello, my name is XTTS v2. I am a text-to-speech engine that can clone any voice using just a short audio sample. How do you like how I sound?",
        "fr": "Bonjour, je m'appelle XTTS v2. Je suis un moteur de synthèse vocale qui peut cloner n'importe quelle voix en utilisant seulement un court échantillon audio. Comment trouvez-vous ma voix?",
        "de": "Hallo, mein Name ist XTTS v2. Ich bin eine Text-zu-Sprache-Engine, die jede Stimme mit nur einer kurzen Audio-Probe klonen kann. Wie gefällt Ihnen mein Klang?"
    }
    
    try:
        # Initialize XTTS engine with speaker reference
        print(f"Initializing XTTS v2 engine with speaker reference: {speaker_wav_path}")
        engine = XttsEngine(
            speaker_wav=speaker_wav_path,
            speed=1.0,
            temperature=0.1
        )
        
        # Generate audio for each language
        for lang, text in test_texts.items():
            print(f"\nGenerating audio for language: {lang}")
            print(f"Text: {text}")
            
            # Generate audio file
            output_path = os.path.join(output_dir, f"voice_clone_{lang}.wav")
            engine.text_to_speech(text, output_path)
            
            print(f"✅ Audio saved to: {output_path}")
            
            # Also test text_to_bytes method
            audio_bytes = engine.text_to_bytes(text)
            print(f"   Generated {len(audio_bytes)} bytes of audio data")
        
        print(f"\n🎉 Voice cloning test completed successfully!")
        print(f"All audio files saved in: {output_dir}")
        
    except Exception as e:
        print(f"❌ Error during voice cloning test: {e}")
        logging.error(f"Error during voice cloning test: {e}", exc_info=True)
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="XTTS v2 Voice Cloning Example")
    parser.add_argument(
        "speaker_wav", 
        help="Path to speaker reference audio file (WAV, MP3, etc.)"
    )
    parser.add_argument(
        "--output-dir", 
        default="outputs", 
        help="Output directory for generated audio files (default: outputs)"
    )
    
    args = parser.parse_args()
    
    # Check if speaker file exists
    if not os.path.exists(args.speaker_wav):
        print(f"❌ Speaker reference file not found: {args.speaker_wav}")
        sys.exit(1)
    
    # Run the example
    success = voice_clone_example(args.speaker_wav, args.output_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 