# Read Me a Book — Contexto técnico y guía de trabajo

Este documento resume la arquitectura del proyecto, sus componentes y los contextos clave necesarios para trabajar, extender y mantener el sistema.

Contenido:
- Resumen del proyecto
- Arquitectura y directorios
- Backend (FastAPI)
- Motores de TTS disponibles
- Configuración y variables de entorno
- Frontend (SvelteKit)
- Flujo de uso e integración Frontend/Backend
- Ejecución local y con Docker
- Consideraciones de desarrollo
- Áreas de mejora y tareas pendientes


## 1) Resumen del proyecto

Read Me a Book es una aplicación que:
- Convierte documentos en audiolibros (PDF → EPUB, EPUB → Audio, Texto libre → Audio).
- Permite configurar el motor de Texto a Voz (TTS) y sus parámetros desde el frontend.
- Exponer un API backend (FastAPI) y una interfaz web frontend (SvelteKit), con soporte de PWA, temas y i18n.
- Soporta varios motores TTS: gTTS, Piper, XTTS v2 (Coqui TTS Community), y Kokoro TTS.

Repositorio estructurado como monorepo con dos carpetas principales: `backend/` y `frontend/`.


## 2) Arquitectura y directorios

Estructura principal del repositorio:
- `backend/`
  - `src/` (código del API y servicios)
    - `main.py` (API FastAPI, endpoints principales)
    - `services/` (servicios de PDF, EPUB, audio)
    - `engines/` (implementaciones de motores TTS y fábrica)
    - `interfaces.py` (contrato común para engines TTS)
    - `config.py` (configuración centralizada)
  - `Dockerfile` (imagen para backend)
  - `models/` (modelos de voces de Piper descargados)
  - `outputs/` (salidas de procesamiento por solicitud)
  - `requirements*.txt` (dependencias)
- `frontend/`
  - `src/` (SvelteKit + Tailwind + i18n)
  - `vite.config.ts` (servidor de desarrollo y build)
  - `package.json` (scripts y dependencias)
  - `Dockerfile` (imagen para frontend)
- `docs/` (capturas y documentación)
- `docker-compose.yml` y `docker-compose.override.yml` (orquestación)
- `env.example` (variables de entorno del frontend)


## 3) Backend (FastAPI)

Archivo clave: `backend/src/main.py`

Características principales:
- Framework: FastAPI + Uvicorn.
- CORS: Permitir todos los orígenes durante desarrollo.
- Puertos:
  - FastAPI: 8000 (por defecto).
- Endpoints:
  1. `POST /pdf_to_epub`
     - Entrada: archivo PDF (`UploadFile`).
     - Valida `content_type` = `application/pdf`.
     - Extrae texto del PDF y genera un EPUB (calibre/servicios).
     - Devuelve `FileResponse` con el EPUB.
  2. `POST /epub_to_audio`
     - Entrada: archivo EPUB (`UploadFile`).
     - Valida `content_type` = `application/epub+zip`.
     - Parámetros (Query): 
       - `tts_provider`: `gtts` | `piper` | `xtts` | `kokoro`
       - `lang`: idioma (ver `SUPPORTED_LANGUAGES` de XTTS)
       - `piper_voice_key`: clave de voz Piper (ver `PIPER_VOICES_CONFIG`)
       - `xtts_speaker_wav`: ruta de audio referencia para XTTS
       - `xtts_speed`, `xtts_temperature`: ajustes del modelo XTTS
       - `kokoro_voice`: voz específica en Kokoro
     - Flujo:
       - Guarda EPUB, extrae texto, persiste `texto_extraido.txt` en `outputs/<uuid>/`.
       - Crea el engine TTS según `tts_provider`.
       - Genera audio por chunks grandes (mejor calidad), concatena y guarda.
       - Devuelve el archivo de audio (WAV para Piper/Kokoro/XTTS; MP3 para gTTS).
  3. `POST /text_to_audio`
     - Entrada: JSON `{ "text": "..." }` (`TextToAudioRequest`).
     - Parámetros (Query): mismos que `epub_to_audio`.
     - Flujo:
       - Crea el engine TTS y realiza streaming de audio en chunks.
       - `media_type`: `audio/mpeg` para gTTS, `audio/wav` para el resto.
       - Para Piper: añade encabezado WAV al principio del stream (primer chunk).
       - Control de reintentos y pequeños delays por proveedor.

