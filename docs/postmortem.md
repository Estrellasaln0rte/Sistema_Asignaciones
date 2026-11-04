# Postmortem sin culpables · Saturación del curso caliente

Formato de *Site Reliability Engineering* (Google, cap. 15). Documenta el incidente que se
reproduce en la demo. Los campos marcados con `__` se llenan con las horas que anota el
equipo durante la demo: inicio de la avalancha (T0), primer aviso en Discord (T1), activación
de la corrección (T2) y aviso de resolución (T3).

| Campo | Valor |
|---|---|
| Fecha | __ de noviembre de 2026 |
| Servicio | `api-asignaciones`, `POST /asignaciones` |
| Severidad | Crítica: SLO incumplido en la ventana de asignación |
| Estado | Resuelto |

## Resumen

Al abrir la asignación, 200 estudiantes por segundo pidieron el mismo curso (Ingeniería de
Software I, 30 cupos). La implementación inicial tomaba el candado de la fila del curso y hacía
las validaciones con el candado tomado. Las solicitudes hicieron fila, el pool de 10 conexiones
se agotó y el SLI bajó de 95%. La telemetría llevó a la causa en menos de un minuto y la
corrección se activó con un feature flag, sin reiniciar.

## Impacto

- SLI de asignación: de 100% a __% durante __ minutos.
- Peticiones fallidas o lentas (> 2 s): __% (k6 `http_req_failed`).
- Integridad: **ningún** cupo negativo ni asignación duplicada (lo protegen las restricciones de
  la base de datos aun en el peor momento).

## Línea de tiempo

| Hora | Evento | Fuente |
|---|---|---|
| T0 = __:__:__ | Inicia la avalancha (k6, 200 peticiones/s) | Cronometrista |
| __:__:__ | `PoolConexionesPorAgotarse` / `PresupuestoErrorQuemaRapida` en *Firing* (alertas tempranas) | Alertmanager |
| T1 = __:__:__ | Primer 🔴 en Discord | Discord |
| __:__:__ | Se abre la traza lenta: el tiempo está en `db.pool.acquire` y `db.query` | Tempo |
| T2 = __:__:__ | `PUT /admin/flags {"modo_atomico": true}` | Log `feature flag cambiado` en Loki |
| T3 = __:__:__ | 🟢 de `SLOAsignacionIncumplido` | Discord / Alertmanager |

## KPIs del incidente

Se leen en la fila **Historia y KPIs** del dashboard, con el rango de tiempo puesto en el periodo
del incidente (ver `docs/historia-y-kpis.md`).

| KPI | Valor | Meta |
|---|---|---|
| MTTD (T1 − T0) | __ s | ≤ 60 s (RNF3) |
| MTTR (T3 − T1) | __ min __ s | Lo más bajo posible |
| Saturación máxima del pool | 10 / 10 | < 10 sostenido |
| p95 antes / después | __ s / __ s | < 2 s |

## Causa raíz

`asignar_inicial` hace `SELECT … FOR UPDATE` y luego `validar()` (50 ms) con el candado tomado.
Todas las solicitudes al mismo curso se serializan detrás de ese candado y cada una retiene una
conexión del pool mientras espera. Con 10 conexiones el sistema atiende como máximo unas 20
asignaciones por segundo en ese curso; a 200 por segundo la fila crece sin parar.

## Por qué funcionó la detección

- El SLI mide la experiencia del estudiante (201 y 409 en < 2 s), no el CPU.
- Las alertas predictiva y de presupuesto de error avisaron antes que la reactiva.
- La traza separó las capas: el servidor web y la red casi no sumaban tiempo.

## Acciones

| Acción | Tipo | Responsable | Estado |
|---|---|---|---|
| Validar fuera de la transacción y descontar con `UPDATE … WHERE cupos > 0` | Corrección | R1 | ✅ Hecho (`modo_atomico`) |
| Correr la avalancha antes de cada semestre como ensayo de capacidad | Prevención | R5 | Propuesto |
| Congelar cambios si el presupuesto de error del semestre anterior se agotó | Proceso | R4 | Propuesto |
| Límite de peticiones por cliente en Nginx | Prevención | R2 | Propuesto |

## Lecciones

- **Lo que salió bien:** la alerta llegó antes de que alguien mirara el dashboard; la causa se
  encontró con una traza, sin adivinar.
- **Lo que salió mal:** la implementación inicial pasaba todas las pruebas funcionales (RF1);
  solo la prueba de carga mostró el problema.
- **Dónde tuvimos suerte:** las restricciones de la base de datos evitaron datos inconsistentes
  aun cuando el diseño de la transacción era malo.
