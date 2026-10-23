# Sistema de Asignaciones

como intalar, ejecutar y probar el prototipo 


Esta guía explica, paso a paso, cómo instalar, ejecutar y probar el prototipo en tu computadora.

**Antes de comenzar, tomar en cuenta**
- Los comandos están escritos para **PowerShell en Windows**, con permisos de administrador 
- Salvo que se indique otra cosa, los comandos se ejecutan **dentro de la carpeta del proyecto** (la carpeta `Sistema_Asignaciones`, donde está el archivo `docker-compose.yml`).
- Todo el sistema corre dentro de Docker. No hace falta instalar Python, Node.js ni PostgreSQL.


## 1. Requisitos

**Cómo revisar si la virtualización está activada:**

1. Presiona `Ctrl + Shift + Esc` para abrir el **Administrador de tareas**.
2. Ve a la pestaña **Rendimiento** y haz clic en **CPU**.
3. Abajo a la derecha busca **Virtualización**. Debe decir **Habilitado**.
4. Si dice *Deshabilitado*, hay que activarla en la BIOS del equipo (la opción se llama *Intel VT-x*, *Intel Virtualization Technology* o *AMD-V / SVM*, según el equipo).

### 1.2 Programas

| Programa | como instalarlo | Para qué se usa |
|---|---|---|
| WSL 2 | ejecutar en PowerShell `wsl --install` cuando termine, **reinicia la computadora**' | Base para Docker Desktop |
| Docker Desktop | [dockerdocs](https://docs.docker.com/desktop/setup/install/windows-install/) y sigue el numeral 2.1 | Levantar todo el sistema |
| Git | [Git](https://git-scm.com/book/es/v2/Inicio---Sobre-el-Control-de-Versiones-Instalación-de-Git) | Descargar el proyecto desde GitHub |
| Editor de texto | Bloc de notas o VS Code | Abrir archivos de configuración si hace falta |

### 1.3 Cuenta

Una cuenta de **GitHub** con acceso al repositorio ['Sistema_Asignaciones'](https://github.com/Estrellasaln0rte/Sistema_Asignaciones.git)

### 1.4 Puertos libres

El sistema usa estos puertos de tu computadora. Ningún otro programa debe estar usándolos:

| Puerto | Servicio |
|---|---|
| 3000 | Grafana |
| 3100 | Loki |
| 4317 y 4318 | OpenTelemetry Collector |
| 5173 | Portal |
| 5432 | PostgreSQL |
| 8000 | API |
| 9090 | Prometheus |
| 9093 | Alertmanager |

Para verificar que ningún otro programa esté ocupando estos puertos en tu máquina ejecuta en PowerShell y ejecuta 
```Get-NetTCPConnection -LocalPort 3000,3100,4317,4318,5173,5432,8000,9090,9093 -ErrorAction SilentlyContinue | Select-Object LocalPort, State, OwningProcess
```

Si la consola no devuelve nada, todos los puertos están libres.
Si aparece una tabla, la columna LocalPort indica el puerto ocupado y la columna OwningProcess muestra el identificador del proceso (PID) que lo está usando.

**Liberar un puerto ocupado:**
Para saber qué programa es el duño de ese PID, ejecuta en PowerShell `tasklist /FI "PID eq [Número_PID]"`, reemplaza [Número_PID] por el número que obtuviste en el paso anterior.

Puedes cerrar el programa manualmente o forzar su cierre desde la pestaña Detalles del Administrador de tareas de Windows buscando ese mismo PID.

---

## 2. Instalar los programas

### 2.1 Instalar Docker Desktop

1. Con **Docker Desktop for Windows (AMD64)** ya descargado.
2. Abre el instalador. Cuando pregunte, deja marcada la opción **Use WSL 2 instead of Hyper-V**.
3. Al terminar, reinicia la computadora si lo pide.
4. Abre **Docker Desktop** desde el menú Inicio. Acepta los términos. No es necesario iniciar sesión, puedes elegir *Skip*.
5. Espera a que abajo a la izquierda aparezca **Engine running** en verde.

> Docker Desktop debe estar **abierto** cada vez que quieras usar el sistema.

### 2.2 Comprobar la instalación

1. Abre una ventana nueva de PowerShell (no hace falta que sea como administrador).
2. Ejecuta uno por uno:

   ```powershell
   docker --version
   docker compose version
   git --version
   ```

3. Cada comando debe mostrar una versión, por ejemplo:

   ```powershell
   Docker version 27.3.1, build ce12230
   Docker Compose version v2.29.7
   git version 2.47.0.windows.1
   ```

4. Si alguno muestra un error como *"no se reconoce como nombre de un cmdlet"*, ese programa no quedó instalado. Cierra PowerShell, vuelve a instalarlo y abre PowerShell de nuevo.

---

## 3. Descargar el proyecto

1. Abre PowerShell.
2. Ve a la carpeta donde quieres guardar el proyecto. Por ejemplo, Documentos:

   ```powershell
   cd $HOME\Documents
   ```

3. Descarga el proyecto:

   ```powershell
   git clone https://github.com/Estrellasaln0rte/Sistema_Asignaciones.git
   ```

   Si es la primera vez que usas Git con GitHub, se abrirá una ventana para iniciar sesión.
   Inicia sesión con tu cuenta de GitHub.

4. Entra a la carpeta del proyecto:

   ```powershell
   cd Sistema_Asignaciones
   ```

5. Comprueba que estás en la carpeta correcta:

   ```powershell
   dir
   ```

   Debes ver, entre otros, `docker-compose.yml`, `README.md` y las carpetas `api`, `portal`,
   `infra` y `load-tests`.

> **A partir de aquí, todos los comandos se ejecutan dentro de esta carpeta.** Si cierras
> PowerShell, al abrirlo de nuevo vuelve a entrar con
> `cd $HOME\Documents\Sistema_Asignaciones`.

---

## 4. Configurar el proyecto

Solo hay que hacerlo una vez.

1. Crea tu archivo de configuración local copiando el de ejemplo:

   ```powershell
   Copy-Item .env.example .env
   ```

2. No hace falta cambiar nada en `.env`. Los valores que trae son los de la demo:

   | Variable | Valor | Qué significa |
   |---|---|---|
   | `POSTGRES_PASSWORD` | `app` | Contraseña de la base de datos local |
   | `POOL_SIZE` | `10` | Cuántas conexiones a la base de datos tiene la API. Es el límite que provoca el cuello de botella |
   | `POOL_TIMEOUT_S` | `5` | Segundos que una petición espera una conexión libre antes de fallar |
   | `MODO_ATOMICO` | `false` | Con qué modo arranca la API: `false` es la implementación inicial (lenta) y `true` la corrección |

> **Sobre las alertas de Discord:** no tienes que configurar nada. Si no hay webhook, el sistema
> funciona igual y las alertas se ven en Alertmanager (http://localhost:9093) y en Prometheus
> (http://localhost:9090/alerts). Las alertas a Discord se configuran en la computadora que hace
> la demo.

---

## 5. Levantar el sistema

1. Abre **Docker Desktop** y espera a que diga **Engine running**.
2. En PowerShell, dentro de la carpeta del proyecto, ejecuta:

   ```powershell
   docker compose up -d --build
   ```

   - `up` levanta los servicios.
   - `-d` los deja corriendo en segundo plano, para que puedas seguir usando PowerShell.
   - `--build` construye la API y el portal con el código actual.

3. **La primera vez tarda entre 5 y 15 minutos**, porque descarga las imágenes. Verás muchas
   líneas de descarga; es normal. Las siguientes veces tarda menos de un minuto.
4. Cuando termine, verás líneas como estas, todas con `Started` o `Healthy`:

   ```
   ✔ Container sistema_asignaciones-postgres-1   Healthy
   ✔ Container sistema_asignaciones-api-1        Started
   ✔ Container sistema_asignaciones-portal-1     Started
   ...
   ```

5. Comprueba que todo esté corriendo:

   ```powershell
   docker compose ps
   ```

   Deben aparecer estos **10 servicios** y en la columna `STATUS` todos deben decir `Up`:

   | Servicio | Qué hace |
   |---|---|
   | `postgres` | Base de datos de cursos y asignaciones |
   | `api` | Lógica de asignación (FastAPI) |
   | `portal` | Página del estudiante (React) |
   | `otel-collector` | Recibe la telemetría de la API y la reparte |
   | `prometheus` | Guarda las métricas y evalúa las alertas |
   | `postgres-exporter` | Saca métricas de PostgreSQL |
   | `tempo` | Guarda las trazas |
   | `loki` | Guarda los logs |
   | `alertmanager` | Envía las alertas |
   | `grafana` | Dashboard |

6. Espera unos 10 segundos más para que la API termine de arrancar antes de abrir las páginas.

---

## 6. Abrir las páginas del sistema

Abre cada dirección en el navegador:

| Página | Dirección | Qué debes ver |
|---|---|---|
| Portal del estudiante | http://localhost:5173 | Título *Asignación de cursos*, un campo *Carné* y una tabla con 3 cursos |
| Documentación de la API | http://localhost:8000/docs | Lista de operaciones (`POST /asignaciones`, `GET /cursos`, etc.) |
| Grafana | http://localhost:3000 | Página de inicio de Grafana (no pide usuario ni contraseña) |
| Prometheus, alertas | http://localhost:9090/alerts | Lista de reglas de alerta en verde (*Inactive*) |
| Alertmanager | http://localhost:9093 | Lista de alertas (vacía si no hay problemas) |

**Para abrir el dashboard en Grafana:**

1. Entra a http://localhost:3000.
2. En el menú de la izquierda (☰) haz clic en **Dashboards**.
3. Abre la carpeta **SRE** y luego **Asignaciones · SRE**.
4. El dashboard se actualiza solo cada 5 segundos. Al principio los paneles pueden decir
   *No data*: es normal, todavía no hay tráfico.

---

## 7. Cambiar el modo y reiniciar el curso

Varias pruebas piden cambiar el modo de asignación o reiniciar el curso. Se hace desde la
documentación de la API, sin escribir comandos.

### 7.1 Cambiar el modo

1. Entra a http://localhost:8000/docs.
2. Haz clic en la fila **PUT /admin/flags** para desplegarla.
3. Haz clic en el botón **Try it out** (a la derecha).
4. En el cuadro **Request body** borra todo lo que haya y escribe **solo una** de estas dos
   líneas, sin el texto de adelante:

   Para activar la **corrección**:

   ```json
   {"modo_atomico": true}
   ```

   Para volver a la **implementación inicial**:

   ```json
   {"modo_atomico": false}
   ```

   Si pegas las dos líneas o el texto "Para activar...", la respuesta será **Code 422**.
5. Haz clic en el botón azul **Execute**.
6. Baja hasta **Server response**. Debe decir **Code 200** y mostrar el modo nuevo, por ejemplo
   `{"modo_atomico": true}`.

Para ver qué modo está activo sin cambiarlo (en la misma página, en el navegador):

1. Haz clic en la fila verde **GET /admin/flags** para desplegarla (abrirla).
2. Haz clic en **Try it out** y luego en **Execute**. Aquí no se escribe nada.
3. En **Response body** verás `{"modo_atomico": true}` si está la corrección, o `false` si está
   la implementación inicial.

### 7.2 Reiniciar el curso

Esto borra todas las asignaciones del curso *Ingeniería de Software I* y le devuelve sus cupos.
Hazlo antes de cada prueba de carga.

1. En http://localhost:8000/docs haz clic en la fila **POST /admin/reiniciar** para desplegarla.
2. Haz clic en **Try it out**.
3. En el campo **cupos** deja el valor `30`.
4. Haz clic en **Execute**.
5. En **Server response** debe aparecer **Code 200** y `{"curso_id": 1, "cupos": 30}`.

---

## 8. Pruebas

### Prueba 1 · Asignación desde el portal

**Qué valida:** que un estudiante pueda asignarse a un curso y reciba la respuesta correcta en cada caso.

1. Reinicia el curso (paso 7.2).
2. Abre http://localhost:5173.
3. En **Carné** escribe `1102124`.
4. Haz clic en **Asignar curso** en la fila de *Ingeniería de Software I*.
   - **Esperado:** mensaje verde *Asignación confirmada. Cupos restantes: 29*, y en la tabla el
     curso pasa de 30 a 29 cupos.
5. Sin cambiar el carné, haz clic otra vez en **Asignar curso** en el mismo curso.
   - **Esperado:** mensaje *El estudiante ya está asignado a este curso*, y los cupos siguen en 29.
6. Borra el carné y haz clic en **Asignar curso**.
   - **Esperado:** mensaje rojo *Ingrese su carné*.

**Curso inexistente** (se prueba desde la documentación de la API):

1. En http://localhost:8000/docs haz clic en la fila **POST /asignaciones** para desplegarla y luego en **Try it out**.
2. En **Request body** escribe:

   ```json
   {"estudiante_id": "1102124", "curso_id": 99}
   ```

3. Haz clic en **Execute**.
   - **Esperado:** **Code 404** y `{"detalle": "Curso inexistente"}`.

### Prueba 2 · Concurrencia: 500 solicitudes al mismo tiempo

**Qué valida:** que aunque 500 estudiantes pidan el mismo curso a la vez, solo se asignen los
30 cupos que existen, nadie quede asignado dos veces y los cupos nunca queden negativos.

1. Cambia el modo a la corrección: `{"modo_atomico": true}` (paso 7.1).
2. Reinicia el curso con `cupos = 30` (paso 7.2).
3. En PowerShell ejecuta:

   ```powershell
   docker compose run --rm k6 run /scripts/rf2_concurrencia.js
   ```

   La primera vez descarga la imagen de k6 (unos segundos). La prueba en sí dura menos de 10 segundos.

4. Al final del resultado busca estas líneas:

   ```
   ✓ asignadas_201..................: 30
   ✓ curso_lleno_409................: 470
   ✓ otras_respuestas...............: 0
   ```

   y un poco más arriba:

   ```
   Cupos finales del curso 1: 0 (esperado 0)
   ```

5. **La prueba pasa si las tres líneas tienen ✓.** Si alguna tiene ✗, la prueba falló: anota
   los números y avisa al equipo.

### Prueba 3 · Avalancha, alerta y corrección (guion de la demo)

**Qué valida:** que el sistema detecte la saturación, avise, permita encontrar la causa con una
traza y se recupere al activar la corrección.

**Preparación:**

1. Abre el dashboard **Asignaciones · SRE** en Grafana (paso 6).
2. En otra pestaña abre http://localhost:9090/alerts.

#### Paso A · Provocar el problema

1. Cambia el modo a la implementación inicial: `{"modo_atomico": false}` (paso 7.1).
2. Reinicia el curso (paso 7.2).
3. En PowerShell lanza la avalancha:

   ```powershell
   docker compose run --rm k6
   ```

   Simula 200 estudiantes por segundo durante unos 3 minutos y medio. Deja PowerShell abierto
   mientras corre.

4. Mira el dashboard. Entre 10 y 60 segundos después deberías ver:

   | Panel | Qué pasa |
   |---|---|
   | SLI de asignación | Pasa a **rojo**, por debajo de 95% |
   | Presupuesto de error restante | Baja hacia 0% |
   | Latencia de asignación | La línea p95 sube por encima de la línea roja de 2 s |
   | Pool de conexiones | *En uso* llega a 10 y *esperando* sube |
   | Alertas activas | Pasa de 0 a 4 |

5. En http://localhost:9090/alerts recarga la página. Estas cuatro alertas pasan a **Firing**
   (rojo). El orden puede variar, pero las tres primeras suelen adelantarse a la última:
   - `PoolConexionesPorAgotarse` (predictiva)
   - `LatenciaP95EnAumento` (preventiva)
   - `PresupuestoErrorQuemaRapida` (preventiva)
   - `SLOAsignacionIncumplido` (reactiva)

#### Paso B · Encontrar la causa con una traza

1. En el dashboard baja hasta el panel **Trazas lentas (más de 2 s)**.
2. Haz clic en cualquier valor de la columna **Trace ID**. Se abre la traza a la derecha.
3. Observa las barras de cada paso. La mayor parte del tiempo está en:
   - `db.pool.acquire`: la petición esperando que se libere una conexión.
   - `db.query`: la petición esperando el candado de la fila del curso.

   El tiempo **no** está en el servidor web ni en la red. Esa es la causa raíz.
4. Para ver los logs de esa misma petición: haz clic en el paso `POST /asignaciones` y luego en
   el botón **Logs for this span**.

#### Paso C · Aplicar la corrección y verificar

1. Espera a que termine k6 o detenlo presionando `Ctrl + C` en PowerShell.
2. Cambia el modo a la corrección: `{"modo_atomico": true}` (paso 7.1).
3. Reinicia el curso (paso 7.2).
4. Lanza otra vez la avalancha:

   ```powershell
   docker compose run --rm k6
   ```

5. **Esperado** en el dashboard en el siguiente minuto:
   - El SLI vuelve a **verde**, por encima de 95%.
   - La latencia p95 queda muy por debajo de 2 s (alrededor de 0.1 s).
   - El pool de conexiones deja de saturarse.
6. En http://localhost:9090/alerts las alertas vuelven a **Inactive** (verde) en 1 a 5 minutos.
7. Al terminar, en PowerShell k6 debe mostrar `http_req_failed: 0.00%`.

#### Cambiar la carga (opcional)

Si tu computadora va lenta con 200 peticiones por segundo, usa una carga menor:

```powershell
docker compose run --rm -e RPS=100 -e DURACION=1m k6
```

- `RPS` = peticiones por segundo.
- `DURACION` = cuánto dura la carga máxima (por ejemplo `30s`, `1m`, `3m`).

---

## 9. Detener el sistema

Para apagar todo, conservando los datos:

```powershell
docker compose down
```

Para apagar todo y **borrar la base de datos** (la próxima vez arranca desde cero, con los cursos iniciales):

```powershell
docker compose down -v
```

Después puedes cerrar Docker Desktop.

---

## 10. Actualizar el proyecto

Cuando alguien del equipo suba cambios a GitHub:

1. Dentro de la carpeta del proyecto ejecuta:

   ```powershell
   git pull
   ```

2. Vuelve a levantar el sistema para que use el código nuevo:

   ```powershell
   docker compose up -d --build
   ```

---

## 11. Problemas comunes

| Lo que ves | Qué significa | Cómo resolverlo |
|---|---|---|
| `error during connect` o `Cannot connect to the Docker daemon` | Docker Desktop no está abierto | Abre Docker Desktop, espera **Engine running** y repite el comando |
| `no configuration file provided: not found` | No estás en la carpeta del proyecto | Ejecuta `cd $HOME\Documents\Sistema_Asignaciones` |
| `Bind for 0.0.0.0:5432 failed: port is already allocated` (u otro puerto) | Otro programa usa ese puerto | Cierra ese programa (ver 1.4) y ejecuta otra vez `docker compose up -d` |
| En `docker compose ps` falta algún servicio | Ese servicio se detuvo por un error | Ejecuta `docker compose logs <servicio>` y comparte el mensaje con el equipo |
| El portal dice *Sin conexión con el servidor* | La API todavía está arrancando | Espera 10 segundos y recarga la página |
| Los paneles de Grafana dicen *No data* | Todavía no hay tráfico | Haz una asignación en el portal o lanza k6 |
| El panel de trazas lentas está vacío | No hubo peticiones de más de 2 s | Es normal en modo corrección. Repite el paso A de la prueba 3 |
| El modo volvió a `false` solo | La API se reinició y tomó el valor de `MODO_ATOMICO` del `.env` | Vuelve a cambiarlo con el paso 7.1 |
| La computadora se pone muy lenta durante la avalancha | La carga es alta para el equipo | Usa una carga menor (ver *Cambiar la carga*) |
| `/salud` dice `"base_de_datos":"sin conexión"` | PostgreSQL no está listo | Revisa que `postgres` diga `healthy` en `docker compose ps` |
| `WSL 2 installation is incomplete` al abrir Docker Desktop | Falta WSL 2 | Ejecuta `wsl --install` (tabla 1.2) y reinicia |
