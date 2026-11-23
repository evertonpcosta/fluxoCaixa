import logging
import os
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.consumer import ciclo_consumo
from app import db
from app.db import init_db
from app.models import SaldoDiario
from app.schemas import SaldoOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


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
    thread = threading.Thread(target=ciclo_consumo, args=(parar,), name="consumidor", daemon=True)
    thread.start()
    yield
    parar.set()
    thread.join(timeout=2)


app = FastAPI(title="Consolidado", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "servico": "consolidado"}


@app.get("/ready")
def ready():
    try:
        with db.engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="banco indisponível") from exc
    return {"status": "ready"}


@app.get(
    "/v1/saldos/{comerciante_id}",
    response_model=SaldoOut,
    dependencies=[Depends(exigir_chave)],
)
def consultar_saldo(
    comerciante_id: uuid.UUID,
    data: date = Query(...),
    session: Session = Depends(get_session),
):
    saldo = session.get(SaldoDiario, (comerciante_id, data))
    if saldo is None:
        return SaldoOut(
            comerciante_id=comerciante_id,
            data=data,
            total_creditos=Decimal("0.00"),
            total_debitos=Decimal("0.00"),
            saldo=Decimal("0.00"),
            atualizado_em=None,
        )
    return saldo
