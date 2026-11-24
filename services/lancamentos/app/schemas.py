from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain import TipoLancamento


class LancamentoCreate(BaseModel):
    tipo: TipoLancamento
    valor: Decimal = Field(..., gt=0, max_digits=18, decimal_places=2)
    descricao: str = Field(default="", max_length=255)
    data_lancamento: date

    @field_validator("descricao")
    @classmethod
    def strip_descricao(cls, value: str) -> str:
        return (value or "").strip()


class LancamentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tipo: TipoLancamento
    valor: Decimal
    descricao: str
    data_lancamento: date
    criado_em: datetime


class LancamentoListResponse(BaseModel):
    items: list[LancamentoResponse]
    total: int
