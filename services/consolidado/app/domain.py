from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID


class TipoLancamento(str, Enum):
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"


class DomainError(ValueError):
    """Violação de regra de negócio no consolidado."""


@dataclass(frozen=True)
class EventoLancamento:
    event_id: UUID
    lancamento_id: UUID
    tipo: TipoLancamento
    valor: Decimal
    data_lancamento: date


def parse_evento(payload: dict) -> EventoLancamento:
    try:
        tipo = TipoLancamento(payload["tipo"])
        valor = Decimal(str(payload["valor"]))
        if valor <= 0:
            raise DomainError("valor do evento deve ser maior que zero")
        return EventoLancamento(
            event_id=UUID(str(payload["event_id"])),
            lancamento_id=UUID(str(payload["lancamento_id"])),
            tipo=tipo,
            valor=valor.quantize(Decimal("0.01")),
            data_lancamento=date.fromisoformat(payload["data_lancamento"]),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise DomainError(f"payload de evento inválido: {exc}") from exc


def aplicar_no_saldo(saldo_atual: Decimal, tipo: TipoLancamento, valor: Decimal) -> Decimal:
    atual = saldo_atual or Decimal("0")
    if tipo is TipoLancamento.CREDITO:
        return (atual + valor).quantize(Decimal("0.01"))
    if tipo is TipoLancamento.DEBITO:
        return (atual - valor).quantize(Decimal("0.01"))
    raise DomainError(f"tipo desconhecido: {tipo}")
