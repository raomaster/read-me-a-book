# Guía de comandos gcloud (Windows/PowerShell)

Este documento recopila los comandos clave usados para:
- Habilitar servicios (APIs)
- Crear y configurar una Service Account (SA)
- Construir y publicar la imagen (Cloud Build)
- Desplegar el servicio (Cloud Run)
- Mapear dominio y diagnóstico

Usa PowerShell en Windows. Sustituye los placeholders según corresponda:
- `$PROJECT_ID` → ID de tu proyecto (p.ej. `my-project-123`)
- `$REGION` → región de Cloud Run (p.ej. `us-central1`)
- `$SERVICE` → nombre del servicio (p.ej. `frontend`)
- `$REPO` → nombre del repositorio en Artifact Registry (p.ej. `readmeabook`)
- `$DOMAIN` → dominio/subdominio que mapearás (p.ej. `frontend.tu-dominio.com`)
- `$BACKEND_URL` → URL del backend (p.ej. `https://backend-XXXX.us-central1.run.app`)

> Nota: En PowerShell, evita backticks o comillas “inteligentes”. Usa comillas simples `'` o dobles `"` normales. Cuando pases múltiples sustituciones, es más seguro definirlas en una variable y luego referenciarla.

---

## 1) Autenticación y selección de proyecto/región

```bash
gcloud auth login
```

```bash
gcloud auth application-default login
```

```bash
$PROJECT_ID = "tu-project-id"
```

```bash
$REGION = "us-central1"
```

```bash
gcloud config set project $PROJECT_ID
```

```bash
gcloud config set run/region $REGION
```

---

## 2) Habilitar APIs necesarias

```bash
gcloud services enable run.googleapis.com
```

```bash
gcloud services enable cloudbuild.googleapis.com
```

```bash
gcloud services enable artifactregistry.googleapis.com
```

```bash
gcloud services enable iam.googleapis.com
```

---

## 3) (Opcional pero recomendado) Crear repositorio de Artifact Registry para Docker

```bash
$REPO = "readmeabook"
```

```bash
gcloud artifacts repositories create $REPO --repository-format=docker --location=$REGION --description="Repo Docker para frontend"
```

---

## 4) Service Account para Cloud Run (ejecución del contenedor)

```bash
gcloud iam service-accounts create cloud-run-sa --display-name "Cloud Run SA"
```

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID --member "serviceAccount:cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" --role "roles/artifactregistry.reader"
```

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID --member "serviceAccount:cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" --role "roles/logging.logWriter"
```

> Si usas Container Registry (GCR) en lugar de Artifact Registry, añade también:
```bash
gcloud projects add-iam-policy-binding $PROJECT_ID --member "serviceAccount:cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com" --role "roles/storage.objectViewer"
```

---

## 5) Build de la imagen del frontend con Cloud Build (usando cloudbuild.yaml)

Ir al directorio del frontend antes de ejecutar:

```bash
Set-Location c:\Users\raoma\Code\read-me-a-book\frontend
```

Define sustituciones (PowerShell-safe):

```bash
$BACKEND_URL = "https://backend-XXXX.us-central1.run.app"
```

```bash
$subs = "_BACKEND_URL=$BACKEND_URL,_PUBLIC_TTS_MODE=gcloud"
```

```bash
gcloud builds submit --project $PROJECT_ID --substitutions $subs
```

> Alternativa si prefieres escribirlas inline (ojo a comillas y sin espacios alrededor de `=`):
```bash
gcloud builds submit --project $PROJECT_ID --substitutions "_BACKEND_URL=https://backend-XXXX.us-central1.run.app,_PUBLIC_TTS_MODE=gcloud"
```

---

## 6) (Opcional) Build directo etiquetando la imagen en Artifact Registry (sin cloudbuild.yaml)

> Solo si NO usas `cloudbuild.yaml` y quieres un build rápido con `--tag`:

```bash
$IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest"
```

```bash
gcloud builds submit --project $PROJECT_ID --tag $IMAGE
```

---

## 7) Despliegue en Cloud Run

