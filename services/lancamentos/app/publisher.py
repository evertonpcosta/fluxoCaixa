import json
import logging
import os
import threading
from datetime import date, datetime, timezone

import redis
from sqlalchemy import select

from app import db
from app.models import Lancamento, Outbox

logger = logging.getLogger(__name__)

STREAM = "fluxo.lancamentos"


def cliente_redis() -> redis.Redis:
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


def publicar_pendentes(cliente: redis.Redis) -> int:
    publicados = 0
    with db.SessionLocal() as session:
        pendentes = session.scalars(
            select(Outbox)
            .where(Outbox.publicado_em.is_(None))
            .limit(50)
            .with_for_update(skip_locked=True)
        ).all()
        for item in pendentes:
            # Sem MAXLEN: a fonte de verdade é a outbox. Se a fila for truncada,
            # republicar pelo período reconstrói o stream a partir do banco.
            cliente.xadd(STREAM, {"data": json.dumps(item.payload)})
            item.publicado_em = datetime.now(timezone.utc)
            publicados += 1
        session.commit()
    return publicados


def republicar_periodo(session, data_inicio: date, data_fim: date) -> int:
    linhas = session.scalars(
        select(Outbox)
        .join(Lancamento, Lancamento.id == Outbox.lancamento_id)
        .where(Lancamento.data_lancamento >= data_inicio)
        .where(Lancamento.data_lancamento <= data_fim)
        .order_by(Lancamento.criado_em)
    ).all()
    for item in linhas:
        item.publicado_em = None
    session.flush()
    return len(linhas)


def ciclo_publicacao(parar: threading.Event) -> None:
    while not parar.is_set():
        try:
            quantidade = publicar_pendentes(cliente_redis())
            if quantidade:
                logger.info("publicados=%s", quantidade)
        except Exception:
            logger.exception("falha ao publicar outbox")
        parar.wait(0.5)
