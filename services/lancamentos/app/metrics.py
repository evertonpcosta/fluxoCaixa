from prometheus_client import Counter, Gauge, Histogram

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

OUTBOX_PENDING = Gauge(
    "outbox_pending",
    "Quantidade de eventos pendentes no outbox",
)

PUBLISH_FAILURES = Counter(
    "outbox_publish_failures_total",
    "Falhas ao publicar eventos no broker",
)

SERVICE_NAME = "lancamentos"