Servicios auxiliares:
- `services/pdf_service.py`: extracción de texto desde PDF.
- `services/epub_service.py`: generación de EPUB a partir de texto.
- `services/audio_service.py`: extracción de texto de EPUB.

División en chunks y streaming:
- `src/utils/text_splitter.py` usado para fragmentar el texto.
- Configurable vía `STREAMING_CONFIG` (`chunk_size`, `max_retries`, `gtts_delay`, `piper_delay`).
- Cuando el proveedor es Piper y se hace streaming: se antepone un header WAV con `create_wav_header(sample_rate)`.

Soporte Windows:
- Ajuste de política del event loop (`WindowsProactorEventLoopPolicy`) si el SO es Windows.


## 4) Motores de TTS disponibles

Fábrica de engines: `backend/src/engines/engine_factory.py`
- `create_engine(engine_type, lang, ...)` retorna una instancia que implementa `TextToSpeechInterface`.

Contrato común: `backend/src/interfaces.py`
- Métodos:
  - `text_to_speech(text, output_path)` → genera un archivo.
  - `text_to_bytes(text)` → devuelve el audio como bytes.

Motores:
- `gtts_engine.py`
  - Usa Google Text-to-Speech (gTTS).
  - Idioma via `lang`.
  - Guarda/retorna MP3.
- `piper_engine.py`
  - Ejecuta Piper como proceso externo con `subprocess`.
  - Necesita: `piper_executable_path`, `model_path` (derivado del `piper_voice_key`).
  - Determina `sample_rate` desde el JSON del modelo si existe.
  - Genera WAV.
- `xtts_engine.py` (Coqui TTS Community, XTTS v2)
  - Parámetros: `speaker_wav`, `language`, `speed`, `temperature`.
  - Por defecto usa `cpu`.
  - Genera WAV (se maneja con archivo temporal y se regresa como bytes).
  - Requiere dependencias adicionales (coqui-tts, torch, torchaudio).
- `kokoro_engine.py`
  - Usa `KPipeline` de Kokoro TTS.
  - Mapeo de idioma → `lang_code` interno.
  - Voz por defecto según idioma; configurable por `kokoro_voice`.
  - Genera WAV.

Validaciones de parámetros:
- El backend verifica coherencia de `tts_provider`, `lang`, `piper_voice_key`, etc. antes de procesar.


## 5) Configuración y variables de entorno

Archivo central: `backend/src/config.py`
- Rutas externas (leídas desde `.env` en `backend/`):
  - `TESSERACT_CMD_PATH`, `CALIBRE_EBOOK_CONVERT_PATH`, `POPPLER_PATH`, `PIPER_EXECUTABLE_PATH`.
- Directorios internos:
  - `PIPER_MODELS_BASE_DIR = BASE_DIR / "models"` (modelos .onnx y JSON).
  - `OUTPUTS_DIR = BASE_DIR / "outputs"` (salidas por solicitud).
- Voces Piper disponibles (mapa `PIPER_VOICES_CONFIG`), ej.:
  - `es_MX-claude-high`, `es_MX-ald-medium`, `es_ES-mls_9972-low`, etc.
- Configs de streaming:
  - `STREAMING_CONFIG` y `COMPLETE_AUDIO_CONFIG` (chunk_size, retries, delays).
- Config de XTTS:
  - `default_speed`, `default_temperature`, `default_language`, `sample_rate`, `supported_languages`.

Frontend `.env` de ejemplo: `env.example`
- `BACKEND_URL=https://leeme.mooo.com/api`
- Para desarrollo local, cambiar a `http://localhost:8000`.

