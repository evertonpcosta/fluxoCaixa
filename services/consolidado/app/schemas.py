from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SaldoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: date
    saldo: Decimal
    atualizado_em: datetime | None = None
    encontrado: bool = True
