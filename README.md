## Estructura del proyecto

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

### 2.3 Comprobar la instalación

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
   
---

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
4. El dashboard se actualiza solo cada 5 segundos. *No data*: todavía no hay tráfico.

---

## 7. Cambiar el modo y reiniciar el curso

Varias pruebas piden cambiar el modo de asignación o reiniciar el curso. Se hace desde la
documentación de la API, sin escribir comandos.

### 7.1 Cambiar el modo

1. Entra a http://localhost:8000/docs.
2. Haz clic en la fila **PUT /admin/flags** para desplegarla.
3. Haz clic en el botón **Try it out** (a la derecha).
4. En el cuadro **Request body** borra lo que haya y escribe:
   - Para la **corrección**: `{"modo_atomico": true}`
   - Para la **implementación inicial**: `{"modo_atomico": false}`
5. Haz clic en el botón azul **Execute**.
6. Baja hasta **Server response**. Debe decir **Code 200** y mostrar el modo nuevo, por ejemplo
   `{"modo_atomico": true}`.

Para ver qué modo está activo sin cambiarlo: despliega **GET /admin/flags**, haz clic en
**Try it out** y luego en **Execute**.

### 7.2 Reiniciar el curso

Esto borra todas las asignaciones del curso *Ingeniería de Software I* y le devuelve sus cupos.
Hazlo antes de cada prueba de carga.

1. En http://localhost:8000/docs despliega **POST /admin/reiniciar**.
2. Haz clic en **Try it out**.
3. En el campo **cupos** deja el valor `30`.
4. Haz clic en **Execute**.
5. En **Server response** debe aparecer **Code 200** y `{"curso_id": 1, "cupos": 30}`.
> `db/init.sql` solo se ejecuta la primera vez que se crea la base de datos. Si alguien lo
> cambia, cada integrante debe ejecutar `docker compose down -v` y luego
> `docker compose up -d --build` para recrearla.
