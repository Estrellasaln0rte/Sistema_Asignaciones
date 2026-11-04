"""Genera un año SIMULADO de historia del portal de asignación para Prometheus.

Sirve para ejemplificar SRE con datos históricos: encontrar en el año anterior los días con
más tráfico y más problemas (las ventanas de asignación), ver qué facultades concentran la carga
y, con eso, prepararse antes del próximo pico.

Los datos son ficticios y se distinguen de los reales:
- todas las métricas empiezan con `historico_` (las reales son asignaciones_total, etc.);
- todas llevan la etiqueta fuente="simulado".
Así no afectan el SLI, las alertas ni el dashboard principal.

Uso (lo corre docker compose, ver docs/historia-anual.md):
    python generar_historia.py [salida.om]

Salida: un archivo OpenMetrics que se carga con
    promtool tsdb create-blocks-from openmetrics historia.om /prometheus
"""

import math
import random
import sys
from datetime import datetime, timedelta, timezone

random.seed(2026)  # mismo resultado cada vez: la demo es reproducible

ZONA = timezone(timedelta(hours=-6))  # Guatemala
# Año anterior completo, hasta ayer (respecto a la fecha de la entrega).
INICIO = datetime(2025, 11, 1, 0, 0, tzinfo=ZONA)
FIN = datetime(2026, 11, 1, 0, 0, tzinfo=ZONA)
PASO = timedelta(hours=1)

# Peso de cada facultad en el tráfico normal y en las ventanas de asignación.
# Ingeniería concentra más en la asignación porque sus cursos de área común son la "fila caliente".
FACULTADES = {
    "ingenieria":           {"normal": 0.30, "asignacion": 0.42},
    "ciencias_economicas":  {"normal": 0.28, "asignacion": 0.25},
    "ciencias_juridicas":   {"normal": 0.16, "asignacion": 0.13},
    "humanidades":          {"normal": 0.14, "asignacion": 0.10},
    "ciencias_salud":       {"normal": 0.12, "asignacion": 0.10},
}

# Eventos del calendario académico: (fecha, hora de apertura, evento, pico de peticiones/min,
# SLI de ese día, saturación del pool). El pico y el SLI malo son los de la implementación
# inicial, antes de la corrección atómica.
EVENTOS = [
    ("2026-01-12", 7, "Asignación primer ciclo 2026 (día 1)", 11800, 0.58, 1.00),
    ("2026-01-13", 7, "Asignación primer ciclo 2026 (día 2)", 5200, 0.81, 1.00),
    ("2026-01-19", 8, "Cambios de sección primer ciclo", 2100, 0.96, 0.70),
    ("2026-01-26", 8, "Asignación extemporánea primer ciclo", 900, 0.99, 0.40),
    ("2026-06-01", 8, "Asignación de interciclo", 1500, 0.97, 0.60),
    ("2026-07-06", 7, "Asignación segundo ciclo 2026 (día 1)", 12600, 0.52, 1.00),
    ("2026-07-07", 7, "Asignación segundo ciclo 2026 (día 2)", 5600, 0.79, 1.00),
    ("2026-07-13", 8, "Cambios de sección segundo ciclo", 2300, 0.95, 0.75),
    ("2026-07-20", 8, "Asignación extemporánea segundo ciclo", 950, 0.99, 0.40),
]
EVENTOS_POR_DIA = {e[0]: e for e in EVENTOS}


def trafico_normal(t: datetime) -> float:
    """Peticiones/min de un día cualquiera: más de día, menos en fin de semana."""
    if t.weekday() >= 5:
        base = 3
    else:
        base = 8
    # Curva diaria: casi nada de noche, pico a media mañana y otro en la tarde.
    hora = t.hour + 0.5
    curva = max(0.05, math.sin(math.pi * (hora - 6) / 16)) if 6 <= hora <= 22 else 0.05
    return base * curva * random.uniform(0.8, 1.2)


