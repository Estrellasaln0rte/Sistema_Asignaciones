"""Las dos implementaciones del descuento de cupos (RF2).

- Inicial: toma el candado de la fila del curso, valida y después descuenta.
  Con muchas solicitudes al mismo curso cada una espera su turno con el candado
  y la conexión ocupados, y el pool se agota. Es el escenario del caso de uso 2.
- Atómica (la corrección): valida antes de tomar una conexión y luego verifica y
  descuenta en una sola instrucción UPDATE ... WHERE cupos > 0, que libera el
  candado de inmediato.
"""

import os
import time

from opentelemetry import trace

tracer = trace.get_tracer("asignaciones")

# Tiempo de las validaciones (prerrequisitos, choques de horario, etc.), simulado.
VALIDACIONES_S = float(os.getenv("VALIDACIONES_S", "0.05"))


def validar():
    with tracer.start_as_current_span("validaciones"):
        time.sleep(VALIDACIONES_S)


def asignar_inicial(conn, estudiante_id: str, curso_id: int):
    with conn.transaction():
        with tracer.start_as_current_span("db.query", attributes={"db.operacion": "select_for_update"}):
            fila = conn.execute("SELECT cupos FROM cursos WHERE id = %s FOR UPDATE", (curso_id,)).fetchone()
        if fila is None:
            return 404, {"detalle": "Curso inexistente"}
        # Las validaciones se hacen con el candado tomado: todas las solicitudes
        # al mismo curso quedan en fila, aunque ya no haya cupo.
        validar()
        if fila[0] <= 0:
            return 409, {"detalle": "Curso lleno"}
        with tracer.start_as_current_span("db.query", attributes={"db.operacion": "update_insert"}):
            conn.execute("UPDATE cursos SET cupos = cupos - 1 WHERE id = %s", (curso_id,))
            conn.execute(
                "INSERT INTO asignaciones (estudiante_id, curso_id) VALUES (%s, %s)",
                (estudiante_id, curso_id),
            )
        return 201, {"detalle": "Asignación confirmada", "cupos_restantes": fila[0] - 1}


def asignar_atomico(conn, estudiante_id: str, curso_id: int):
    # Las validaciones ya se hicieron antes de tomar la conexión (ver main.asignar).
    with conn.transaction():
        with tracer.start_as_current_span("db.query", attributes={"db.operacion": "update_atomico"}):
            fila = conn.execute(
                "UPDATE cursos SET cupos = cupos - 1 WHERE id = %s AND cupos > 0 RETURNING cupos",
                (curso_id,),
            ).fetchone()
            if fila is None:
                existe = conn.execute("SELECT 1 FROM cursos WHERE id = %s", (curso_id,)).fetchone()
                return (409, {"detalle": "Curso lleno"}) if existe else (404, {"detalle": "Curso inexistente"})
            conn.execute(
                "INSERT INTO asignaciones (estudiante_id, curso_id) VALUES (%s, %s)",
                (estudiante_id, curso_id),
            )
        return 201, {"detalle": "Asignación confirmada", "cupos_restantes": fila[0]}
