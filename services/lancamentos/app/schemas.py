from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.domain import TipoLancamento


class LancamentoIn(BaseModel):
    comerciante_id: UUID
    tipo: TipoLancamento
    valor: Decimal
    descricao: str | None = Field(default=None, max_length=500)
    data_lancamento: date


class LancamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    comerciante_id: UUID
    tipo: TipoLancamento
    valor: Decimal
    descricao: str | None
    data_lancamento: date
    criado_em: datetime

    @field_serializer("valor")
    def serializar_valor(self, valor: Decimal) -> str:
        return f"{valor:.2f}"
