from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class TipoLancamento(str, Enum):
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"


class DomainError(ValueError):
    """Violação de regra de negócio."""


@dataclass(frozen=True)
class NovoLancamento:
    tipo: TipoLancamento
    valor: Decimal
    descricao: str
    data_lancamento: date


def validar_novo_lancamento(
    tipo: str,
    valor: Decimal,
    descricao: str,
    data_lancamento: date,
) -> NovoLancamento:
    try:
        tipo_enum = TipoLancamento(tipo)
    except ValueError as exc:
        raise DomainError("tipo deve ser CREDITO ou DEBITO") from exc

    if valor is None or valor <= 0:
        raise DomainError("valor deve ser maior que zero")

    if data_lancamento is None:
        raise DomainError("data_lancamento é obrigatória")

    descricao_limpa = (descricao or "").strip()
    if len(descricao_limpa) > 255:
        raise DomainError("descricao deve ter no máximo 255 caracteres")

    return NovoLancamento(
        tipo=tipo_enum,
        valor=valor.quantize(Decimal("0.01")),
        descricao=descricao_limpa,
        data_lancamento=data_lancamento,
    )
