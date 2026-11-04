# Guion de ejecución de la demo · Sistema de Asignaciones (SRE)

Demo en vivo de **8 minutos** dentro de la presentación de 20 a 25 minutos. Muestra el caso de
uso 2 completo: **detectar → diagnosticar → corregir → verificar**, y cierra con los KPIs del
incidente medidos en vivo (MTTD y MTTR).

## 0. Quién hace qué

Antes del ensayo, llenen esta tabla. Cada bloque tiene una persona que **habla** y otra que
**maneja la computadora**, para que nadie hable mientras escribe comandos.

| Rol | Integrante | Habla en | Maneja la computadora en |
|---|---|---|---|
| R1 · Backend | | Bloque 1 | Bloque 3 |
| R2 · Frontend | | Bloque 1 (portal) | Bloque 2 |
| R3 · Instrumentación | | Bloque 4 | Bloque 5 |
| R4 · Observabilidad | | Bloque 3 | Bloque 4 |
| R5 · Carga y calidad | | Bloques 2 y 5 | Bloque 1 |
| **Cronometrista** (cualquiera que no hable en ese momento) | | — | Anota las 4 horas de la sección 4 |

## 1. La presentación completa (20 a 25 min)

| Min | Segmento (enunciado 3.3) | Contenido | Material |
|---|---|---|---|
| 0:00 | Problema y contexto (2 min) | Fila caliente, pool saturado, TI a ciegas. Una frase: *"el problema no es que se caiga, es que nadie sabe dónde"* | Diapositivas |
| 2:00 | Arquitectura (5 min) | C4 de contenedores (`docs/c4.md`), por qué un monolito modular + stack de observabilidad y no microservicios; por qué OpenTelemetry (estándar abierto, sin amarrarse a un proveedor); SLI que cuenta el 409 como bueno | `docs/c4.md` |
| 7:00 | Ciclo de vida, calidad y seguridad (6 min) | Requisitos → pruebas: cada RF/RNF tiene su prueba automática o su paso de demo. Plan de calidad (3 atributos ISO/IEC 25010). Seguridad: CIA + OWASP. CI en GitHub Actions | `docs/plan-calidad.md`, `docs/seguridad.md`, pestaña *Actions* |
| 13:00 | **Demo en vivo (8 min)** | Sección 3 de este guion (6 bloques) | Sistema corriendo |
| 21:00 | Lecciones y cierre (2 min) | Postmortem con MTTD/MTTR medidos en la demo, lecciones, uso de IA | `docs/postmortem.md` |
| 23:00 | Preguntas (2 min) | Sección 6 | — |

## 2. Preparación

### El día anterior

1. `git checkout main` y `git pull` (después de pasar `dev` a `main`).
2. Revisar que existan `.env` e `infra\alertmanager\discord_webhook` en la computadora de la demo.
3. Descargar todas las imágenes para no depender del internet de la universidad:

   ```powershell
   docker compose --profile carga pull
   ```

4. Ensayo completo cronometrado con este guion, **incluyendo** los 🔴 y 🟢 de Discord.
   **Este ensayo queda guardado como historia** (volúmenes de Prometheus, Tempo y Loki): en la
   demo hace de "semestre anterior" para el bloque 6. Anoten la hora en que lo corren.
5. Grabar el ensayo (Win + Alt + R con la Xbox Game Bar) y guardar capturas de cada bloque en
   `docs/plan-b/`. Es el plan B si algo falla en vivo.

### 15 minutos antes

```powershell
docker compose --profile carga down --remove-orphans   # SIN -v: así se conserva la historia del ensayo
docker compose up -d --build
docker compose ps        # 10 servicios en Up, postgres en healthy
```

Pestañas abiertas, en este orden (Ctrl + 1 a Ctrl + 6 para saltar entre ellas):

