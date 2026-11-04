# Plan de calidad · Sistema de Asignaciones (SRE)

Entregable 3 del enunciado: atributos de calidad de ISO/IEC 25010 priorizados para el caso y
cómo se prueban. Se eligieron tres, en este orden, porque el problema del hito 1 es exactamente
una falla de ellos durante los primeros 15 minutos del semestre.

| Prioridad | Característica (ISO/IEC 25010:2023) | Subcaracterísticas | Por qué importa en el caso |
|---|---|---|---|
| 1 | **Eficiencia de desempeño** | Comportamiento temporal, utilización de recursos, capacidad | Miles de estudiantes en 15 minutos sobre un curso de 30 cupos; el pool de conexiones es el recurso que se agota |
| 2 | **Fiabilidad** | Ausencia de fallos (*faultlessness*), disponibilidad, tolerancia a fallos | El estudiante no puede perder su cupo ni recibir un error genérico; RF2 exige integridad bajo concurrencia |
| 3 | **Mantenibilidad** | Modularidad, capacidad de ser probado (*testability*), capacidad de ser analizado | TI debe poder encontrar en qué capa falla y corregir sin rediseñar; la corrección es un cambio pequeño detrás de un feature flag |

## 1. Eficiencia de desempeño

| Métrica | Meta | Cómo se mide | Prueba |
|---|---|---|---|
| Latencia p95 de `POST /asignaciones` | < 2 s | Histograma `asignacion_duracion_seconds` en Prometheus; regla `sli:asignacion:latencia_p95_1m` | `load-tests/avalancha.js` (200 peticiones/s), umbral de k6 `p(95)<2000` |
| Saturación del pool | En uso < `POOL_SIZE` y sin peticiones esperando de forma sostenida | Gauges `db_pool_conexiones{estado}` y `db_pool_tamano` | Avalancha + alerta predictiva `PoolConexionesPorAgotarse` |
| Capacidad | 200 peticiones/s sostenidas sobre el curso caliente sin romper el SLO | k6 + panel *Tráfico por respuesta* | Avalancha con `modo_atomico` activo |

**Resultados medidos** (avalancha de 200 peticiones/s sobre el curso 1):

| Implementación | Peticiones fallidas | p95 | ¿Cumple? | Dónde se midió |
|---|---|---|---|---|
| Inicial (`SELECT … FOR UPDATE` + validar con el candado) | 94% (timeouts) | 10 s (tope del timeout de k6) | ✗ | Revisión del 4 nov, API sin Docker, 30 s de carga |
| Atómica (`UPDATE … WHERE cupos > 0`) | 0% | 54 ms | ✓ | Revisión del 4 nov, API sin Docker, 30 s de carga |
| Atómica, sistema completo con telemetría | 0% | 137 ms | ✓ | Ensayo de `build/hito2`, en Docker |

## 2. Fiabilidad

| Métrica | Meta | Cómo se mide | Prueba |
|---|---|---|---|
| SLI de asignación | ≥ 95% de peticiones válidas buenas (201 o 409 en < 2 s) | `sli:asignacion:ratio_rate30s` | Avalancha; `infra/prometheus/tests/slo_test.yml` (promtool) |
| Integridad de cupos (RF2) | Exactamente 30 asignadas, 470 "curso lleno", 0 cupos, nadie dos veces | Contadores de k6 + consulta a `asignaciones` | `load-tests/rf2_concurrencia.js` (500 solicitudes simultáneas) |
| Tolerancia a fallos | Con el pool agotado, responder 503 en ≤ `POOL_TIMEOUT_S` (5 s) en lugar de colgarse | Código `503` en `asignaciones_total{status}` | `test_503_pool_saturado` (pytest) |
| Detección | Aviso en Discord ≤ 60 s desde que el SLI cae bajo 95%; ningún aviso con tráfico normal | Hora de la alerta en Alertmanager | Demo (MTTD en `docs/guion-demo.md`); promtool, caso "tráfico sano" sin alertas |

**Resultados:** RF2 dio 30 / 470 / 0 y 30 estudiantes distintos en la tabla `asignaciones`
(revisión del 4 nov). Las pruebas de promtool del SLI y de las 4 alertas pasan.

## 3. Mantenibilidad

| Métrica | Meta | Cómo se mide | Prueba |
|---|---|---|---|
| Casos de RF1 automatizados | 201, 409 lleno, 409 repetido, 404, 503 y 422 en los **dos** modos | `api/tests/` | `pytest`: 22 pruebas, todas pasan |
| Pruebas en cada cambio | Cada pull request corre las pruebas antes de unirse a `dev` | GitHub Actions | `.github/workflows/ci.yml` (pytest + promtool + build) |
| Capacidad de ser analizado | Desde una alerta se llega a la causa raíz sin entrar al servidor | Traza con `db.pool.acquire`, `validaciones` y `db.query`; salto a logs por `trace_id` | Bloque 4 de la demo |
| Modularidad | La corrección cambia una función (`asignar_atomico`) sin tocar portal, telemetría ni infraestructura | Revisión del diff | Feature flag `modo_atomico` |

## 4. Trazabilidad requisito → prueba

| Requisito | Prueba automática | Paso de la demo |
|---|---|---|
| RF1 | pytest (`test_201…`, `test_409…`, `test_404…`, `test_422…`) | Bloque 1 |
| RF2 | `rf2_concurrencia.js` | Bloque 2 |
| RNF1 | — (se verifica visualmente) | Bloque 4 |
| RNF2 | — | Bloque 3 (tráfico visible en ≤ 10 s, refresco de 5 s) |
| RNF3 | `slo_test.yml` (promtool) | Bloques 3 y 5 (🔴 y 🟢 en Discord) |
| HU1 | pytest + portal | Bloque 1 |
| HU2 | — | Bloque 4 |

## 5. Cómo correr todas las pruebas

```powershell
# RF1 (API)
docker compose run --rm -v ${PWD}/api/tests:/srv/tests -e OTEL_SDK_DISABLED=true api sh -c "pip install -q -r tests/requirements.txt && python -m pytest -q tests"
# SLO y alertas
docker run --rm -v ${PWD}/infra/prometheus:/p -w /p --entrypoint promtool prom/prometheus:v2.54.1 test rules tests/slo_test.yml
# RF2
docker compose run --rm k6 run /scripts/rf2_concurrencia.js
# Desempeño (avalancha)
docker compose run --rm k6
```
