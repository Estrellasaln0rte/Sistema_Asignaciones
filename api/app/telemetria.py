"""Instrumentación con OpenTelemetry: trazas, métricas y logs estructurados (RNF1).

Las tres señales salen por OTLP hacia el OpenTelemetry Collector, que las
enruta a Tempo (trazas), Prometheus (métricas) y Loki (logs).
"""

import json
import logging
import os

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.metrics import Observation
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import ExplicitBucketHistogramAggregation, View
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


# Atributos propios de LogRecord; lo demás viene de extra={...} en cada log.
_ATRIBUTOS_BASE = set(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Log JSON en stdout con el trace_id para correlacionar con la traza."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = trace.get_current_span().get_span_context()
        data = {
            "nivel": record.levelname,
            "mensaje": record.getMessage(),
            "logger": record.name,
            "trace_id": format(ctx.trace_id, "032x") if ctx.is_valid else None,
            "span_id": format(ctx.span_id, "016x") if ctx.is_valid else None,
        }
        data.update({k: v for k, v in vars(record).items() if k not in _ATRIBUTOS_BASE})
        return json.dumps(data, ensure_ascii=False)


def configurar_telemetria() -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "api-asignaciones")})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
    trace.set_tracer_provider(tracer_provider)

    # Exporta cada 5 s para que el dashboard refleje el tráfico en menos de 10 s (RNF2).
    reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint, insecure=True), export_interval_millis=5000)
    # Buckets en segundos alrededor del umbral de 2 s del SLO (los de defecto empiezan en 5).
    buckets = View(
        instrument_name="asignacion.duracion",
        aggregation=ExplicitBucketHistogramAggregation([0.05, 0.1, 0.25, 0.5, 1, 1.5, 2, 3, 5, 10]),
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader], views=[buckets]))

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True)))
    set_logger_provider(logger_provider)

    stdout = logging.StreamHandler()
    stdout.setFormatter(JsonFormatter())
    raiz = logging.getLogger()
    raiz.setLevel(logging.INFO)
    raiz.handlers = [stdout, LoggingHandler(logger_provider=logger_provider)]


# ---------- Métricas del SLI ----------
UMBRAL_SLO_S = 2.0

_meter = metrics.get_meter("asignaciones")
# asignaciones_total{sli="buena|mala|excluida", status, modo} alimenta el SLI en Prometheus.
_contador = _meter.create_counter("asignaciones", description="Solicitudes de asignación clasificadas para el SLI")
_duracion = _meter.create_histogram("asignacion.duracion", unit="s", description="Latencia de la asignación")


def clasificar_sli(status: int, segundos: float) -> str:
    """SLI del hito 1: 201 y 409 en menos de 2 s son buenas; lentas, 5xx o timeouts son malas;
    los errores del cliente (400, 404, 422) se excluyen."""
    if status in (400, 404, 422):
        return "excluida"
    if status in (201, 409) and segundos < UMBRAL_SLO_S:
        return "buena"
    return "mala"


def registrar_asignacion(status: int, segundos: float, modo: str) -> str:
    sli = clasificar_sli(status, segundos)
    atributos = {"sli": sli, "status": str(status), "modo": modo}
    _contador.add(1, atributos)
    _duracion.record(segundos, atributos)
    return sli


def observar_pool(pool, tamano: int) -> None:
    """Gauges del pool de conexiones: en uso, peticiones esperando y tamaño."""

    def _conexiones(_options):
        stats = pool.get_stats()
        yield Observation(stats.get("pool_size", 0) - stats.get("pool_available", 0), {"estado": "en_uso"})
        yield Observation(stats.get("requests_waiting", 0), {"estado": "esperando"})

    _meter.create_observable_gauge("db.pool.conexiones", callbacks=[_conexiones],
                                   description="Conexiones del pool en uso y peticiones esperando")
    _meter.create_observable_gauge("db.pool.tamano", callbacks=[lambda _o: [Observation(tamano)]])
