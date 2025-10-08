# Desarrollo local (sin Docker)

Esta guía explica cómo levantar el backend (FastAPI) y el frontend (SvelteKit/Vite) en local, sin Docker, para pruebas de desarrollo.

## Prerrequisitos

- Python 3.10+ (ideal 3.12) y `pip`
- Node.js LTS (incluye `npm`)
- pnpm opcional (puedes usar `npm` si prefieres)

> Opcional según funcionalidades:
> - TTS Piper (si quieres usar voces locales con Piper): instalar `piper.exe` y añadir al PATH o configurar en `.env`
> - Tesseract, Poppler, Calibre (solo si vas a usar endpoints de PDF/EPUB)

## Backend (FastAPI)

1. Crear y activar entorno virtual:

```bat
python -m venv backend\venv-backend
```

```bat
.\backend\venv-backend\Scripts\activate
```

2. Instalar dependencias:

```bat
pip install -r backend\requirements.txt
```

3. (Opcional) Configurar `.env` en `backend/.env` si vas a usar Piper o PDF/EPUB:

# Piper (si piper.exe no está en el PATH)
PIPER_EXECUTABLE_PATH=C:\ruta\completa\a\piper.exe

# Solo PDF/EPUB:
TESSERACT_CMD_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\Program Files\poppler-xx\Library\bin
CALIBRE_EBOOK_CONVERT_PATH=C:\Program Files\Calibre2\ebook-convert.exe

4. Ejecutar el servidor:

```bat
cd backend
python -m src.main
```

- El backend corre en `http://localhost:8000`.
- Endpoints relevantes:
  - `POST /text_to_audio` — streaming de audio a partir de texto
  - `POST /epub_to_audio` — convierte EPUB a audio (requiere dependencias)
  - `POST /pdf_to_epub` — convierte PDF a EPUB (requiere dependencias)

> CORS está abierto en desarrollo: el frontend puede llamar al backend sin bloqueos.

## Frontend (SvelteKit/Vite)

1. Instalar dependencias:

Con pnpm:
```bat
cd frontend
pnpm install
```

Con npm:
```bat
cd frontend
npm install
```

2. Configurar backend en frontend (.env):

En `frontend/.env`:

```plaintext
VITE_BACKEND_URL=http://localhost:8000
```

- En local, no uses sufijo `/api`.
- Al construir el frontend con Docker, esta variable se pasa como argumento de construcción (build arg) y/o variable de entorno; ver `frontend/Dockerfile`.

Alternativas sin archivo `.env` (solo para la sesión actual):

En CMD de Windows:
```bat
set VITE_BACKEND_URL=http://localhost:8000
```

En PowerShell:
```bat
$env:VITE_BACKEND_URL = "http://localhost:8000"
```

Después de setear la variable, corre el servidor de desarrollo (pnpm/npm dev).

3. Ejecutar el frontend:

Con pnpm (puerto 80 por defecto en `vite.config.ts`):
```bat
pnpm dev
```

Con pnpm (puerto personalizado, ej. 5173):
```bat
pnpm dev -- --port 5173
```

Con npm (puerto 80 por defecto):
```bat
npm run dev
```

Con npm (puerto personalizado, ej. 5173):
```bat
npm run dev -- --port 5173
```

4. Abrir en el navegador:

- Si puerto 80: `http://localhost/`
- Si puerto 5173: `http://localhost:5173/`

## Pruebas rápidas

- En el lector, usa la configuración de TTS y selecciona:
  - `gTTS` para pruebas rápidas (no requiere instalar Piper).
  - `piper` si tienes `piper.exe` y una voz configurada (ej. `es_MX-claude-high`).

- Endpoint sencillo para pruebas con texto:

```http
POST http://localhost:8000/text_to_audio?tts_provider=gtts&lang=es
Content-Type: application/json

{ "text": "Hola mundo" }
```

## Problemas comunes

- Puerto 80 requiere permisos en Windows: ejecuta `dev` con `--port 5173`.
- `piper` no funciona: verifica que `PIPER_EXECUTABLE_PATH` apunta a `piper.exe` o que `piper.exe` está en el PATH, y usa una voz válida.
- PDF/EPUB fallan: asegúrate de tener Tesseract, Poppler y Calibre instalados y configurados en `.env`.

## Estructura y referencias

- Backend: `backend/src/main.py` (FastAPI, endpoints y CORS)
- Frontend: `frontend/src/routes/reader/[bookId]/+page.svelte` (TTS y consumo del backend)
- Config Vite: `frontend/vite.config.ts` (puerto y host)