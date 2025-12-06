import functions_framework
from flask import Request, Response
import json
import logging

# Import relativo - exactamente como en Cloud Functions
from .services.tts_service import TTSService

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_cors_headers():
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600'
    }

@functions_framework.http
def app(request: Request) -> Response:
    """
    Cloud Function para desarrollo local - simula exactamente Cloud Functions Gen2
    """
    headers = create_cors_headers()
    
    try:
        # CORS preflight
        if request.method == 'OPTIONS':
            return Response('', status=204, headers=headers)
        
        # Health check
        if request.path == '/health':
            return Response(
                json.dumps({"status": "ok"}),
                status=200,
                headers={'Content-Type': 'application/json', **headers}
            )
        
        # Solo permitir POST para /text_to_audio
        if request.method != 'POST':
            return Response(
                json.dumps({"error": "Método no permitido"}),
                status=405,
                headers={**headers, 'Content-Type': 'application/json'}
            )
        
        # Obtener datos del request
        data = request.get_json()
        if not data:
            return Response(
                json.dumps({"error": "JSON requerido"}),
                status=400,
                headers={**headers, 'Content-Type': 'application/json'}
            )
        
        text = data.get('text', '').strip()
        if not text:
            return Response(
                json.dumps({"error": "El campo 'text' es requerido"}),
                status=400,
                headers={**headers, 'Content-Type': 'application/json'}
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
            return Response(
                json.dumps({"error": "Audio vacío generado"}),
                status=500,
                headers={**headers, 'Content-Type': 'application/json'}
            )
        
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
        logger.error(f"Error: {e}")
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            headers={**headers, 'Content-Type': 'application/json'}
        )