from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer


class SaldoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comerciante_id: UUID
    data: date
    total_creditos: Decimal
    total_debitos: Decimal
    saldo: Decimal
    atualizado_em: datetime | None

    @field_serializer("total_creditos", "total_debitos", "saldo")
    def serializar_dinheiro(self, valor: Decimal) -> str:
        return f"{valor:.2f}"
