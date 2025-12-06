#!/usr/bin/env python3
"""
Descarga un archivo MP3 y lo convierte a WAV (16kHz, mono)
Uso: python scripts/download_and_convert_reference.py <url_mp3> <output_wav>
"""
import sys
import requests
from pydub import AudioSegment
import os

def download_mp3(url, filename):
    print(f"Descargando MP3 desde: {url}")
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
        print(f"✅ MP3 descargado: {filename}")
    else:
        raise Exception(f"Error al descargar MP3: {r.status_code}")

def convert_mp3_to_wav(mp3_path, wav_path, sample_rate=24000):
    print(f"Convirtiendo {mp3_path} a WAV ({sample_rate} Hz, mono)...")
    audio = AudioSegment.from_mp3(mp3_path)
    audio = audio.set_frame_rate(sample_rate).set_channels(1)
    audio.export(wav_path, format="wav")
    print(f"✅ WAV generado: {wav_path}")

def main():
    if len(sys.argv) != 3:
        print("Uso: python scripts/download_and_convert_reference.py <url_mp3> <output_wav>")
        sys.exit(1)
    url = sys.argv[1]
    wav_path = sys.argv[2]
    mp3_path = "temp_reference.mp3"
    try:
        download_mp3(url, mp3_path)
        convert_mp3_to_wav(mp3_path, wav_path)
    finally:
        if os.path.exists(mp3_path):
            os.remove(mp3_path)

if __name__ == "__main__":
    main() 