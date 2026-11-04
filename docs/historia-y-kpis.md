# Historia, tendencias y KPIs

Responde a la corrección del ingeniero al hito 1: *"reforzar los beneficios de tener historia,
métricas, tendencias y KPIs"* y que SRE no es solo reactivo, sino preventivo y predictivo.

## 1. Qué se guarda y cuánto tiempo

| Señal | Dónde | Volumen | Retención |
|---|---|---|---|
| Métricas (SLI, latencia, pool, alertas) | Prometheus | `promdata` | 400 días (`--storage.tsdb.retention.time=400d`) |
| Trazas | Tempo | `tempodata` | 14 días (valor por defecto de Tempo) |
| Logs | Loki | `lokidata` | Sin borrado automático |
| Cursos y asignaciones | PostgreSQL | `pgdata` | Permanente |

La historia sobrevive a `docker compose down` y a reiniciar la computadora. Solo se borra con
`docker compose down -v`.

## 2. Cómo se usa la historia en el sistema

| Uso | Tipo de SRE | Dónde se ve |
|---|---|---|
| Ventanas de 1 y 5 minutos para la quema del presupuesto de error | Preventivo | Alerta `PresupuestoErrorQuemaRapida` |
| Tendencia de los últimos 2 minutos del pool proyectada 60 s con `predict_linear` | Predictivo | Alerta `PoolConexionesPorAgotarse` |
| KPIs calculados sobre cualquier periodo | Aprender / planificar | Fila **Historia y KPIs** del dashboard |
| Comparar el presente con el pasado (`offset`) | Tendencias | Gráficas *ahora vs hace $comparar* |
| Historial de las alertas (serie `ALERTS`) | Postmortem (MTTD, MTTR) | Panel *Tiempo con el SLO incumplido* |

## 3. La fila "Historia y KPIs" del dashboard

Todos los paneles se recalculan con el rango de tiempo elegido arriba a la derecha (`$__range`):
*Last 15 minutes* muestra la demo; *Last 2 days* incluye el ensayo de ayer; *Last 30 days*, todo
lo guardado.

| Panel | KPI del hito 1 | Consulta (resumen) |
|---|---|---|
| Cumplimiento del SLO en el periodo | Cumplimiento del SLO | buenas / válidas con `increase(…[$__range])` |
| Presupuesto de error consumido | Presupuesto consumido | malas / (5% de las válidas) |
| Pico de saturación del pool | Saturación máxima del pool | `max_over_time` de conexiones en uso / tamaño |
| Tiempo con el SLO incumplido | Duración del incidente (base del MTTR) | `sum_over_time` de la alerta en *firing* × 5 s |
| Asignaciones exitosas en el periodo | Asignaciones exitosas | `increase` de las respuestas 201 |
| SLI por modo y p95 por modo | Antes vs después de la corrección | Las mismas consultas agrupadas por `modo` |
| Latencia p95 y SLI: ahora vs hace $comparar | Tendencias | La métrica con `offset $comparar` (5m a 7d) |

Las consultas se probaron con promtool sobre datos simulados de una avalancha en modo inicial
seguida de una en modo atómico: SLI de 10% contra 100%, p95 de 2 s contra 0,095 s, pool al 100% y
295 s con el SLO incumplido.

## 4. Cómo se aplica al caso real

- **Antes del semestre:** se compara la carga del semestre anterior (*Last 30 days*, o una
  retención más larga) y se repite la avalancha como ensayo. Si el pico del pool llegó al 100% o
  el presupuesto se agotó, se corrige antes de abrir la asignación.
- **Durante la ventana crítica:** las alertas predictiva y preventivas usan la tendencia reciente
  para avisar antes de romper el SLO.
- **Después:** el postmortem toma los KPIs del periodo del incidente (`docs/postmortem.md`).

La retención de 400 días permite comparar semestre contra semestre. Para ejemplificarlo sin
esperar un año real, el proyecto carga un año **simulado**: ver `docs/historia-anual.md`.
