import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.metrics import HTTP_LATENCY, HTTP_REQUESTS, SERVICE_NAME

app = FastAPI(title="FluxoCaixa — Consolidado", version="0.1.0")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path in {"/metrics", "/health"}:
        return await call_next(request)

    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed = time.perf_counter() - start
    endpoint = request.url.path
    HTTP_REQUESTS.labels(
        SERVICE_NAME, request.method, endpoint, str(response.status_code)
    ).inc()
    HTTP_LATENCY.labels(SERVICE_NAME, request.method, endpoint).observe(elapsed)
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/")
def root() -> dict:
    return {
        "service": SERVICE_NAME,
        "message": "Esqueleto ativo. Endpoints de negócio na Etapa 5.",
    }
