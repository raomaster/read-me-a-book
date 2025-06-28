#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento de PiperEngine.text_to_bytes directamente
"""
import os
import logging
from src.engines.piper_engine import PiperEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    piper_path = "/usr/local/bin/piper/piper"
    model_path = "/app/models/es_MX/es_MX-claude-high.onnx"
    config_path = "/app/models/es_MX/es_MX-claude-high.onnx.json"
    test_text = "Hola mundo, esto es una prueba directa usando PiperEngine.text_to_bytes para ver si el audio se genera correctamente."
    output_wav = "test_direct_engine.wav"

    if not os.path.exists(piper_path):
        logger.error(f"No existe el ejecutable Piper: {piper_path}")
        return 1
    if not os.path.exists(model_path):
        logger.error(f"No existe el modelo: {model_path}")
        return 1
    if not os.path.exists(config_path):
        logger.error(f"No existe el config: {config_path}")
        return 1

    logger.info("Instanciando PiperEngine...")
    engine = PiperEngine(model_path, piper_path)
    logger.info("Llamando a text_to_bytes...")
    audio_bytes = engine.text_to_bytes(test_text)
    logger.info(f"Bytes recibidos: {len(audio_bytes)}")

    with open(output_wav, "wb") as f:
        f.write(audio_bytes)
    logger.info(f"Archivo guardado: {output_wav}")
    if len(audio_bytes) < 1000:
        logger.warning("El archivo generado es muy pequeño. Puede ser solo el header WAV.")
    else:
        logger.info("El archivo parece contener audio válido.")
    return 0

if __name__ == "__main__":
    exit(main()) 