| # | Pestaña | Dirección |
|---|---|---|
| 1 | Portal | http://localhost:5173 |
| 2 | API (docs) | http://localhost:8000/docs |
| 3 | Dashboard | http://localhost:3000/d/asignaciones-sre |
| 4 | Alertas | http://localhost:9090/alerts |
| 5 | Discord | Canal del equipo |
| 6 | GitHub | Pestaña *Actions* del repositorio (CI en verde) |

Estado inicial (pestaña 2): **PUT /admin/flags** `{"modo_atomico": false}` y
**POST /admin/reiniciar** con `cupos` = 30. En la pestaña 4 no debe haber nada en *Firing*.

PowerShell con letra grande (Ctrl + rueda) y en la carpeta del proyecto. Zoom del navegador al 125%.

## 3. La demo, minuto a minuto (8 min)

Formato: **🗣 qué se dice**, **⌨ qué se hace**, **👀 qué debe verse**. Si lo que se ve no
coincide, ir a la sección 5.

### Bloque 1 · El sistema y un estudiante (0:00 – 1:30) · RF1, HU1

⌨ PowerShell: `docker compose ps`

🗣 *"Esta es la arquitectura del C4 corriendo de verdad: diez contenedores. Arriba la aplicación:
portal, API y PostgreSQL. Abajo la observabilidad: el Collector de OpenTelemetry, Prometheus,
Tempo, Loki, Alertmanager y Grafana."*

⌨ Pestaña 1 (portal). Carné `1102124` → **Asignar curso** en *Ingeniería de Software I*.

👀 Verde: *Asignación confirmada. Cupos restantes: 29*. La tabla baja a 29.

⌨ Clic otra vez en el mismo curso.

👀 Naranja: *El estudiante ya está asignado a este curso*. Sigue en 29.

⌨ Carné `abc` → **Asignar curso**.

👀 Rojo: *El carné debe tener de 7 a 10 dígitos…*

🗣 *"Ese es el caso de uso 1. Validamos en el portal para el usuario y otra vez en la API, porque
el portal no es una barrera de seguridad. Y si alguien intenta usar la API de administración
desde el portal…"*

⌨ En la barra de direcciones: `localhost:5173/api/admin/flags`

👀 **403 Forbidden**. *"…el proxy lo bloquea: es la mitigación del riesgo A01 de OWASP."*

### Bloque 2 · 500 estudiantes, 30 cupos (1:30 – 2:30) · RF2

⌨ Pestaña 2: **PUT /admin/flags** `{"modo_atomico": true}` → **POST /admin/reiniciar** `cupos` = 30.

⌨ PowerShell:

```powershell
docker compose run --rm k6 run /scripts/rf2_concurrencia.js
```

👀 En unos 2 s: `✓ asignadas_201: 30`, `✓ curso_lleno_409: 470`, `✓ otras_respuestas: 0`,
*Cupos finales del curso 1: 0*.

🗣 *"Quinientas solicitudes al mismo tiempo sobre treinta cupos: exactamente treinta asignados,
cero cupos negativos, nadie dos veces. Lo garantizan la instrucción atómica y dos restricciones de
la base de datos: `CHECK (cupos >= 0)` y `UNIQUE (estudiante, curso)`. El 93% de 'fallidas' que
dice k6 son los 409: curso lleno es la respuesta correcta."*

⌨ Dejar listo el bloque 3: **PUT /admin/flags** `{"modo_atomico": false}` → **POST /admin/reiniciar** `cupos` = 30.

### Bloque 3 · La avalancha y la detección (2:30 – 4:30) · RNF2, RNF3

⌨ Pestaña 3 (dashboard) a la vista. En PowerShell:

```powershell
docker compose run --rm k6
```

⏱ **Cronometrista: anotar la hora de inicio (T0).**

🗣 *"Ahora volvemos a la implementación inicial, la que tenía la universidad, y mandamos 200
estudiantes por segundo al mismo curso. Miren el dashboard: se refresca solo cada 5 segundos."*

👀 En ≤ 10 s aparece el tráfico (RNF2). Entre 20 y 60 s:

