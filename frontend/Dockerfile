# Build stage
FROM node:lts AS build
ENV CI=true
WORKDIR /app
COPY . /app

# Pasar la variable de entorno al build
ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

# NUEVO: agregar PUBLIC_TTS_MODE para el build
ARG PUBLIC_TTS_MODE
ENV PUBLIC_TTS_MODE=${PUBLIC_TTS_MODE}

# NUEVO: credenciales públicas de Firebase
ARG PUBLIC_FIREBASE_API_KEY
ENV PUBLIC_FIREBASE_API_KEY=${PUBLIC_FIREBASE_API_KEY}
ARG PUBLIC_FIREBASE_AUTH_DOMAIN
ENV PUBLIC_FIREBASE_AUTH_DOMAIN=${PUBLIC_FIREBASE_AUTH_DOMAIN}
ARG PUBLIC_FIREBASE_PROJECT_ID
ENV PUBLIC_FIREBASE_PROJECT_ID=${PUBLIC_FIREBASE_PROJECT_ID}
ARG PUBLIC_FIREBASE_APP_ID
ENV PUBLIC_FIREBASE_APP_ID=${PUBLIC_FIREBASE_APP_ID}

RUN corepack enable && pnpm install --frozen-lockfile
RUN pnpm run build   # generates /build with the PWA assets

# Debug: listar contenido de /app
RUN echo "=== list /app ===" && ls -R /app

# Production
FROM node:lts-slim AS runner
WORKDIR /app
RUN corepack enable
COPY --from=build /app ./

# Exponer el puerto (Cloud Run usa $PORT)
EXPOSE 80

# Escucha en $PORT (Cloud Run) o 80 por defecto
CMD ["sh", "-c", "pnpm preview --host 0.0.0.0 --port ${PORT:-80}"]