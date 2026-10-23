"""API del Sistema de Asignaciones.

Por ahora solo expone /salud para verificar que la API está arriba y que
puede conectarse a PostgreSQL.
"""

import os

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Sistema de Asignaciones")


@app.get("/salud")
def salud():
    try:
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3) as conn:
            conn.execute("SELECT 1")
        return {"api": "ok", "base_de_datos": "ok"}
    except psycopg.Error:
        return JSONResponse(status_code=503, content={"api": "ok", "base_de_datos": "sin conexión"})