| Panel | Qué pasa |
|---|---|
| SLI de asignación | De verde a **rojo**, muy por debajo de 95% |
| Presupuesto de error | Cae a 0% |
| Latencia | El p95 cruza la línea de 2 s |
| Pool de conexiones | *En uso* = 10 y *esperando* sube |
| Alertas activas | De 0 a 4; en las gráficas aparecen franjas rojas (anotaciones) |

⌨ Pestaña 4 (alertas), recargar.

🗣 *"Fíjense en el orden. Primero avisan la predictiva y la de presupuesto: el pool se va a agotar
y el presupuesto de error se quema seis veces más rápido de lo sostenible. La reactiva, 'SLO
incumplido', llega después, y la de latencia confirma la tendencia. SRE no espera a que el
estudiante sufra."*

> El orden exacto puede variar unos segundos entre corridas; en el ensayo anoten el que salga y
> ajusten la frase.

⌨ Pestaña 5 (Discord).

👀 Los avisos 🔴 con severidad, resumen y enlace al dashboard.

⏱ **Cronometrista: anotar la hora del primer 🔴 en Discord (T1).**

🗣 *"Nadie estaba mirando el dashboard y el equipo ya se enteró: eso es RNF3."*

> La avalancha **sigue corriendo**. No se detiene hasta el bloque 5.

### Bloque 4 · Diagnóstico: ¿en qué capa falla? (4:30 – 6:00) · RNF1, HU2

⌨ Pestaña 3, panel **Trazas lentas (más de 2 s)** → clic en un **Trace ID**.

👀 Una traza de varios segundos. Casi todo el tiempo está en `db.pool.acquire` y `db.query`.

🗣 *"Esta es la pregunta que TI no podía responder. La petición tardó seis segundos y el servidor
web y la red casi no suman: el tiempo se va esperando una conexión libre del pool y esperando el
candado de la fila del curso. Y aquí está el porqué: en la implementación inicial las validaciones
(`validaciones`) se hacen con el candado tomado, así que todos hacen fila detrás del mismo curso."*

⌨ Clic en el span `POST /asignaciones` → **Logs for this span**.

👀 Loki abre el log JSON de esa misma petición, con el mismo `trace_id`, su `status` y su `duracion_ms`.

🗣 *"De la alerta a la causa raíz en menos de un minuto, sin entrar a ningún servidor. Más
hardware no lo arreglaba: con más conexiones habría más gente haciendo fila en el mismo candado."*

⏱ **Cronometrista: anotar la hora en que se aplica la corrección (T2)** (en el paso siguiente).

### Bloque 5 · Corrección y verificación (6:00 – 7:15) · RF2, RNF3

⌨ PowerShell: **Ctrl + C** para detener la avalancha.

⌨ Pestaña 2: **PUT /admin/flags** `{"modo_atomico": true}` → **Execute**. Luego
**POST /admin/reiniciar** `cupos` = 30.

🗣 *"La corrección es un feature flag: se activa en caliente, sin reiniciar ni desplegar. Valida
antes de tomar la conexión y descuenta con una sola instrucción, `UPDATE ... WHERE cupos > 0`,
así el candado dura milisegundos."*

⌨ PowerShell, la **misma** avalancha por 1 minuto:

```powershell
docker compose run --rm -e DURACION=1m k6
```

👀 Dashboard: *Modo de asignación activo* = **atomico**, franja verde de anotación, SLI de vuelta
en **verde**, p95 cerca de 0,1 s, pool sin espera.

👀 PowerShell al terminar: `http_req_failed: 0.00%` y el umbral `http_req_duration{esperado:si}` con ✓.

👀 Pestaña 4 y Discord (1 a 2 min): las alertas vuelven a *Inactive* y llegan los 🟢.

⏱ **Cronometrista: anotar la hora del 🟢 de `SLOAsignacionIncumplido` (T3).**

### Bloque 6 · La historia: de reaccionar a prevenir (7:15 – 8:00) · corrección del hito 1

