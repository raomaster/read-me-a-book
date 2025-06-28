# Read Me a Book - Docker Setup con SSL

Este proyecto incluye un proxy reverso con Caddy que proporciona SSL automático y soporte para desarrollo con hot reload.

## Configuración

### 1. Dominio
Asegúrate de que tu dominio `leeme.mooo.com` apunte a tu servidor.

### 2. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto:

```bash
# Para producción (con SSL)
BACKEND_URL=https://leeme.mooo.com/api

# Para desarrollo local (sin SSL)
# BACKEND_URL=http://localhost:8000
```

## Uso

### Desarrollo (con hot reload)
```bash
# Iniciar en modo desarrollo con hot reload
docker compose up --watch

# Acceder directamente al servidor de desarrollo
# http://localhost:5173
```

### Producción
```bash
# Iniciar en modo producción (sin override)
docker compose -f docker-compose.yml up -d

# O simplemente (sin archivo override presente)
docker compose up -d
```

### Ver logs
```bash
# Todos los servicios
docker compose logs -f

# Solo un servicio
docker compose logs -f caddy
docker compose logs -f backend
docker compose logs -f frontend
```

### Detener servicios
```bash
docker compose down
```

### Reconstruir después de cambios
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Estructura de Archivos

```
read-me-a-book/
├── docker-compose.yml          # Configuración base (producción)
├── docker-compose.override.yml # Configuración desarrollo (hot reload)
├── caddy/
│   └── Caddyfile              # Configuración del proxy reverso
├── frontend/                  # Aplicación SvelteKit
└── backend/                   # API Python
```

## URLs de Acceso

### Producción
- **Frontend**: https://leeme.mooo.com
- **Backend API**: https://leeme.mooo.com/api/
  - `/api/text_to_audio` - Convertir texto a audio
  - `/api/pdf_to_epub` - Convertir PDF a EPUB
  - `/api/epub_to_audio` - Convertir EPUB a audio

### Desarrollo
- **Frontend (dev server)**: http://localhost:5173
- **Backend API**: http://localhost:8000

## Configuración de Desarrollo vs Producción

### Desarrollo (`docker-compose.override.yml`)
- Frontend ejecuta `pnpm dev` con hot reload
- Puerto 5173 expuesto para acceso directo
- Watch mode activado para sincronización de archivos
- Variables de entorno de desarrollo

### Producción (`docker-compose.yml`)
- Frontend sirve archivos estáticos optimizados
- Solo Caddy expone puertos al host (80, 443)
- Configuración optimizada para rendimiento
- SSL automático con Let's Encrypt

## Seguridad

Caddy incluye automáticamente:
- SSL/TLS con Let's Encrypt
- Headers de seguridad
- Redirección automática HTTP → HTTPS

## Troubleshooting

### Verificar que los servicios funcionen
```bash
# Verificar Caddy
docker compose exec caddy caddy version

# Verificar que el backend responde
curl https://leeme.mooo.com/api/text_to_audio

# Verificar que el frontend responde
curl https://leeme.mooo.com
```

### Problemas de puertos
Si obtienes error "port is already allocated":
```bash
# Verificar qué está usando el puerto 80
netstat -aon | findstr :80

# Detener todos los contenedores
docker compose down

# Reiniciar Docker Desktop si es necesario
```

### Hot reload no funciona
```bash
# Verificar que el override está presente
ls docker-compose.override.yml

# Reconstruir con watch mode
docker compose down
docker compose up --watch
```