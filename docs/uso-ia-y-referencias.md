# Declaración del uso de IA y referencias

El enunciado (sección 9) permite la IA como herramienta, pero pide declararla, comprenderla y
poder defenderla. **Revisen y ajusten esta sección para que diga exactamente lo que hizo el
equipo.**

## 1. Uso de IA

| Herramienta | Para qué se usó | Cómo lo validó el equipo |
|---|---|---|
| Claude (Anthropic) | Armar la base del prototipo para el ensayo del hito 2 (`build/hito2`), proponer el plan de desarrollo y las ramas, revisar código y documentos, redactar borradores del plan de calidad, seguridad, postmortem y guion de la demo | Cada integrante es responsable de los archivos de su rama, los revisó en un pull request y los probó con las pruebas automáticas (pytest, promtool, k6) y en el ensayo de la demo |
| __ (otra, si aplica) | | |

Lo que **no** delegamos en la IA: la elección del problema y del alcance (hito 1), las decisiones
de diseño que defendemos en la presentación (SLI con el 409 como bueno, SLO de 95% en 2 s, la
corrección atómica) y la ejecución de la demo. Todo lo presentado lo podemos explicar sin la IA.

## 2. Referencias

1. Beyer, B., Jones, C., Petoff, J. y Murphy, N. R. (2016). *Site Reliability Engineering: How
   Google Runs Production Systems*. O'Reilly. Caps. 4 (SLO), 6 (Monitoreo) y 15 (Postmortems).
   https://sre.google/sre-book/table-of-contents/ → definición de SLI/SLO, presupuesto de error y
   postmortem sin culpables.
2. Beyer, B., Murphy, N. R., Rensin, D. K., Kawahara, K. y Thorne, S. (2018). *The Site
   Reliability Workbook*. O'Reilly. Cap. 5 (Alerting on SLOs).
   https://sre.google/workbook/alerting-on-slos/ → alerta de quema del presupuesto de error
   multi-ventana (`PresupuestoErrorQuemaRapida`).
3. OpenTelemetry Authors. *OpenTelemetry Documentation* (Python SDK, Collector).
   https://opentelemetry.io/docs/ → trazas, métricas y logs con un solo estándar.
4. Prometheus Authors. *Query functions: predict_linear* y *Unit testing for rules*.
   https://prometheus.io/docs/prometheus/latest/querying/functions/#predict_linear →
   alerta predictiva del pool y pruebas con promtool.
5. PostgreSQL Global Development Group. *Explicit Locking* (`SELECT … FOR UPDATE`, bloqueos de
   fila). https://www.postgresql.org/docs/16/explicit-locking.html → causa raíz del cuello de
   botella.
6. ISO/IEC 25010:2023. *Systems and software engineering — Product quality model*. → plan de
   calidad.
7. OWASP Foundation (2025). *OWASP Top 10:2025*. https://owasp.org/Top10/ → análisis de seguridad.
8. Grafana Labs. *k6 Documentation* (`ramping-arrival-rate`, thresholds).
   https://grafana.com/docs/k6/latest/ → pruebas de carga.
9. Brown, S. *The C4 model for visualising software architecture*. https://c4model.com/ →
   diagrama de contenedores.
