"""Prepara un curso propio para las pruebas y lo borra al terminar.

Las pruebas usan la misma base de datos del sistema (DATABASE_URL), pero nunca
tocan los cursos de la demo: crean el curso PRUEBA-RF1 y lo eliminan al final.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture(scope="session")
def cliente():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture(params=["inicial", "atomico"])
def modo(request):
    """Cada prueba de RF1 corre con las dos implementaciones de la asignación."""
    anterior = main.flags["modo_atomico"]
    main.flags["modo_atomico"] = request.param == "atomico"
    yield request.param
    main.flags["modo_atomico"] = anterior


@pytest.fixture
def curso():
    """Crea un curso con cupos a elección y lo borra, con sus asignaciones, al terminar."""
    creados = []

    def crear(cupos: int) -> int:
        codigo = f"PRUEBA-{uuid.uuid4().hex[:8]}"
        with main.pool.connection() as conn:
            curso_id = conn.execute(
                "INSERT INTO cursos (codigo, nombre, cupos) VALUES (%s, 'Curso de prueba RF1', %s) RETURNING id",
                (codigo, cupos),
            ).fetchone()[0]
        creados.append(curso_id)
        return curso_id

    yield crear

    with main.pool.connection() as conn:
        for curso_id in creados:
            conn.execute("DELETE FROM asignaciones WHERE curso_id = %s", (curso_id,))
            conn.execute("DELETE FROM cursos WHERE id = %s", (curso_id,))


@pytest.fixture
def carne():
    """Carné distinto en cada llamada, para que las pruebas no choquen entre sí."""
    return lambda: str(1_000_000_000 + uuid.uuid4().int % 1_000_000_000)
