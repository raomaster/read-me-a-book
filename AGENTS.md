# Repository Guidelines

## Project Structure
- `backend/`: FastAPI API; entrypoint in `backend/src/main.py`, services in `backend/src/services`, TTS engines in `backend/src/engines`, utilities in `backend/src/utils`. Uploads land in `backend/uploads`, generated audio/text in `backend/outputs`.
- `frontend/`: SvelteKit app; routes in `frontend/src/routes`, shared UI and stores in `frontend/src/lib`, static assets in `frontend/static`.
- `caddy/`: Reverse-proxy config (`caddy/Caddyfile`).
- `docs/`: Screenshots and reference docs. Compose files and `env.example` live at repo root for local/Docker workflows.

## Build, Test, and Development Commands
- Docker stack: `docker-compose up -d` (use `--build` after backend/frontend changes). Frontend at `http://localhost`, API docs at `/api/docs`.
- Backend local: `pip install -r backend/requirements.txt` then `cd backend && python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000`.
- Frontend local: `cd frontend && pnpm install && pnpm dev` (prod build with `pnpm build`, preview with `pnpm preview`).
- Quality: `cd frontend && pnpm check` (types/svelte-check), `pnpm lint`, `pnpm format`. Run before opening a PR that touches the UI.

## Coding Style & Naming Conventions
- Python: Follow PEP8, prefer type hints and small service functions. Keep new endpoints thin and delegate to `services/`; share helpers in `utils/`. Store config in `config.py` or environment variables, not literals.
- Svelte/TS: Use `script lang="ts"`, PascalCase component files, camelCase variables/stores. Co-locate page-specific logic under `src/routes`; reusable UI in `src/lib/components`.
- Formatting: Frontend is enforced by Prettier/ESLint (`pnpm format`/`pnpm lint`). Python formatting is manual—match existing style and docstrings, avoid unused imports.

## Testing Guidelines
- Automated suites are minimal; rely on smoke checks:
  - Backend: after starting uvicorn, call `POST /text_to_audio` or `/pdf_to_epub` (see README curl examples) and confirm artifacts appear in `backend/outputs`.
  - Cloud Functions: run `python backend/src_gcloud/run_local.py` then POST to `http://localhost:8080` for a quick health check.
  - Frontend: `pnpm check && pnpm lint` must pass before merge.
- If you add tests, keep them near the code under `backend/src` or `frontend/src` and prefer deterministic fixtures (no remote services).

## Commit & Pull Request Guidelines
- Use conventional commits (`feat(scope): ...`, `fix: ...`, `chore: ...`); recent history shows this pattern (e.g., `feat(tts): add XTTS v2...`).
- PRs: include a short summary, test notes (`pnpm check`, curl commands run), and screenshots/GIFs for UI changes. Mention required external tools (Tesseract, Poppler, Piper) if setup-sensitive.
- Avoid committing large generated audio in `backend/outputs` or local env files (`.env`, `frontend/.env*`). Add to `.gitignore` if new artifacts are created.

## Configuration & Security Tips
- Start from `env.example`; never commit real secrets or API keys. Keep Tesseract/Poppler/Piper paths configurable via env vars or the placeholders in `backend/src/main.py`.
- When working on Windows, ensure the `bin` paths for external tools are set in PATH or in `main.py` constants before running conversions.
