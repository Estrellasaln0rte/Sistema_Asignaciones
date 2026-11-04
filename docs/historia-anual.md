# Historia anual simulada: predecir el próximo pico

El prototipo guarda la historia real de cada ejecución (`docs/historia-y-kpis.md`), pero un año
real no se puede esperar para la entrega. Para **ejemplificar** cómo SRE usa la historia para
prevenir, el proyecto carga en Prometheus un año **simulado** del portal de asignación
(noviembre 2025 a octubre 2026).

> Son datos ficticios y se declaran así. Usan métricas propias (`historico_*`) con la etiqueta
> `fuente="simulado"`: no tocan las métricas reales, el SLI, las alertas ni el dashboard
> *Asignaciones · SRE*. La historia de las corridas en vivo se sigue guardando igual.

## 1. Qué contiene

| Métrica | Qué representa (una muestra por hora) |
|---|---|
| `historico_peticiones_por_minuto{facultad}` | Pico de peticiones por minuto, por facultad |
| `historico_sli_asignacion` | SLI de la hora |
| `historico_pool_saturacion` | Conexiones en uso / tamaño del pool |
| `historico_alertas_disparadas` | Alertas en *firing* |
| `historico_dia_critico_pico{fecha, evento}` y `historico_dia_critico_sli{fecha, evento}` | Pico y SLI de cada día del calendario académico |

El año sigue un calendario creíble: tráfico bajo y de día en días normales, menos en fin de
semana, y 9 eventos (asignación de primer y segundo ciclo con dos días cada una, cambios de
sección, extemporáneas e interciclo). Los días 1 de asignación tienen el pico de la
implementación inicial: unas 12 000 peticiones/min (≈ 200 por segundo, lo mismo que la
avalancha de k6), SLI de 52% a 58% y el pool al 100%. El generador usa una semilla fija, así que
siempre produce los mismos datos.

## 2. Cómo se carga (una sola vez)

En PowerShell, en la carpeta del proyecto, con el sistema levantado:

```powershell
# 1. Generar el año simulado (usa la imagen de la API, no hace falta instalar Python)
docker compose run --rm --no-deps -v "${PWD}/historia:/historia" api python /historia/generar_historia.py /historia/historia.om

# 2. Cargarlo en Prometheus (con Prometheus detenido)
docker compose stop prometheus
docker compose --profile historia run --rm historia
docker compose up -d prometheus   # aplica también la retención de 400 días
```

Para que no se borre, Prometheus guarda **400 días** (`docker-compose.yml`). La carga queda en el
volumen `promdata`: sobrevive a `docker compose down` y solo se borra con `down -v` (después de
un `down -v` se repiten los pasos 1 y 2).

## 3. El dashboard *Historia anual · datos simulados*

Dashboards → SRE → **Historia anual · datos simulados**. El rango ya viene fijo en el año
simulado.

| Panel | Qué pregunta responde |
|---|---|
| Pico de tráfico del año, Peor SLI del año, Horas con el SLO incumplido, Días críticos | ¿Qué tan malo fue el año? |
| Tráfico por facultad (con marcas de los eventos) | ¿Cuándo hay más tráfico? Enero y julio, día 1, de 7:00 a 9:00 |
| SLI histórico y saturación del pool | ¿Cuándo fallamos? Solo en las ventanas de asignación |
| Días críticos del año | Ranking de días por tráfico, con su SLI |
| Quién genera el pico | Ingeniería: 42% del pico, aunque en un día normal es el 30% |
| Qué nos dice la historia | La predicción y las acciones |

Valores esperados (comprobados con Prometheus): pico de 12 140 peticiones/min, peor SLI de 54%,
14 horas con el SLO incumplido y 7 días críticos con más de 1 000 peticiones/min.

## 4. De la historia a la acción (SRE preventivo)

1. **Predecir:** las ventanas críticas caen siempre el lunes de apertura de cada ciclo. Las
   próximas son el **11 de enero de 2027** y el **5 de julio de 2027**, desde las 7:00.
2. **Ensayar:** la semana anterior, correr la avalancha de k6 al pico histórico (≈ 210
   peticiones/s) y comprobar que el SLO se cumple.
3. **Proteger el presupuesto:** si el presupuesto de error está gastado, congelar cambios antes
   de la ventana.
4. **Repartir la carga por grupo de usuarios:** como Ingeniería concentra el pico, escalonar la
   apertura por facultad (Ingeniería 7:00, Ciencias Económicas 8:00, el resto 9:00) y avisar a
   cada facultad con anticipación. Es la misma idea de enfocar acciones en los días y usuarios de
   más tráfico, sin agregar hardware.
5. **Guardia:** ese día, el equipo de guardia desde las 6:30 con el dashboard *Asignaciones · SRE*
   abierto.
