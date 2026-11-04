# Análisis de seguridad · API e infraestructura

Entregable 4 del enunciado. Complementa `docs/seguridad-portal.md` (portal) con la API, la base
de datos y el stack de observabilidad. Alcance: el prototipo tal como lo levanta
`docker-compose.yml`. Quedan fuera, como dice el hito 1, la autenticación real y los pagos.

## 1. Tríada CIA aplicada al sistema completo

| Propiedad | Activo | Control que ya existe | Brecha aceptada en el prototipo |
|---|---|---|---|
| **Confidencialidad** | Carné y asignaciones; webhook de Discord | El webhook vive fuera del repositorio (`.gitignore`, verificado con `git check-ignore`). Los logs y spans no guardan nombre ni datos personales, solo el carné (revisado en `docs/instrumentacion.md`). La API responde mensajes genéricos (`Error interno`), sin trazas de pila | Sin TLS; Grafana con acceso anónimo; el carné aparece en los logs de Loki |
| **Integridad** | Cupos y asignaciones | `CHECK (cupos >= 0)` y `UNIQUE (estudiante_id, curso_id)` en PostgreSQL; `UPDATE … WHERE cupos > 0` atómico; validación con Pydantic (carné con patrón, curso entero positivo); consultas parametrizadas en todo `asignacion.py`; probado con RF2 (500 solicitudes) | Sin autenticación: se puede asignar con el carné de otro |
| **Disponibilidad** | Servicio de asignación en la ventana crítica | SLO de 95% con 4 alertas; pool con `POOL_TIMEOUT_S` que responde 503 en vez de colgarse; corrección atómica activable sin reiniciar | Sin límite de peticiones por cliente; una sola réplica de la API |

## 2. Riesgos OWASP Top 10 (2025) en la API y la infraestructura

### A01 · Control de acceso roto (alto → mitigado en el portal)

- **Riesgo:** `/admin/flags` y `/admin/reiniciar` cambian el comportamiento y borran asignaciones
  sin autenticación.
- **Mitigación aplicada:** `portal/nginx.conf` responde **403** a `/api/admin/`, así que desde el
  portal público no se alcanzan. Se demuestra en vivo (bloque 1 del guion).
- **Riesgo residual:** el puerto 8000 de la API sigue publicado en `localhost` para operar la
  demo. En producción la API no se publicaría y `/admin` exigiría un token de operador.

### A02 · Configuración de seguridad incorrecta (medio)

- **Riesgo:** Grafana con `GF_AUTH_ANONYMOUS_ORG_ROLE: Admin`, PostgreSQL publicado en el puerto
  5432 con la contraseña por defecto `app`, Nginx mostrando su versión.
- **Mitigación aplicada:** `server_tokens off` y cabeceras `X-Content-Type-Options`,
  `X-Frame-Options` y `Referrer-Policy` en `nginx.conf`; la contraseña se cambia en `.env`
  (`POSTGRES_PASSWORD`) sin tocar el código.
- **Mitigación propuesta para producción:** Grafana con rol `Viewer` o inicio de sesión, quitar
  `ports` de PostgreSQL, Loki y el Collector, y secretos en un gestor (no en `.env`).

### A09 · Fallas en el registro y las alertas de seguridad (cubierto por diseño)

- **Riesgo:** que un abuso (por ejemplo un script que satura el pool) pase sin que nadie se entere,
  que es justo el problema del caso.
- **Cómo se cubre:** cada asignación deja log JSON con `trace_id`, el cambio del feature flag queda
  registrado como `WARNING` (`feature flag cambiado`), y la saturación dispara alertas a Discord en
  ≤ 60 s. Es la parte de seguridad que el enfoque SRE resuelve de forma natural.

### A05 · Inyección (bajo)

- **Cómo se cubre:** todas las consultas usan parámetros de psycopg (`%s`), nunca f-strings; el
  carné se valida en la API con `^[A-Za-z0-9-]{1,20}$`. La prueba
  `test_422_carne_invalido` intenta `1102124;DROP` y la API responde 422.

## 3. Resumen de mitigaciones

| Riesgo | Estado | Evidencia |
|---|---|---|
| Admin expuesto desde el portal | ✅ Mitigado | `nginx.conf`, 403 en la demo |
| Cabeceras y versión de Nginx | ✅ Mitigado | `nginx.conf` |
| Inyección SQL | ✅ Mitigado | Consultas parametrizadas, pytest 422 |
| Webhook en el repositorio | ✅ Mitigado | `.gitignore` |
| Saturación sin aviso | ✅ Mitigado | SLO + 4 alertas + Discord |
| Sin autenticación | ⚠️ Fuera de alcance | Hito 1, alcance |
| Sin límite de tasa | ⚠️ Aceptado | Afectaría las pruebas de k6; en producción, `limit_req` en Nginx |
| Grafana anónimo y puertos publicados | ⚠️ Aceptado para la demo | Ver A02 |
