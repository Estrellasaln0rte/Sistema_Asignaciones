// Caso de uso 2: avalancha de estudiantes sobre el curso caliente.
// Uso: docker compose run --rm k6
//      docker compose run --rm -e RPS=100 -e DURACION=1m k6
import http from "k6/http";
import { check } from "k6";

const API = __ENV.API_URL || "http://localhost:8000";
const RPS = Number(__ENV.RPS || 200);
const DURACION = __ENV.DURACION || "3m";
const CURSO = Number(__ENV.CURSO_ID || 1);

export const options = {
  scenarios: {
    avalancha: {
      executor: "ramping-arrival-rate",
      startRate: 10,
      timeUnit: "1s",
      preAllocatedVUs: 200,
      maxVUs: 1000,
      stages: [
        { target: RPS, duration: "20s" },
        { target: RPS, duration: DURACION },
        { target: 0, duration: "10s" },
      ],
    },
  },
  thresholds: {
    // Mismo SLO del sistema: 95% de las respuestas en menos de 2 s.
    "http_req_duration{esperado:si}": ["p(95)<2000"],
  },
};

export default function () {
  const estudiante = `est-${__VU}-${__ITER}`;
  const r = http.post(
    `${API}/asignaciones`,
    JSON.stringify({ estudiante_id: estudiante, curso_id: CURSO }),
    {
      headers: { "Content-Type": "application/json" },
      timeout: "10s",
      tags: { esperado: "si" },
      responseCallback: http.expectedStatuses(201, 409),
    },
  );
  check(r, { "201 o 409": (res) => res.status === 201 || res.status === 409 });
}
