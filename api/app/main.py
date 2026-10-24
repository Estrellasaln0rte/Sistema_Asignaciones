"""API del Sistema de Asignaciones (RF1, RF2), instrumentada con OpenTelemetry (RNF1).

La implementación de la asignación se elige con el feature flag `modo_atomico`
(MODO_ATOMICO en .env, o en caliente con PUT /admin/flags).
"""

import logging
import os
import time

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from psycopg_pool import ConnectionPool, PoolTimeout
from pydantic import BaseModel, Field

from .asignacion import asignar_atomico, asignar_inicial, validar
from .telemetria import configurar_telemetria, observar_pool, registrar_asignacion

configurar_telemetria()

log = logging.getLogger("asignaciones")
tracer = trace.get_tracer("asignaciones")

POOL_SIZE = int(os.getenv("POOL_SIZE", "10"))
POOL_TIMEOUT_S = float(os.getenv("POOL_TIMEOUT_S", "5"))

flags = {"modo_atomico": os.getenv("MODO_ATOMICO", "false").lower() == "true"}

pool = ConnectionPool(
    os.environ["DATABASE_URL"],
    min_size=POOL_SIZE,
    max_size=POOL_SIZE,
    timeout=POOL_TIMEOUT_S,
    open=True,
)
observar_pool(pool, POOL_SIZE)

app = FastAPI(title="Sistema de Asignaciones")
FastAPIInstrumentor.instrument_app(app)


class Solicitud(BaseModel):
    estudiante_id: str = Field(min_length=1, max_length=40)
    curso_id: int


class Flags(BaseModel):
    modo_atomico: bool


@app.get("/salud")
def salud():
    try:
        with pool.connection() as conn:
            conn.execute("SELECT 1")
        return {"api": "ok", "base_de_datos": "ok"}
    except (psycopg.Error, PoolTimeout):
        return JSONResponse(status_code=503, content={"api": "ok", "base_de_datos": "sin conexión"})


@app.get("/cursos")
def listar_cursos():
    with pool.connection() as conn:
        filas = conn.execute("SELECT id, codigo, nombre, cupos FROM cursos ORDER BY id").fetchall()
    return [{"id": f[0], "codigo": f[1], "nombre": f[2], "cupos": f[3]} for f in filas]


@app.post("/asignaciones")
def asignar(sol: Solicitud):
    inicio = time.perf_counter()
    modo = "atomico" if flags["modo_atomico"] else "inicial"
    trace.get_current_span().set_attributes({"asignacion.curso_id": sol.curso_id, "asignacion.modo": modo})

    try:
        if flags["modo_atomico"]:
            # Corrección: validar fuera de la transacción, sin conexión ni candado.
            validar()
        with tracer.start_as_current_span("db.pool.acquire"):
            conn = pool.getconn()
        try:
            implementacion = asignar_atomico if flags["modo_atomico"] else asignar_inicial
            status, cuerpo = implementacion(conn, sol.estudiante_id, sol.curso_id)
        except psycopg.errors.UniqueViolation:
            status, cuerpo = 409, {"detalle": "El estudiante ya está asignado a este curso"}
        finally:
            pool.putconn(conn)
    except PoolTimeout:
        status, cuerpo = 503, {"detalle": "Servicio saturado, intente de nuevo"}
    except Exception:
        log.exception("Error inesperado en la asignación")
        status, cuerpo = 500, {"detalle": "Error interno"}

    segundos = time.perf_counter() - inicio
    sli = registrar_asignacion(status, segundos, modo)
    log.info(
        "asignacion procesada",
        extra={"curso_id": sol.curso_id, "estudiante_id": sol.estudiante_id, "status": status,
               "sli": sli, "modo": modo, "duracion_ms": round(segundos * 1000, 1)},
    )
    return JSONResponse(status_code=status, content=cuerpo)


# ---------- Administración de la demo ----------

@app.get("/admin/flags")
def ver_flags():
    return flags


@app.put("/admin/flags")
def cambiar_flags(nuevos: Flags):
    """Feature flag de la corrección (paso 5 del caso de uso 2)."""
    flags["modo_atomico"] = nuevos.modo_atomico
    log.warning("feature flag cambiado", extra={"modo_atomico": nuevos.modo_atomico})
    return flags


@app.post("/admin/reiniciar")
def reiniciar(cupos: int = 30):
    """Restablece el curso caliente (curso 1) entre corridas de la demo."""
    with pool.connection() as conn:
        conn.execute("DELETE FROM asignaciones WHERE curso_id = 1")
        conn.execute("UPDATE cursos SET cupos = %s WHERE id = 1", (cupos,))
    return {"curso_id": 1, "cupos": cupos}