> Para no pasarse de 8 minutos: la parte del **año simulado** (abajo) se puede contar mientras
> corre la avalancha corregida de 1 minuto del bloque 5, que de todos modos hay que esperar.

⌨ Dashboard: bajar a la fila **Historia y KPIs**. Arriba a la derecha, rango de tiempo
**Last 15 minutes**.

👀 Los KPIs de lo que acaba de pasar: *Cumplimiento del SLO en el periodo*, *Presupuesto de error
consumido* (más de 100%), *Pico de saturación del pool* (100%), *Tiempo con el SLO incumplido*, y
*SLI* y *p95 por modo*: **inicial** en rojo contra **atomico** en verde.

⌨ Cambiar el rango a **Last 2 days**.

👀 Aparece también el ensayo de ayer, con el mismo patrón.

🗣 *"Esto es lo que TI no tenía: historia. Los datos se guardan 400 días. Ayer, en el ensayo,
el sistema se rompió igual, a la misma carga y en la misma capa. Para la universidad, ese 'ayer'
es el semestre anterior: con este dato, antes de abrir la asignación se corre la prueba de carga,
se ve que el pool llega al 100% y se corrige antes de que llegue el primer estudiante. Eso es SRE
preventivo, no solo reactivo."*

⌨ Abrir el dashboard **Historia anual · datos simulados** (Dashboards → SRE).

👀 Un año de asignaciones: los picos de enero y julio, la tabla de días críticos (el día 1 de cada
ventana con SLI de 52% a 58%) y que Ingeniería genera el 42% del pico.

🗣 *"Y si tuviéramos un año de historia, así se vería (son datos simulados, con métricas aparte).
Los problemas no son al azar: siempre el día 1 de la asignación, de 7 a 9 de la mañana, con unas
210 peticiones por segundo, justo lo que reproduce nuestra avalancha. Con esto predecimos que el
lunes 11 de enero de 2027 hay que estar de guardia, ensayamos la semana anterior, y como
Ingeniería concentra el pico, proponemos escalonar la apertura por facultad: se reparte la carga
sin comprar hardware."*

> Opcional, si sobra tiempo: en la variable **Comparar con** (arriba a la izquierda) elegir `5m`.
> Las gráficas *ahora vs hace 5m* ponen la corrida corregida encima del incidente.

🗣 **Cierre:** *"Detectamos antes de que fallara, diagnosticamos con una traza, corregimos con un
flag sin reiniciar, verificamos con el mismo SLO y guardamos la historia para prevenir el próximo
pico. Y lo medimos: el equipo se enteró en __ segundos (MTTD, la meta era 60) y el servicio se
recuperó en __ (MTTR). Eso queda en nuestro postmortem."*

> Si el 🟢 tarda, no esperar en silencio: pasar a lecciones aprendidas y volver a mostrar Discord
> al final; para entonces ya habrá llegado.

## 4. KPIs del incidente (para el cierre y el postmortem)

| Hora | Qué es | Anotada |
|---|---|---|
| T0 | Inicio de la avalancha | |
| T1 | Primer 🔴 en Discord | |
| T2 | Se activa `modo_atomico` | |
| T3 | 🟢 de `SLOAsignacionIncumplido` | |

- **MTTD** (tiempo de detección) = T1 − T0. Meta del hito 1: ≤ 60 s.
- **MTTR** (tiempo de recuperación) = T3 − T1.

