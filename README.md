

## Estructura del proyecto

```
Sistema_Asignaciones/
├── api/                    API en Python (FastAPI)
│   ├── app/main.py         Código de la API
│   ├── Dockerfile          Cómo se construye el contenedor de la API
│   └── requirements.txt    Librerías de Python
├── portal/                 Portal del estudiante (React + Vite, servido con nginx)
│   ├── src/App.jsx         Pantalla principal
│   ├── Dockerfile          Cómo se construye el contenedor del portal
│   └── nginx.conf          Redirige /api/ hacia la API
├── db/
│   └── init.sql            Tablas y datos iniciales (se ejecuta al crear la base)
├── infra/                  Configuración de observabilidad
│   ├── otel-collector.yaml Rutas de la telemetría hacia Prometheus, Tempo y Loki
│   ├── prometheus/         Configuración y reglas de Prometheus
│   ├── alertmanager/       Configuración de las alertas
│   ├── grafana/            Fuentes de datos y dashboards de Grafana
│   ├── tempo.yaml          Configuración de Tempo
│   └── loki.yaml           Configuración de Loki
├── docker-compose.yml      Lista de todos los servicios y cómo se conectan
├── .env.example            Plantilla de configuración local
└── README.md               Esta guía
```

> `db/init.sql` solo se ejecuta la primera vez que se crea la base de datos. Si alguien lo
> cambia, cada integrante debe ejecutar `docker compose down -v` y luego
> `docker compose up -d --build` para recrearla.