> Si has usado `cloudbuild.yaml`, revisa cuál es la imagen que se produce y sustitúyela en `$IMAGE`. Si seguiste la opción “Build directo”, ya tienes `$IMAGE`.

```bash
$SERVICE = "frontend"
```

```bash
$IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest"
```

```bash
gcloud run deploy $SERVICE --image $IMAGE --region $REGION --allow-unauthenticated --service-account "cloud-run-sa@$PROJECT_ID.iam.gserviceaccount.com"
```

> Hacer público el servicio (invocación sin autenticación; si no usaste `--allow-unauthenticated`):
```bash
gcloud run services add-iam-policy-binding $SERVICE --member="allUsers" --role="roles/run.invoker" --region $REGION
```

---

## 8) Diagnóstico (servicio, revisiones y logs)

```bash
gcloud run services describe $SERVICE --region $REGION
```

```bash
gcloud run revisions list --region $REGION --service $SERVICE
```

```bash
gcloud run logs read $SERVICE --region $REGION --limit 100
```

---

## 9) Dominio personalizado (Cloud Run Domain Mapping)

> Crea el mapeo de dominio y obtén los registros DNS que debes configurar en Cloudflare:

```bash
$DOMAIN = "frontend.tu-dominio.com"
```

```bash
gcloud run domain-mappings create --service $SERVICE --domain $DOMAIN --region $REGION
```

```bash
gcloud run domain-mappings describe --domain $DOMAIN --region $REGION
```

> Para eliminar un mapeo:
```bash
gcloud run domain-mappings delete --domain $DOMAIN --region $REGION
```

---

## 10) Limpieza / utilidades

```bash
gcloud run services list --region $REGION
```

```bash
gcloud run services delete $SERVICE --region $REGION
```

```bash
gcloud artifacts repositories list --location $REGION
```

---

## Notas importantes

- En Cloud Run, el contenedor debe escuchar en el puerto especificado por la variable de entorno `PORT`. Asegúrate de que tu `Dockerfile` use algo como:
  - `CMD ["sh", "-c", "pnpm preview --host 0.0.0.0 --port ${PORT:-80}"]`
- En Vite, si se muestra "Blocked request. This host is not allowed.", agrega el host de Cloud Run a `server.allowedHosts` y `preview.allowedHosts` en `vite.config.ts`.
- Evita el uso de backticks o espacios erróneos en `--substitutions`. Usa variables en PowerShell para mayor seguridad.

---

## Seguridad al publicar en GitHub

- Mantén este archivo sin valores reales: usa siempre placeholders como `$PROJECT_ID`, `$REGION`, `$SERVICE`, `$BACKEND_URL`, `$REPO` y `$DOMAIN`.
- NO subas llaves de Service Account al repositorio:
  - Prefiere usar `gcloud auth login` y `gcloud auth application-default login`.
  - Si necesitas usar una key temporal, guárdala fuera del repo y usa secretos del sistema de CI/CD (GitHub Actions, Cloud Build) para inyectarla.
- Principio de mínimo privilegio:
  - Da a tu Service Account solo los roles necesarios (`roles/artifactregistry.reader`, `roles/run.invoker`, `roles/logging.logWriter`, etc.).
- Variables locales en PowerShell para no exponer valores:
  - Define los valores en tu sesión local:
    ```bash
    $PROJECT_ID = "tu-project-id"
    $REGION = "us-central1"
    $SERVICE = "frontend"
    $REPO = "readmeabook"
    $BACKEND_URL = "https://backend-XXXX.us-central1.run.app"
    $DOMAIN = "frontend.tu-dominio.com"
    ```
  - Usa las variables en los comandos en lugar de escribir valores literales.
- Sustituciones de Cloud Build:
  - Evita comillas curvas y backticks.
  - Construye una variable con todas las sustituciones antes de ejecutar el submit:
    ```bash
    $subs = "_BACKEND_URL=$BACKEND_URL,_PUBLIC_TTS_MODE=gcloud"
    gcloud builds submit --project $PROJECT_ID --substitutions $subs
    ```
