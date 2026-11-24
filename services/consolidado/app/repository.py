from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain import EventoLancamento, aplicar_no_saldo
from app.models import EventoProcessadoModel, SaldoDiarioModel


def evento_ja_processado(db: Session, event_id) -> bool:
    return db.get(EventoProcessadoModel, event_id) is not None


def obter_saldo(db: Session, data_referencia: date) -> SaldoDiarioModel | None:
    return db.get(SaldoDiarioModel, data_referencia)


def processar_evento(db: Session, evento: EventoLancamento) -> bool:
    """Aplica evento no saldo. Retorna False se já processado (idempotente)."""
    if evento_ja_processado(db, evento.event_id):
        return False

    saldo_row = obter_saldo(db, evento.data_lancamento)
    saldo_atual = saldo_row.saldo if saldo_row else Decimal("0")
    novo_saldo = aplicar_no_saldo(saldo_atual, evento.tipo, evento.valor)
    agora = datetime.now(timezone.utc)

    if saldo_row is None:
        db.add(
            SaldoDiarioModel(
                data_referencia=evento.data_lancamento,
                saldo=novo_saldo,
                atualizado_em=agora,
            )
        )
    else:
        saldo_row.saldo = novo_saldo
        saldo_row.atualizado_em = agora

    db.add(
        EventoProcessadoModel(
            event_id=evento.event_id,
            lancamento_id=evento.lancamento_id,
            processado_em=agora,
        )
    )
    db.commit()
    return True


def listar_saldos(db: Session, limit: int = 30) -> list[SaldoDiarioModel]:
    stmt = (
        select(SaldoDiarioModel)
        .order_by(SaldoDiarioModel.data_referencia.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
