# Build stage
FROM node:lts AS build
ENV CI=true
WORKDIR /app
COPY . /app

RUN corepack enable && pnpm install --frozen-lockfile
RUN pnpm run build   # generates /build with the PWA assets

# Debug: listar contenido de /app
RUN echo "=== list /app ===" && ls -R /app

# Production
FROM node:lts-slim AS runner
WORKDIR /app

# Habilita corepack para pnpm
RUN corepack enable

# Trae todo de build: código compilado, node_modules, assets, SW…
COPY --from=build /app ./

# Exponer el puerto usado por preview (según vite.config.js: 4173)
EXPOSE 80

# Arranca el servidor preview de Vite en modo no interactivo
CMD ["pnpm", "preview", "--host"]