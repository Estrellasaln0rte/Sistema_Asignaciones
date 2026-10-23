-- Esquema mínimo del prototipo: cursos con cupo limitado y asignaciones.

CREATE TABLE cursos (
    id      SERIAL PRIMARY KEY,
    codigo  TEXT NOT NULL UNIQUE,
    nombre  TEXT NOT NULL,
    cupos   INTEGER NOT NULL CHECK (cupos >= 0)   -- RF2: nunca cupos negativos
);

CREATE TABLE asignaciones (
    id             BIGSERIAL PRIMARY KEY,
    estudiante_id  TEXT NOT NULL,
    curso_id       INTEGER NOT NULL REFERENCES cursos(id),
    creada_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (estudiante_id, curso_id)              -- RF2: nunca asignado dos veces
);

-- Curso 1 es la "fila caliente": área común con 30 cupos.
INSERT INTO cursos (codigo, nombre, cupos) VALUES
    ('ISW1', 'Ingeniería de Software I', 30),
    ('MAT1', 'Matemática I', 120),
    ('FIS1', 'Física I', 80);
