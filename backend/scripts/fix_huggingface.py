#!/usr/bin/env python3
"""
Script para arreglar el problema con modelos de Hugging Face
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🔧 {description}")
    print(f"Comando: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout}")
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error ejecutando comando: {e}")
        return False

def check_current_versions():
    """Verifica las versiones actuales"""
    print("📋 VERIFICANDO VERSIONES ACTUALES")
    print("=" * 50)
    
    run_command("pip show coqui-tts", "Versión actual de coqui-tts")
    run_command("pip show huggingface_hub", "Versión actual de huggingface_hub")
    run_command("pip show torch", "Versión actual de PyTorch")

def try_solutions():
    """Intenta diferentes soluciones"""
    print("\n🔧 INTENTANDO SOLUCIONES")
    print("=" * 50)
    
    solutions = [
        ("pip install --upgrade coqui-tts", "Actualizar coqui-tts a la última versión"),
        ("pip install --upgrade huggingface_hub", "Actualizar huggingface_hub"),
        ("pip install --upgrade transformers", "Actualizar transformers"),
        ("pip install --upgrade torch torchaudio", "Actualizar PyTorch"),
        ("pip install --force-reinstall coqui-tts", "Reinstalar coqui-tts"),
    ]
    
    for command, description in solutions:
        success = run_command(command, description)
        if success:
            print(f"✅ {description} - EXITOSO")
        else:
            print(f"❌ {description} - FALLÓ")

def test_after_fix():
    """Prueba si el problema se arregló"""
    print("\n🧪 PROBANDO DESPUÉS DE LAS REPARACIONES")
    print("=" * 50)
    
    test_code = '''
import sys
from TTS.api import TTS

try:
    print("Probando XTTS v2 de Hugging Face...")
    tts = TTS("coqui/XTTS-v2")
    print("✅ XTTS v2 funciona correctamente!")
    success = True
except Exception as e:
    print(f"❌ XTTS v2 aún falla: {e}")
    success = False

try:
    print("Probando FastSpeech2...")
    tts = TTS("facebook/fastspeech2-es-css10")
    print("✅ FastSpeech2 funciona correctamente!")
    success = success and True
except Exception as e:
    print(f"❌ FastSpeech2 aún falla: {e}")
    success = False

print(f"\\nResultado: {'✅ ÉXITO' if success else '❌ AÚN FALLA'}")
'''
    
    with open("temp_test.py", "w") as f:
        f.write(test_code)
    
    run_command("python temp_test.py", "Prueba de modelos de Hugging Face")
    
    # Limpiar archivo temporal
    try:
        os.remove("temp_test.py")
    except:
        pass

def main():
    print("🔧 ARREGLANDO MODELOS DE HUGGING FACE")
    print("=" * 60)
    
    # Verificar versiones actuales
    check_current_versions()
    
    # Intentar soluciones
    try_solutions()
    
    # Verificar versiones después de las actualizaciones
    print("\n📋 VERIFICANDO VERSIONES DESPUÉS DE ACTUALIZACIONES")
    print("=" * 50)
    check_current_versions()
    
    # Probar si se arregló
    test_after_fix()
    
    print("\n" + "=" * 60)
    print("🎯 PROCESO COMPLETADO")
    print("=" * 60)
    print("Si los modelos aún fallan, las opciones son:")
    print("1. Usar modelos locales (que ya funcionan)")
    print("2. Investigar más a fondo el problema de compatibilidad")
    print("3. Usar una versión específica de coqui-tts que funcione")

if __name__ == "__main__":
    main() 