def trafico_evento(t: datetime, evento) -> float:
    """Pico de la ventana de asignación: sube de golpe a la hora de apertura y decae."""
    _, apertura, _, pico, _, _ = evento
    if t.hour < apertura - 1:
        return 0
    if t.hour == apertura - 1:
        return pico * 0.05  # estudiantes esperando con la página abierta
    horas_desde = t.hour - apertura
    return pico * math.exp(-0.55 * horas_desde) * random.uniform(0.92, 1.05)


def serie(nombre, etiquetas, valores):
    et = ",".join(f'{k}="{v}"' for k, v in etiquetas.items())
    return [f"{nombre}{{{et}}} {v:.4f} {int(ts)}" for ts, v in valores]


def main(salida: str) -> None:
    puntos_fac = {f: [] for f in FACULTADES}
    sli, pool, alertas = [], [], []
    criticos_pico, criticos_sli = [], []

    t = INICIO
    while t < FIN:
        ts = t.timestamp()
        dia = t.strftime("%Y-%m-%d")
        evento = EVENTOS_POR_DIA.get(dia)
        normal = trafico_normal(t)
        extra = trafico_evento(t, evento) if evento else 0

        for fac, peso in FACULTADES.items():
            puntos_fac[fac].append((ts, normal * peso["normal"] + extra * peso["asignacion"]))

        total = normal + extra
        if evento and extra > 1000:
            # La hora pesada del evento: el SLI y el pool reflejan la fila caliente.
            intensidad = min(1.0, extra / evento[3])
            sli_h = 1 - (1 - evento[4]) * intensidad * random.uniform(0.9, 1.0)
            pool_h = max(0.3, evento[5] * intensidad)
        else:
            sli_h = random.uniform(0.985, 1.0)
            pool_h = min(0.25, 0.02 + total / 400)
        sli.append((ts, sli_h))
        pool.append((ts, pool_h))
        alertas.append((ts, 4 if sli_h < 0.95 else (2 if pool_h >= 0.9 else 0)))

        # Un punto por evento, al mediodía, para la tabla de días críticos.
        if evento and t.hour == 12:
            etq = {"fecha": dia, "evento": evento[2], "fuente": "simulado"}
            criticos_pico.append((etq, ts, evento[3]))
            criticos_sli.append((etq, ts, evento[4]))
        t += PASO

    lineas = []
    lineas.append("# HELP historico_peticiones_por_minuto Pico de peticiones de asignación por minuto en cada hora (simulado)")
    lineas.append("# TYPE historico_peticiones_por_minuto gauge")
    for fac, valores in puntos_fac.items():
        lineas += serie("historico_peticiones_por_minuto", {"facultad": fac, "fuente": "simulado"}, valores)
    lineas.append("# HELP historico_sli_asignacion SLI de asignación por hora (simulado)")
    lineas.append("# TYPE historico_sli_asignacion gauge")
    lineas += serie("historico_sli_asignacion", {"fuente": "simulado"}, sli)
    lineas.append("# HELP historico_pool_saturacion Conexiones en uso / tamaño del pool, por hora (simulado)")
    lineas.append("# TYPE historico_pool_saturacion gauge")
    lineas += serie("historico_pool_saturacion", {"fuente": "simulado"}, pool)
    lineas.append("# HELP historico_alertas_disparadas Alertas en firing en cada hora (simulado)")
    lineas.append("# TYPE historico_alertas_disparadas gauge")
    lineas += serie("historico_alertas_disparadas", {"fuente": "simulado"}, alertas)
    lineas.append("# HELP historico_dia_critico_pico Pico de peticiones/min del día de cada evento (simulado)")
    lineas.append("# TYPE historico_dia_critico_pico gauge")
    for etq, ts, v in criticos_pico:
        lineas += serie("historico_dia_critico_pico", etq, [(ts, v)])
    lineas.append("# HELP historico_dia_critico_sli SLI del día de cada evento (simulado)")
    lineas.append("# TYPE historico_dia_critico_sli gauge")
    for etq, ts, v in criticos_sli:
        lineas += serie("historico_dia_critico_sli", etq, [(ts, v)])
    lineas.append("# EOF")

    with open(salida, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas) + "\n")
    horas = len(sli)
    print(f"Historia simulada: {horas} horas ({horas // 24} días), {len(EVENTOS)} eventos -> {salida}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "historia.om")
