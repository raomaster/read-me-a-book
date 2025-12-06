import functions_framework
import logging
import json
from flask import Request, Response
import os
import sys

# Ensure this directory is on sys.path so we can import sibling packages like `engines` and `services`
sys.path.append(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600'
    }

@functions_framework.http
def text_to_audio(request: Request) -> Response:
    headers = create_cors_headers()

    # Imports locales para evitar problemas de importación en el arranque del contenedor
    from engines.cloud_tts_engine import CloudTTSEngine
    from services.tts_service import TTSService

    try:
        # CORS preflight
        if request.method == 'OPTIONS':
            return Response('', status=204, headers=headers)

        # Health check simple
        if getattr(request, 'path', '') == '/health':
            return Response(
                json.dumps({"status": "ok"}),
                status=200,
                headers={'Content-Type': 'application/json', **headers}
            )

        # Listar voces (GET /voices)
        if request.method == 'GET':
            path = getattr(request, 'path', '')
            if path.rstrip('/') == '/voices' or path.endswith('/voices'):
                try:
                    engine = CloudTTSEngine(lang='es-ES')
                    api_resp = engine.client.list_voices()
                    spanish_voices = []
                    for v in api_resp.voices:
                        if any(code.startswith('es') for code in v.language_codes):
                            spanish_voices.append({
                                "name": v.name,
                                "language_codes": list(v.language_codes),
                            })
                    payload = json.dumps({"voices": spanish_voices}, ensure_ascii=False)
                    return Response(
                        payload,
                        status=200,
                        headers={'Content-Type': 'application/json', **headers}
                    )
                except Exception as e:
                    logger.error(f"Error listando voces: {e}")
                    return Response(
                        json.dumps({"error": "Error listando voces"}),
                        status=500,
                        headers={'Content-Type': 'application/json', **headers}
                    )

        # Solo permitir POST para síntesis
        if request.method != 'POST':
            return Response(
                json.dumps({"error": "Método no permitido"}),
                status=405,
                headers={'Content-Type': 'application/json', **headers}
            )

        # Obtener datos del request
        try:
            data = request.get_json(silent=True) or {}
        except Exception:
            data = {}

        if not isinstance(data, dict) or not data:
            return Response(
                json.dumps({"error": "JSON requerido"}),
                status=400,
                headers={'Content-Type': 'application/json', **headers}
            )

        text = str(data.get('text', '')).strip()
        if not text:
            return Response(
                json.dumps({"error": "El campo 'text' es requerido"}),
                status=400,
                headers={'Content-Type': 'application/json', **headers}
            )

        provider = data.get('provider', 'gtts')
        lang = data.get('lang', 'es')
        voice_name = data.get('voice_name')

        logger.info(f"Procesando: {len(text)} caracteres con {provider}")

        tts_service = TTSService()
        audio_data = tts_service.generate_audio(
            text=text,
            provider=provider,
            lang=lang,
            voice_name=voice_name
        )

        # Validar que el audio no esté vacío
        if not audio_data or len(audio_data) == 0:
            logger.error("Se generó audio vacío")
            return Response(json.dumps({"error": "Audio vacío generado"}), status=500, headers={'Content-Type': 'application/json', **headers})

        audio_headers = {
            **headers,
            'Content-Type': 'audio/mpeg',
            'Content-Length': str(len(audio_data)),
            'Cache-Control': 'public, max-age=3600',
            'Content-Disposition': 'attachment; filename="audio.mp3"'
        }

        logger.info(f"Audio generado exitosamente: {len(audio_data)} bytes")
        return Response(audio_data, status=200, headers=audio_headers)

    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return Response(json.dumps({"error": "Error interno del servidor"}), status=500, headers={'Content-Type': 'application/json', **headers})
    