from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.domain import NovoLancamento
from app.models import LancamentoModel, OutboxModel


def criar_lancamento_com_outbox(db: Session, novo: NovoLancamento) -> LancamentoModel:
    lancamento = LancamentoModel(
        id=uuid4(),
        tipo=novo.tipo.value,
        valor=novo.valor,
        descricao=novo.descricao,
        data_lancamento=novo.data_lancamento,
    )
    event_id = uuid4()
    payload = {
        "event_id": str(event_id),
        "event_type": "LancamentoCriado",
        "lancamento_id": str(lancamento.id),
        "tipo": lancamento.tipo,
        "valor": str(lancamento.valor),
        "descricao": lancamento.descricao,
        "data_lancamento": lancamento.data_lancamento.isoformat(),
    }
    outbox = OutboxModel(
        id=uuid4(),
        event_id=event_id,
        event_type="LancamentoCriado",
        payload=payload,
    )
    db.add(lancamento)
    db.add(outbox)
    db.commit()
    db.refresh(lancamento)
    return lancamento


def listar_lancamentos(
    db: Session,
    data: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[LancamentoModel], int]:
    stmt: Select = select(LancamentoModel).order_by(
        LancamentoModel.data_lancamento.desc(),
        LancamentoModel.criado_em.desc(),
    )
    count_stmt = select(func.count()).select_from(LancamentoModel)

    if data is not None:
        stmt = stmt.where(LancamentoModel.data_lancamento == data)
        count_stmt = count_stmt.where(LancamentoModel.data_lancamento == data)

    total = db.scalar(count_stmt) or 0
    items = list(db.scalars(stmt.limit(limit).offset(offset)).all())
    return items, total


def contar_outbox_pendentes(db: Session) -> int:
    stmt = select(func.count()).select_from(OutboxModel).where(
        OutboxModel.publicado_em.is_(None)
    )
    return db.scalar(stmt) or 0


def listar_outbox_pendentes(db: Session, limit: int = 50) -> list[OutboxModel]:
    stmt = (
        select(OutboxModel)
        .where(OutboxModel.publicado_em.is_(None))
        .order_by(OutboxModel.criado_em.asc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def marcar_outbox_publicado(db: Session, outbox_id: UUID) -> None:
    outbox = db.get(OutboxModel, outbox_id)
    if outbox is None:
        return
    outbox.publicado_em = datetime.now(timezone.utc)
    db.commit()
