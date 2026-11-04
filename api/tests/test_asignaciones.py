"""Pruebas de RF1: respuestas de POST /asignaciones y validaciones de entrada."""

import pytest
from psycopg_pool import PoolTimeout

from app import main


def asignar(cliente, estudiante_id, curso_id):
    return cliente.post("/asignaciones", json={"estudiante_id": estudiante_id, "curso_id": curso_id})


def cupos(curso_id):
    with main.pool.connection() as conn:
        return conn.execute("SELECT cupos FROM cursos WHERE id = %s", (curso_id,)).fetchone()[0]


# ---------- RF1: casos de negocio (con los dos modos) ----------

def test_201_asignacion_confirmada(cliente, modo, curso, carne):
    curso_id = curso(cupos=5)
    r = asignar(cliente, carne(), curso_id)
    assert r.status_code == 201
    assert r.json() == {"detalle": "Asignación confirmada", "cupos_restantes": 4}
    assert cupos(curso_id) == 4


def test_409_curso_lleno(cliente, modo, curso, carne):
    curso_id = curso(cupos=1)
    assert asignar(cliente, carne(), curso_id).status_code == 201
    r = asignar(cliente, carne(), curso_id)
    assert r.status_code == 409
    assert r.json() == {"detalle": "Curso lleno"}
    assert cupos(curso_id) == 0


def test_409_estudiante_ya_asignado(cliente, modo, curso, carne):
    curso_id = curso(cupos=5)
    estudiante = carne()
    assert asignar(cliente, estudiante, curso_id).status_code == 201
    r = asignar(cliente, estudiante, curso_id)
    assert r.status_code == 409
    assert r.json() == {"detalle": "El estudiante ya está asignado a este curso"}
    assert cupos(curso_id) == 4  # el intento repetido no descuenta cupo


def test_404_curso_inexistente(cliente, modo, carne):
    r = asignar(cliente, carne(), 999_999)
    assert r.status_code == 404
    assert r.json() == {"detalle": "Curso inexistente"}


def test_503_pool_saturado(cliente, modo, carne, monkeypatch):
    def sin_conexiones(*args, **kwargs):
        raise PoolTimeout("pool agotado")

    monkeypatch.setattr(main.pool, "getconn", sin_conexiones)
    r = asignar(cliente, carne(), 1)
    assert r.status_code == 503
    assert r.json() == {"detalle": "Servicio saturado, intente de nuevo"}


# ---------- Validaciones de entrada (422) ----------

@pytest.mark.parametrize("estudiante_id", ["", "   ", "11 02124", "1102124;DROP", "x" * 21])
def test_422_carne_invalido(cliente, estudiante_id):
    r = asignar(cliente, estudiante_id, 1)
    assert r.status_code == 422
    assert r.json()["detalle"].startswith("Carné inválido")


@pytest.mark.parametrize("curso_id", [0, -1, "abc", 1.5, None])
def test_422_curso_invalido(cliente, carne, curso_id):
    r = asignar(cliente, carne(), curso_id)
    assert r.status_code == 422
    assert r.json() == {"detalle": "El curso debe ser un número entero positivo"}


def test_422_sin_cuerpo(cliente):
    r = cliente.post("/asignaciones")
    assert r.status_code == 422
    assert r.json() == {"detalle": "Solicitud inválida"}


def test_carne_de_pruebas_de_carga_es_valido(cliente, curso):
    """Los identificadores de k6 (est-1-2, rf2-15) deben seguir aceptándose."""
    curso_id = curso(cupos=5)
    assert asignar(cliente, "est-1-2", curso_id).status_code == 201
    assert asignar(cliente, "rf2-15", curso_id).status_code == 201
