# Instrumentación de la API (R3)

Alcance: `api/app/telemetria.py`, los spans de `api/app/main.py` y `api/app/asignacion.py`,
`infra/otel-collector.yaml`, `infra/tempo.yaml`, `infra/loki.yaml` e
`infra/grafana/provisioning/datasources/datasources.yml`. Cubre RNF1 y HU2: desde una petición
lenta se llega a su traza y a sus logs.

## 1. Las tres señales

La API usa el SDK de OpenTelemetry y manda las tres señales por OTLP (gRPC, puerto 4317) al
OpenTelemetry Collector. El Collector las reparte a un almacén por señal y Grafana lee de los
tres.

```
API (FastAPI) ──OTLP──► OTel Collector ──► Tempo       (trazas)
                                       ├─► Prometheus  (métricas, lee el puerto 8889 del Collector)
                                       └─► Loki        (logs)
                                                 ▲
                                    Grafana lee de los tres
```

| Señal | Qué se envía | Dónde se configura |
|---|---|---|
| Trazas | Un span por petición HTTP (automático) y los spans propios de la asignación (sección 2) | `telemetria.py` (`TracerProvider` + `OTLPSpanExporter`), `main.py` (`FastAPIInstrumentor`), pipeline `traces` del Collector, `infra/tempo.yaml` |
| Métricas | `asignaciones_total{sli, status, modo}`, histograma `asignacion_duracion_seconds` (buckets alrededor de 2 s), gauges `db_pool_conexiones{estado="en_uso\|esperando"}` y `db_pool_tamano`. Se exportan cada 5 s | `telemetria.py` (`MeterProvider`, `View` de buckets, `registrar_asignacion`, `observar_pool`), pipeline `metrics` del Collector (exportador `prometheus` en `:8889`) |
| Logs | Un log JSON por asignación con `trace_id` y `span_id`, más los errores y el cambio del feature flag. Salen a stdout (`docker compose logs api`) y por OTLP a Loki | `telemetria.py` (`JsonFormatter`, `LoggerProvider` + `LoggingHandler`), pipeline `logs` del Collector, `infra/loki.yaml` (`allow_structured_metadata`) |

El nombre del servicio (`api-asignaciones`) y la dirección del Collector vienen de
`OTEL_SERVICE_NAME` y `OTEL_EXPORTER_OTLP_ENDPOINT` en `docker-compose.yml`.

## 2. Spans de la asignación

```
POST /asignaciones                      (FastAPIInstrumentor: método, ruta, código HTTP)
├── db.pool.acquire                     espera de una conexión libre del pool
├── db.query  db.operacion=select_for_update   lee el curso y toma el candado de la fila (modo inicial)
├── validaciones                        reglas de negocio simuladas (VALIDACIONES_S, 50 ms)
└── db.query  db.operacion=update_insert       descuenta el cupo e inserta la asignación (modo inicial)
```

En modo atómico el orden cambia: `validaciones` va primero, sin conexión ni candado, y después
`db.pool.acquire` y un solo `db.query` con `db.operacion=update_atomico`.

| Span | Qué mide |
|---|---|
| `POST /asignaciones` | Tiempo total de la petición. Lleva `asignacion.curso_id` y `asignacion.modo` |
| `db.pool.acquire` | Cuánto espera la petición a que se libere una de las `POOL_SIZE` conexiones |
| `validaciones` | El costo de las validaciones; muestra si se hacen dentro o fuera del candado |
| `db.query` | El trabajo en PostgreSQL, incluida la espera del candado `FOR UPDATE` |

## 3. Correlación traza ↔ log

- `JsonFormatter` (`telemetria.py`) toma el span activo y agrega `trace_id` (32 hex) y `span_id`
  (16 hex) a cada log. El log `asignacion procesada` se escribe dentro del span
  `POST /asignaciones`, así que lleva el mismo `trace_id` que la traza.
- `LoggingHandler` envía el mismo log por OTLP. Loki guarda el `trace_id` como metadato
  estructurado del registro.
- `datasources.yml`, en Tempo, `tracesToLogsV2` con `filterByTraceID: true`: activa el botón
  **Logs for this span**, que busca en Loki los logs con ese `trace_id` (un minuto antes y después
  del span).
- `datasources.yml`, en Loki, `derivedFields` sobre `trace_id`: en cada log aparece un enlace que
  abre la traza en Tempo.

## 4. Revisión de datos sensibles

Objetivo: que no se registre información personal además del carné.

| Dónde | Qué se registra | Conclusión |
|---|---|---|
| `main.py`, span de `asignar()` | `asignacion.curso_id`, `asignacion.modo` | No lleva el carné. Correcto |
| `main.py`, log `asignacion procesada` | `curso_id`, `estudiante_id` (carné), `status`, `sli`, `modo`, `duracion_ms` | El carné es el único dato personal y es el permitido: hace falta para atender un reclamo de un estudiante |
| `asignacion.py`, spans `db.query` | `db.operacion` (tipo de consulta) | No guarda el texto SQL ni los valores de los parámetros. Correcto |
| `telemetria.py`, métricas | `sli`, `status`, `modo`, `estado` | Sin datos personales. Además, el carné nunca debe ir como atributo de una métrica: cada valor distinto crearía una serie nueva en Prometheus |
| `FastAPIInstrumentor` (automático) | Método, ruta, URL, código HTTP, IP de origen | No guarda cuerpos de petición ni cabeceras. El carné va en el cuerpo del POST, así que no aparece. La IP de origen es la del contenedor de Nginx del portal, no la del estudiante. No se debe activar la captura de cabeceras (`OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_*`) |
| `main.py`, `log.exception(...)` en errores 500 | Mensaje y traza de la excepción | La traza de Python no incluye variables locales, y los errores de psycopg no incluyen la contraseña. `DATABASE_URL` solo vive en variables de entorno y no se registra |
| `main.py`, log `feature flag cambiado` | `modo_atomico` | Sin datos personales |

Conclusión: la instrumentación cumple. No hizo falta cambiar código. Para confirmarlo en vivo:
hacer una asignación desde el portal y, en Grafana → **Explore** → **Loki**, buscar
`{service_name="api-asignaciones"}`, abrir un log y revisar sus campos.

Riesgo que queda fuera de la instrumentación: el carné se guarda en texto claro en Loki y
cualquiera con acceso a Grafana lo puede ver (en el prototipo Grafana entra sin usuario). En
producción habría que proteger Grafana o seudonimizar el carné en los logs.

## 5. Cómo encontrar la causa de una traza lenta

Pasos en el README, sección 8, *Prueba 3*, *Paso B*. Con la traza abierta:

1. La petición tardó más de 2 s, por eso incumple el SLO y cuenta como `sli="mala"`.
2. Casi todo el tiempo está en `db.pool.acquire`: la petición espera una conexión libre porque
   las 10 del pool están ocupadas.
3. Las conexiones están ocupadas porque, en el modo inicial, cada solicitud toma el candado del
   curso (`db.query select_for_update`) y hace las `validaciones` (50 ms) con el candado tomado.
   Con 200 peticiones por segundo al mismo curso, todas quedan en fila. El tiempo no está en el
   servidor web ni en la red.
4. Con **Logs for this span** se ve el log de esa misma petición (mismo `trace_id`), con su
   `status` y `duracion_ms`.
5. En modo atómico las validaciones se hacen antes de tomar la conexión y el
   `UPDATE ... WHERE cupos > 0` suelta el candado al instante. Por eso `db.pool.acquire` casi
   desaparece y el p95 baja a unos 0.1 s.
