import logging
import time
from datetime import date

from fastapi import Depends, FastAPI, Query, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.config import settings
from app.consumer import consumer
from app.db import get_db
from app.logging_config import configure_logging
from app.metrics import HTTP_LATENCY, HTTP_REQUESTS, SERVICE_NAME
from app.schemas import SaldoResponse
from app.service import consultar_saldo

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="FluxoCaixa — Consolidado", version="0.2.0")


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


@app.on_event("startup")
def on_startup() -> None:
    consumer.start()
    logger.info("Serviço de consolidado iniciado")


@app.on_event("shutdown")
def on_shutdown() -> None:
    consumer.stop()


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
        "endpoints": ["GET /saldo", "GET /health", "GET /metrics"],
    }


@app.get("/saldo", response_model=SaldoResponse)
def get_saldo(
    data: date = Query(..., description="Data de referência (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> SaldoResponse:
    return consultar_saldo(db, data)