El panel *Tiempo con el SLO incumplido* de la fila **Historia y KPIs** da la duración del
incidente aunque el cronometrista se pierda alguna hora. Las horas exactas también quedan en
Alertmanager (http://localhost:9093) y en las anotaciones
del dashboard, por si el cronometrista se pierde alguna.

## 5. Si algo falla en vivo

| Síntoma | Qué hacer (en ≤ 15 s) |
|---|---|
| `docker compose run` no descarga k6 | No hay internet. Por eso el `pull` del día anterior. Pasar al video del plan B de ese bloque |
| RF2 da `asignadas_201: 0` y `curso_lleno_409: 500` | No se reinició el curso: **POST /admin/reiniciar** con 30 y repetir |
| RF2 con timeouts y `otras_respuestas` > 0 | Quedó el modo inicial: **PUT /admin/flags** `{"modo_atomico": true}`, reiniciar y repetir |
| **PUT /admin/flags** da 422 | En *Request body* solo `{"modo_atomico": true}`, en una línea |
| Dashboard en *No data* | Esperar 10 s y recargar |
| No llegan avisos a Discord | Mostrar las alertas en *Firing* en la pestaña 4 (el requisito se cumple igual en Alertmanager) y seguir; revisar después con `docker compose logs alertmanager --tail 20` |
| Panel de trazas lentas vacío | Explore → Tempo → Search → Service `api-asignaciones` → Duration `> 2s` → Run query |
| La computadora se pone muy lenta | `docker compose run --rm -e RPS=100 -e DURACION=1m k6` |
| Algo no responde | `docker compose ps`; si un servicio no está *Up*: `docker compose up -d` |

## 6. Preguntas probables y quién responde

| Pregunta | Responde | Idea clave de la respuesta |
|---|---|---|
| ¿Por qué el 409 cuenta como bueno en el SLI? | R4 | El sistema respondió bien y rápido; "curso lleno" es negocio, no falla. Si lo contáramos como malo, la alerta sonaría cada vez que un curso se llena |
| ¿Por qué 95% y 2 s? | R4 | Es la experiencia del estudiante, no el CPU. Deja un presupuesto de error de 5% para decidir entre confiabilidad y funciones nuevas |
| ¿Por qué no más conexiones en el pool? | R1 | Más conexiones = más gente esperando el mismo candado de fila. El cuello está en el diseño de la transacción, y la traza lo mostró |
| ¿Qué es un span y qué es el `trace_id`? | R3 | Un span es un paso con su duración; el `trace_id` une todos los pasos y los logs de una misma petición |
| ¿Cómo funciona la alerta predictiva? | R4 | `predict_linear` proyecta la tendencia de conexiones en uso 60 s hacia adelante; si llega al tamaño del pool, avisa antes |
| ¿Por qué OpenTelemetry y no la librería de Prometheus directo? | R3 | Un solo estándar para las tres señales; se cambia el backend sin tocar el código |
| ¿Por qué no microservicios? | R1 | Una sola funcionalidad; dividirla agregaría red y latencia sin beneficio. SRE indica con datos si un rediseño hace falta |
| ¿Qué pasa si se cae PostgreSQL? | R1 / R3 | La API responde 503 en `POOL_TIMEOUT_S` segundos en vez de colgarse, el SLI cae y la alerta avisa; la traza muestra el error en `db.pool.acquire` |
| ¿Cómo saben que el código sigue bien después de un cambio? | R5 | CI en GitHub Actions: pytest de RF1 en los dos modos, pruebas de promtool de las alertas y build, en cada pull request |
| ¿Qué riesgo de seguridad queda abierto? | R2 | No hay autenticación (fuera de alcance); en un sistema real el carné vendría del token institucional, no del cuerpo de la petición |
| ¿Cómo usaron la IA? | Cualquiera | Ver `docs/uso-ia-y-referencias.md`; todo lo presentado lo podemos explicar sin ella |
| ¿Para qué sirve guardar la historia? | R4 | Para comparar semestres, ver tendencias (un pool que cada vez se llena antes) y dimensionar capacidad con datos. Prometheus guarda 400 días; la fila *Historia y KPIs* los resume y la variable *Comparar con* superpone el pasado |
| En la traza, ¿qué es el hueco antes de `db.pool.acquire`? | R3 | La petición espera un hilo libre del servidor (FastAPI atiende las rutas síncronas con un grupo de hilos). Es la misma fila, una capa antes |
