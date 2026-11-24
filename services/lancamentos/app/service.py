from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain import DomainError, validar_novo_lancamento
from app.models import LancamentoModel
from app.repository import criar_lancamento_com_outbox, listar_lancamentos


def criar_lancamento(
    db: Session,
    *,
    tipo: str,
    valor: Decimal,
    descricao: str,
    data_lancamento: date,
) -> LancamentoModel:
    try:
        novo = validar_novo_lancamento(tipo, valor, descricao, data_lancamento)
    except DomainError:
        raise
    return criar_lancamento_com_outbox(db, novo)


def obter_lancamentos(
    db: Session,
    *,
    data: date | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[LancamentoModel], int]:
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    return listar_lancamentos(db, data=data, limit=limit, offset=offset)