- Secretos:
  - No incluyas tokens o claves directamente en el Dockerfile ni en este .md.
  - Usa Secret Manager y variables de entorno en Cloud Run si necesitas secretos (configúralos fuera del repo).
- Dominios:
  - No publiques dominios reales si el repo es público. Usa `$DOMAIN` como placeholder.
  - Configura los DNS en Cloudflare de forma privada y no subas capturas con datos sensibles.


## Decisión: Frontend público detrás de Cloudflare

El servicio de Cloud Run del frontend debe quedar público para que Cloudflare pueda hacer proxy de la aplicación y los usuarios puedan acceder. La protección de datos se realizará en el backend mediante verificación de ID Token (Firebase Auth) y reglas de autorización.

Pasos en la consola (UI en español):
1) Cloud Run → Services → selecciona el servicio "frontend" → pestaña "Seguridad".
2) En "Autenticación", selecciona "Permite el acceso público".
3) Si aparece la advertencia "Este servicio es de acceso público porque se le otorgó permiso a 'allUsers'", confirma con "Permite el acceso público" para dejar el estado consistente.
4) Guarda/Despliega si la UI lo solicita.

Roles implicados (IDs):
- Invocador de Cloud Run → roles/run.invoker (se otorga automáticamente a allUsers al dejarlo público)
- Escritor de registros → roles/logging.logWriter (debe estar en la SA de ejecución)
- Visualizador de objetos → roles/storage.objectViewer (debe estar en la SA de ejecución si usas Container Registry gcr.io)

Verificación opcional por CLI:
- Comprobar que el servicio es público (que allUsers tiene run.invoker):
  - gcloud run services get-iam-policy FRONTEND_SERVICE --region REGION --project PROJECT_ID
- Forzar el acceso público si fuera necesario:
  - gcloud run services add-iam-policy-binding FRONTEND_SERVICE --member=allUsers --role=roles/run.invoker --region REGION --project PROJECT_ID

Notas para Cloudflare:
- Usa el modo proxy ("nube naranja") apuntando al dominio de Cloud Run (xxx.run.app) o a tu mapeo de dominio si lo configuras.
- Mantén el frontend público; el backend validará el ID Token y controlará las rutas protegidas.
- Si ves "Blocked request" desde Vite/SvelteKit, añade el dominio de Cloud Run y tu dominio de Cloudflare a la lista de hosts permitidos en la configuración del frontend (vite.config.ts).

Checklist de seguridad (resumen):
- La SA de ejecución del servicio frontend debe tener: roles/logging.logWriter y roles/storage.objectViewer.
- No publiques PROJECT_ID ni dominios reales en este .md; usa placeholders (PROJECT_ID, REGION, FRONTEND_SERVICE).
- La protección de datos sensibles se realiza en el backend con verificación de ID Token y autorización por roles/claims, no en el frontend.

## Configurar acceso público o autenticado en Cloud Run (UI en español)

Esta sección explica cómo hacer que un servicio de Cloud Run sea público (sin autenticación) o privado (requiere IAM). Úsalo para el servicio "frontend".

- Roles mencionados por ID (funcionan en cualquier idioma):
  - Invocador de Cloud Run → roles/run.invoker
  - Escritor de registros → roles/logging.logWriter
  - Visualizador de objetos → roles/storage.objectViewer

Opción A: Dejar el servicio público (recomendado para el frontend)
1) Cloud Run → Services → selecciona tu servicio (frontend) → pestaña "Seguridad".
2) En "Autenticación", selecciona "Permite el acceso público".
3) Si ves el aviso "Este servicio es de acceso público porque se le otorgó permiso a 'allUsers'":
   - Pulsa "Permite el acceso público" para confirmar el modo público.
4) Guarda/Despliega si la UI te lo solicita.

Opción B: Dejar el servicio privado (requiere autenticación IAM)
1) Cloud Run → Services → frontend → "Seguridad".
2) En "Autenticación", selecciona "Necesita autenticación (IAM)".
3) Pulsa "Quitar acceso para allUsers" para eliminar el acceso público.
4) Ve a IAM del proyecto y otorga el rol "roles/run.invoker" solo a los principales que deban invocar el servicio (por ejemplo, tu usuario o un proxy/IAP si usas autenticación de usuario final).
   - Nota: Si activas IAM sin IAP ni un proxy, los visitantes recibirán 401/403 al acceder.

