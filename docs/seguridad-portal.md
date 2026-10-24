# Análisis de seguridad · Portal del estudiante

Alcance: `portal/src/App.jsx`, `portal/nginx.conf` y el contrato
del portal con la API (`GET /cursos`, `POST /asignaciones`).

## 1. Tríada CIA

| Propiedad | Qué protege en el portal | Cómo se cubre hoy | Brecha del prototipo |
|---|---|---|---|
| **Confidencialidad** | El carné del estudiante y sus asignaciones | El portal solo muestra el texto `detalle` que manda la API, sin datos de otros estudiantes. | Todo viaja por HTTP sin cifrar (no hay TLS). El carné puede quedar en los logs. |
| **Integridad** | Que los cupos nunca queden negativos y nadie quede asignado dos veces | La base de datos lo garantiza con `CHECK (cupos >= 0)` y `UNIQUE (estudiante_id, curso_id)`. El modo atómico evita la condición de carrera. El portal valida el formato del carné, pero eso solo mejora la experiencia: la API debe volver a validarlo. | No hay autenticación, así que cualquiera puede asignar un curso con el carné de otra persona. |
| **Disponibilidad** | Que el portal siga respondiendo durante la avalancha de inscripción | Los botones se desactivan mientras se envía, lo que evita dobles clics y peticiones duplicadas. Si la API no responde, el portal muestra un aviso con "Reintentar" en vez de quedarse en blanco. La API corta la espera a los `POOL_TIMEOUT_S` segundos y responde 503. | No hay límite de peticiones por cliente, ni en Nginx ni en la API. Un solo script puede llenar el pool de 10 conexiones (lo que demuestran las pruebas k6). |

## 2. Riesgos OWASP Top 10 (2025)

### A01 · Control de acceso roto (riesgo alto)

- `nginx.conf` reenvía *todo* lo que empieza con `/api/` a la API, también
  `/api/admin/flags` y `/api/admin/reiniciar`. Desde el portal público, cualquiera puede
  cambiar el modo de asignación o borrar las asignaciones del curso. Además, el carné no se
  autentica, así que cualquiera puede inscribir a otra persona.
- **Mitigación propuesta:** bloquear las rutas de administración en el proxy del portal (en la demo se usa en `localhost:8000/docs`, sin pasar por el portal):

  ```nginx
  location /api/admin/ { return 403; }
  ```

  En un sistema real, el estudiante se autenticaría con el inicio de sesión institucional y la API tomaría el carné del token, no del cuerpo de la petición.

### A05 · Inyección (riesgo bajo)

- El carné es texto libre que llega a la base de datos.
- **Cómo se cubre:** el portal acepta solo de 7 a 10 dígitos (`FORMATO_CARNE`) y React escapa
  la salida, lo que evita XSS al mostrar `detalle`. La defensa real está en la API: debe usar
  consultas parametrizadas de psycopg (nunca armar el SQL con f-strings) y validar
  `estudiante_id` con Pydantic.

### A02 · Configuración de seguridad incorrecta (riesgo medio)

- Nginx corre con la configuración por defecto. Muestra su versión
  (`server_tokens`), no envía cabeceras de seguridad y no limita la tasa de peticiones.
- **Mitigación propuesta:**

  ```nginx
  server_tokens off;
  add_header X-Content-Type-Options nosniff;
  add_header X-Frame-Options DENY;
  add_header Content-Security-Policy "default-src 'self'";
  # y en el bloque http: limit_req_zone $binary_remote_addr zone=asig:10m rate=5r/s;
  ```

  Nota: el límite de tasa afectaría las pruebas k6 si pasan por el portal. 

