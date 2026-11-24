import logging
import time
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.domain import DomainError
from app.logging_config import configure_logging
from app.metrics import HTTP_LATENCY, HTTP_REQUESTS, SERVICE_NAME
from app.publisher import publisher
from app.schemas import LancamentoCreate, LancamentoListResponse, LancamentoResponse
from app.service import criar_lancamento, obter_lancamentos

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="FluxoCaixa — Lançamentos", version="0.2.0")


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
    publisher.start()
    logger.info("Serviço de lançamentos iniciado")


@app.on_event("shutdown")
def on_shutdown() -> None:
    publisher.stop()


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
        "endpoints": [
            "POST /lancamentos",
            "GET /lancamentos",
            "GET /health",
            "GET /metrics",
        ],
    }


@app.post(
    "/lancamentos",
    response_model=LancamentoResponse,
    status_code=201,
)
def post_lancamento(
    body: LancamentoCreate,
    db: Session = Depends(get_db),
) -> LancamentoResponse:
    try:
        lancamento = criar_lancamento(
            db,
            tipo=body.tipo.value,
            valor=body.valor,
            descricao=body.descricao,
            data_lancamento=body.data_lancamento,
        )
    except DomainError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LancamentoResponse.model_validate(lancamento)


@app.get("/lancamentos", response_model=LancamentoListResponse)
def get_lancamentos(
    data: date | None = Query(default=None, description="Filtro por data (YYYY-MM-DD)"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> LancamentoListResponse:
    items, total = obter_lancamentos(db, data=data, limit=limit, offset=offset)
    return LancamentoListResponse(
        items=[LancamentoResponse.model_validate(i) for i in items],
        total=total,
    )