Verificación
- En la página del servicio → "Seguridad":
  - Público: debe quedar "Permite el acceso público" sin avisos de allUsers inconsistentes.
  - Privado: debe quedar "Necesita autenticación (IAM)" y sin la advertencia de "allUsers".
- Prueba la URL:
  - Público: accesible para cualquiera.
  - Privado: requiere credenciales con roles/run.invoker (por ejemplo, usuarios de tu organización o cuentas de servicio).
- Revisa que la SA de ejecución esté configurada correctamente (cloud-run-frontend-sa@PROJECT_ID.iam.gserviceaccount.com) y que tenga:
  - roles/logging.logWriter (Escritor de registros)
  - roles/storage.objectViewer (Visualizador de objetos)

Notas
- Para sitios públicos (frontend), usa "Permite el acceso público" y protege datos en el backend con verificación de ID Token.
- Si la app muestra "Blocked request", agrega el host de Cloud Run a los permitidos en tu configuración de Vite. Revisa vite.config.ts y añade el dominio *.run.app correspondiente a tu servicio en allowedHosts.

---

## Asignar roles a la Cuenta de Servicio desde la consola (UI en español)

Esta sección explica cómo otorgar a una Cuenta de Servicio (SA) los permisos mínimos necesarios para que el servicio de Cloud Run (frontend) escriba registros y lea la imagen en Container Registry (gcr.io). En la interfaz en español, los roles aparecen con estos nombres:

- Escritor de registros → ID: roles/logging.logWriter (categoría: Cloud Logging)
- Visualizador de objetos → ID: roles/storage.objectViewer (categoría: Storage)
- Nota: si migras a Artifact Registry (us-xxx-docker.pkg.dev/...), el rol equivalente es Lector de Artifact Registry → ID: roles/artifactregistry.reader

Pasos en la consola (IAM del proyecto):
1) Ve al menú "IAM y administración" → "IAM".
2) Pulsa el botón "Otorgar acceso" (Agregar principal).
3) En "Nuevos principales", pega el correo de tu SA:
   - cloud-run-frontend-sa@PROJECT_ID.iam.gserviceaccount.com
   - Usa PROJECT_ID como placeholder para tu proyecto; no publiques nombres reales en el repositorio.
4) En "Seleccionar un rol", busca y selecciona:
   - "Escritor de registros" (roles/logging.logWriter).
5) Pulsa "Añadir otro rol" y selecciona:
   - "Visualizador de objetos" (roles/storage.objectViewer).
6) Guarda los cambios.

Sugerencias si no encuentras los roles:
- Pega directamente el ID del rol en el filtro: "roles/logging.logWriter" y "roles/storage.objectViewer".
- Desplázate por las categorías hasta "Cloud Logging" y "Storage".
- Verifica que estás en el proyecto correcto y que tu usuario tiene permisos para asignar IAM (Propietario o Administrador de IAM).

Vincular la SA al servicio de Cloud Run:
1) Ve a "Cloud Run" → "Services" → selecciona tu servicio frontend.
2) Pulsa "Edit & deploy new revision".
3) En "Service account" elige: cloud-run-frontend-sa@PROJECT_ID.iam.gserviceaccount.com.
4) Despliega la nueva revisión.

Verificación rápida:
- En "IAM", la SA debe mostrar los roles "Escritor de registros" y "Visualizador de objetos".
- En la página del servicio de Cloud Run, sección "Security", debe figurar esa SA como identidad de ejecución.
- En Cloud Logging verás registros de la aplicación una vez desplegado.

Buenas prácticas de seguridad:
- Mantén PROJECT_ID y otros datos sensibles como placeholders en este archivo (.md) para evitar filtrar información en GitHub.
- No publiques correos reales de cuentas de servicio; usa el formato con PROJECT_ID como guía.
