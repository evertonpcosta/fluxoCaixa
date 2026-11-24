from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain import parse_evento
from app.repository import obter_saldo, processar_evento
from app.schemas import SaldoResponse


def consultar_saldo(db: Session, data_referencia: date) -> SaldoResponse:
    row = obter_saldo(db, data_referencia)
    if row is None:
        return SaldoResponse(
            data=data_referencia,
            saldo=Decimal("0.00"),
            atualizado_em=None,
            encontrado=False,
        )
    return SaldoResponse(
        data=row.data_referencia,
        saldo=row.saldo,
        atualizado_em=row.atualizado_em,
        encontrado=True,
    )


def aplicar_evento_payload(db: Session, payload: dict) -> bool:
    evento = parse_evento(payload)
    return processar_evento(db, evento)