Docker (backend): `backend/Dockerfile`
- Instala: `tesseract-ocr`, `poppler-utils`, `ffmpeg`, `calibre`, descarga Piper según arquitectura.
- Define ENV para paths.
- Descarga modelos Piper al directorio `./models/...`.
- Expone puerto 8000 y ejecuta `python -m src.main`.


## 6) Frontend (SvelteKit)

Configuración Vite: `frontend/vite.config.ts`
- Plugins: `sveltekit`, `@tailwindcss/vite`, `@vite-pwa/sveltekit`.
- Dev server:
  - `host: true` (0.0.0.0)
  - `port: 80`
  - `allowedHosts: ['leeme.mooo.com']`
- Build: `outDir: 'build'`.

Scripts (npm): `frontend/package.json`
- `dev`: `vite dev`
- `build`: `vite build`
- `preview`: `vite preview`
- `check`: `svelte-check` + TS config
- `lint`: `prettier` + `eslint`

Características del frontend:
- Rutas clave:
  - `/` (pantalla principal)
  - `/reader/[bookId]` (vista de lectura y TTS)
- Componentes:
  - Configuración TTS (`TTSConfigurator.svelte`): seleccionar motor, idioma y voz Piper.
  - Switchers de tema, idioma y tamaño de fuente.
- i18n:
  - `fallbackLocale`: `es`
  - Cadenas en `src/lib/i18n/en.ts` y `src/lib/i18n/es.ts`.
- UI/Temas:
  - Tailwind 4 + variables CSS en `app.css` para paletas (Light, Dark, Princess, Ocean).
- PWA:
  - Configurado con `@vite-pwa/sveltekit` (estrategia `generateSW`).


## 7) Flujo de uso e integración Frontend/Backend

- El frontend debe conocer `BACKEND_URL` (desde `.env` del frontend).
- Escenarios típicos:
  1. Convertir PDF → EPUB:
     - El frontend sube un PDF a `/pdf_to_epub`.
     - Recibe un archivo EPUB para descarga/uso.
  2. Convertir EPUB → Audio:
     - El frontend sube un EPUB a `/epub_to_audio` con los parámetros de TTS seleccionados.
     - Recibe un archivo de audio generado (por chunks grandes, mayor calidad).
  3. Texto libre → Audio (streaming):
     - El frontend llama a `/text_to_audio` con JSON `{ text: "..." }` y parámetros de TTS.
     - Reproduce el streaming (MPEG para gTTS, WAV para Piper/XTTS/Kokoro).
- Piper:
  - En streaming, el backend añade un encabezado WAV antes del primer chunk.
  - `piper_voice_key` debe estar en `PIPER_VOICES_CONFIG` y existir el modelo correspondiente.


## 8) Ejecución local y con Docker

Backend (local):
- Requisitos:
  - Python 3.12
  - Dependencias de `requirements.txt`
  - Herramientas externas opcionales según la ruta configurada (`tesseract`, `poppler`, `calibre`, `piper`).
- Ejecución:
  - Asegurar `.env` con rutas (o usar defaults).
  - Levantar FastAPI con `python -m src.main` (puerto 8000).

Backend (Docker):
- Construir imagen usando `backend/Dockerfile`.
- Piper y modelos descargados en build.
- Expuesto en `8000`.

Frontend:
- `.env` con `BACKEND_URL`.
- Desarrollo: `vite dev` (puerto 80, host true).
- Build: `vite build`; `vite preview` para servir el build.

Docker Compose:
- `docker-compose.yml` define servicios (frontend y posiblemente backend).
- Ajustar `BACKEND_URL` del frontend para apuntar al backend en Docker o local según el entorno.

## 8.1) Desarrollo Local con Google Cloud Functions

**Ubicación**: `backend/src_gcloud/`

**Propósito**: 
- Desarrollo y testing del componente TTS que se despliega en Google Cloud Functions Gen2
- Simulación exacta del entorno de producción usando Functions Framework

