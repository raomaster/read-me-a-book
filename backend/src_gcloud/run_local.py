"""
Script para ejecutar el servidor local usando Functions Framework
Simula exactamente el entorno de Google Cloud Functions Gen2
"""

import subprocess
import sys

if __name__ == '__main__':
    print("🚀 Iniciando servidor TTS con Functions Framework")
    print("📋 Simula exactamente Google Cloud Functions Gen2")
    print("🌐 Servidor disponible en: http://localhost:8080")
    print()
    
    cmd = [
        sys.executable, "-m", "functions_framework",
        "--target=app",
        "--source=local_test.py",
        "--port=8080",
        "--debug"
    ]
    
    subprocess.run(cmd)