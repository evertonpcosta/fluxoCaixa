import logging
import os
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import db
from app.db import init_db
from app.domain import LancamentoInvalido, normalizar_valor
from app.models import Lancamento, Outbox
from app.publisher import ciclo_publicacao, republicar_periodo
from app.schemas import LancamentoIn, LancamentoOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("lancamentos")


def exigir_chave(x_api_key: str | None = Header(default=None)) -> None:
    esperada = os.environ.get("API_KEY", "")
    if esperada and x_api_key != esperada:
        raise HTTPException(status_code=401, detail="chave de API inválida")


def get_session():
    session = db.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    parar = threading.Event()
    thread = threading.Thread(target=ciclo_publicacao, args=(parar,), name="outbox", daemon=True)
    thread.start()
    yield
    parar.set()
    thread.join(timeout=2)


app = FastAPI(title="Lançamentos", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "servico": "lancamentos"}


@app.get("/ready")
def ready():
    try:
        with db.engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="banco indisponível") from exc
    return {"status": "ready"}


@app.post(
    "/v1/lancamentos",
    response_model=LancamentoOut,
    status_code=201,
    dependencies=[Depends(exigir_chave)],
)
def criar(dados: LancamentoIn, session: Session = Depends(get_session)):
    try:
        valor = normalizar_valor(dados.valor)
    except LancamentoInvalido as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    lancamento = Lancamento(
        id=uuid.uuid4(),
        comerciante_id=dados.comerciante_id,
        tipo=dados.tipo.value,
        valor=valor,
        descricao=dados.descricao,
        data_lancamento=dados.data_lancamento,
        criado_em=datetime.now(timezone.utc),
    )
    payload = {
        "evento_id": str(lancamento.id),
        "lancamento_id": str(lancamento.id),
        "comerciante_id": str(lancamento.comerciante_id),
        "tipo": lancamento.tipo,
        "valor": f"{valor:.2f}",
        "descricao": lancamento.descricao,
        "data_lancamento": lancamento.data_lancamento.isoformat(),
    }
    session.add(lancamento)
    session.add(Outbox(id=uuid.uuid4(), lancamento_id=lancamento.id, payload=payload))
    session.flush()
    logger.info("lancamento registrado id=%s comerciante=%s", lancamento.id, lancamento.comerciante_id)
    return lancamento


@app.get(
    "/v1/lancamentos",
    response_model=list[LancamentoOut],
    dependencies=[Depends(exigir_chave)],
)
def listar(
    comerciante_id: uuid.UUID = Query(...),
    data_lancamento: date | None = Query(default=None),
    limite: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    consulta = select(Lancamento).where(Lancamento.comerciante_id == comerciante_id)
    if data_lancamento is not None:
        consulta = consulta.where(Lancamento.data_lancamento == data_lancamento)
    consulta = consulta.order_by(Lancamento.criado_em.desc()).limit(limite)
    return list(session.scalars(consulta))


class RepublicarIn(BaseModel):
    data_inicio: date
    data_fim: date


@app.post(
    "/v1/outbox/republicar",
    dependencies=[Depends(exigir_chave)],
)
def republicar(dados: RepublicarIn, session: Session = Depends(get_session)):
    if dados.data_fim < dados.data_inicio:
        raise HTTPException(status_code=422, detail="data_fim deve ser >= data_inicio")
    quantidade = republicar_periodo(session, dados.data_inicio, dados.data_fim)
    return {
        "marcados": quantidade,
        "data_inicio": dados.data_inicio.isoformat(),
        "data_fim": dados.data_fim.isoformat(),
    }