**Archivos clave**:
- `local_test.py`: Función principal con decorador `@functions_framework.http`
- `run_local.py`: Script de conveniencia para ejecutar el servidor local
- `requirements.txt`: Dependencias incluyendo `functions-framework==3.*`

**Arquitectura**:
- Usa `@functions_framework.http` en lugar de Flask app tradicional
- Función única que maneja todas las rutas basada en `request.path` y `request.method`
- Imports relativos (`from .services.tts_service import TTSService`) idénticos a Cloud Functions
- Compatible con despliegue directo sin modificaciones

**Ejecución**:
```bash
cd backend/src_gcloud
python run_local.py
```

**Endpoints disponibles**:
- `POST /`: Conversión de texto a audio
- `GET /health`: Health check
- `OPTIONS /`: CORS preflight

**Ventajas del enfoque**:
- ✅ Compatibilidad 100% con Google Cloud Functions Gen2
- ✅ No requiere modificaciones para despliegue
- ✅ Debugging local completo
- ✅ Imports relativos funcionan correctamente
- ✅ Misma estructura de request/response que producción

**Diferencias con el backend FastAPI principal**:
- Enfoque de función única vs. múltiples endpoints
- Functions Framework vs. FastAPI/Uvicorn
- Diseñado específicamente para Cloud Functions
- Menor superficie de ataque y mayor simplicidad


## 9) Consideraciones de desarrollo

- Mantenimiento de modelos Piper:
  - Los modelos deben existir en `backend/models/...` con su archivo JSON (`.onnx.json`) si se requiere `sample_rate`.
- Persistencia de salidas:
  - `outputs/<uuid>/` contiene archivos temporales y resultados (texto extraído, audio).
- Validación estricta de parámetros TTS:
  - Evita errores en ejecución (`ValueError`, `FileNotFoundError`, etc.).
- Logging:
  - Informativo y con detalles por chunk (progreso en completo/streaming).
- CORS abierto:
  - Durante desarrollo, orígenes permitidos `*`. Para producción, restringir.
- Windows:
  - Política del loop asyncio ajustada (mejor compatibilidad).
- Seguridad:
  - Sanitizar entradas (p.ej. nombres de archivo/título).
  - Confirmar tipos MIME (`content_type`) de archivos.


## 10) Áreas de mejora y tareas pendientes

- Documentar explícitamente formatos de respuesta en `/epub_to_audio` (nombre final y tipo exacto).
- Añadir pruebas automáticas (unit/integration) para cada engine TTS, especialmente streaming.
- Mejorar gestión de errores y reintentos por proveedor (timeouts, fallback).
- Parametrizar `allowedHosts` y puertos del frontend por entorno.
- Añadir soporte de colas/trabajos en background para archivos largos (celery/rq si se desea).
- Integrar y/o unificar el backend antiguo en Flask (`backend/src/server.py`) si aún se necesita OCR (ahora FastAPI no expone rutas OCR explícitas).
- Completar documentación de modelos Kokoro/XTTS y su instalación en producción.


## 11) Recursos clave y ubicación de archivos

- Backend (FastAPI y servicios):
  - `backend/src/main.py` — Endpoints y configuración principal.
  - `backend/src/services/` — PDF/EPUB/audio.
  - `backend/src/engines/` — Motores TTS y fábrica.
  - `backend/src/interfaces.py` — Contrato TTS.
  - `backend/src/config.py` — Variables, rutas y configuración TTS.
- Frontend (SvelteKit):
  - `frontend/src/` — Componentes, rutas, i18n y estilos.
  - `frontend/vite.config.ts` — Configuración de server y PWA.
  - `frontend/package.json` — Scripts de desarrollo y build.
- Configuración:
  - `env.example` — URL del backend para el frontend.
  - `backend/Dockerfile` — Build del backend con herramientas y modelos.
- Salidas y modelos:
  - `backend/outputs/` — Resultados por solicitud.
  - `backend/models/` — Modelos de Piper (.onnx y .json).

---