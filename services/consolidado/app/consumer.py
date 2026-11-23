import json
import logging
import os
import threading
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import redis
from sqlalchemy import text

from app import db
from app.domain import delta_do_lancamento

logger = logging.getLogger(__name__)

STREAM = "fluxo.lancamentos"
GROUP = "consolidado"
DLQ = "fluxo.lancamentos.dlq"


def cliente_redis() -> redis.Redis:
    url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    return redis.Redis.from_url(url, decode_responses=True)


def garantir_grupo(cliente: redis.Redis) -> None:
    try:
        cliente.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def processar_evento(session, evento: dict) -> None:
    evento_id = str(uuid.UUID(evento["evento_id"]))
    comerciante_id = str(uuid.UUID(evento["comerciante_id"]))
    data_lancamento = date.fromisoformat(evento["data_lancamento"])
    valor = Decimal(evento["valor"])
    delta = delta_do_lancamento(evento["tipo"], valor)
    agora = datetime.now(timezone.utc)

    inseriu = session.execute(
        text(
            """
            INSERT INTO eventos_processados (evento_id, processado_em)
            VALUES (CAST(:evento_id AS uuid), :agora)
            ON CONFLICT (evento_id) DO NOTHING
            RETURNING evento_id
            """
        ),
        {"evento_id": evento_id, "agora": agora},
    ).first()
    if inseriu is None:
        logger.info("evento repetido id=%s", evento_id)
        return

    session.execute(
        text(
            """
            INSERT INTO saldos_diarios (
                comerciante_id, data, total_creditos, total_debitos, saldo, atualizado_em
            ) VALUES (
                CAST(:comerciante_id AS uuid), :data, :creditos, :debitos, :saldo, :agora
            )
            ON CONFLICT (comerciante_id, data) DO UPDATE SET
                total_creditos = saldos_diarios.total_creditos + EXCLUDED.total_creditos,
                total_debitos = saldos_diarios.total_debitos + EXCLUDED.total_debitos,
                saldo = (saldos_diarios.total_creditos + EXCLUDED.total_creditos)
                      - (saldos_diarios.total_debitos + EXCLUDED.total_debitos),
                atualizado_em = EXCLUDED.atualizado_em
            """
        ),
        {
            "comerciante_id": comerciante_id,
            "data": data_lancamento,
            "creditos": delta.creditos,
            "debitos": delta.debitos,
            "saldo": delta.creditos - delta.debitos,
            "agora": agora,
        },
    )


def _mensagens(lote) -> list[tuple[str, dict]]:
    if not lote:
        return []
    mensagens: list[tuple[str, dict]] = []
    for _stream, itens in lote:
        mensagens.extend(itens)
    return mensagens


def reclamar_pendentes(cliente: redis.Redis, consumidor: str) -> list[tuple[str, dict]]:
    try:
        resultado = cliente.xautoclaim(STREAM, GROUP, consumidor, 3000, "0-0", count=20)
    except redis.ResponseError:
        return []
    if not resultado or len(resultado) < 2:
        return []
    return list(resultado[1] or [])


def ler_novas(cliente: redis.Redis, consumidor: str) -> list[tuple[str, dict]]:
    lote = cliente.xreadgroup(GROUP, consumidor, {STREAM: ">"}, count=20, block=2000)
    return _mensagens(lote)


def tratar_mensagem(cliente: redis.Redis, message_id: str, campos: dict) -> None:
    bruto = campos.get("data") or ""
    try:
        evento = json.loads(bruto)
        with db.SessionLocal() as session:
            processar_evento(session, evento)
            session.commit()
        cliente.xack(STREAM, GROUP, message_id)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.exception("evento inválido id=%s", message_id)
        cliente.xadd(DLQ, {"data": bruto, "erro": str(exc), "id": message_id})
        cliente.xack(STREAM, GROUP, message_id)
    except Exception:
        logger.exception("falha ao processar id=%s", message_id)


def ciclo_consumo(parar: threading.Event) -> None:
    consumidor = f"consolidado-{os.getpid()}"
    while not parar.is_set():
        try:
            cliente = cliente_redis()
            garantir_grupo(cliente)
            mensagens = reclamar_pendentes(cliente, consumidor)
            if not mensagens:
                mensagens = ler_novas(cliente, consumidor)
            for message_id, campos in mensagens:
                tratar_mensagem(cliente, message_id, campos)
        except Exception:
            logger.exception("fila indisponível")
            parar.wait(1)
