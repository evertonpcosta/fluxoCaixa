from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total de requisições HTTP",
    ["service", "method", "endpoint", "status"],
)

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latência das requisições HTTP",
    ["service", "method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

EVENTS_PROCESSED = Counter(
    "consolidado_events_processed_total",
    "Eventos de lançamento processados com sucesso",
)

EVENTS_FAILED = Counter(
    "consolidado_events_failed_total",
    "Falhas ao processar eventos de lançamento",
)

SERVICE_NAME = "consolidado"
