// Criterio de RF2: 500 solicitudes simultáneas sobre un curso de 30 cupos.
// Esperado: exactamente 30 asignaciones (201), 470 "curso lleno" (409) y 0 cupos.
// Antes de correrlo: curl -X POST "http://localhost:8000/admin/reiniciar?cupos=30"
// Uso: docker compose run --rm k6 run /scripts/rf2_concurrencia.js
import http from "k6/http";
import { Counter } from "k6/metrics";

const API = __ENV.API_URL || "http://localhost:8000";
const asignadas = new Counter("asignadas_201");
const llenas = new Counter("curso_lleno_409");
const otras = new Counter("otras_respuestas");

export const options = {
  scenarios: {
    simultaneas: { executor: "per-vu-iterations", vus: 500, iterations: 1, maxDuration: "1m" },
  },
  thresholds: {
    asignadas_201: ["count==30"],
    curso_lleno_409: ["count==470"],
    otras_respuestas: ["count==0"],
  },
};

export default function () {
  const r = http.post(
    `${API}/asignaciones`,
    JSON.stringify({ estudiante_id: `rf2-${__VU}`, curso_id: 1 }),
    { headers: { "Content-Type": "application/json" }, timeout: "30s" },
  );
  if (r.status === 201) asignadas.add(1);
  else if (r.status === 409) llenas.add(1);
  else otras.add(1);
}

export function teardown() {
  const curso = http.get(`${API}/cursos`).json().find((c) => c.id === 1);
  console.log(`Cupos finales del curso 1: ${curso.cupos} (esperado 0)`);
}
