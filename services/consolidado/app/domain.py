from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class TipoLancamento(str, Enum):
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"


@dataclass(frozen=True)
class Delta:
    creditos: Decimal
    debitos: Decimal


@dataclass(frozen=True)
class EventoConsolidacao:
    evento_id: str
    tipo: str
    valor: Decimal


def delta_do_lancamento(tipo: str, valor: Decimal) -> Delta:
    if valor <= 0:
        raise ValueError("valor deve ser maior que zero")
    if tipo == TipoLancamento.CREDITO:
        return Delta(creditos=valor, debitos=Decimal("0.00"))
    if tipo == TipoLancamento.DEBITO:
        return Delta(creditos=Decimal("0.00"), debitos=valor)
    raise ValueError("tipo de lançamento inválido")


def aplicar_eventos(eventos: list[EventoConsolidacao]) -> tuple[Decimal, Decimal, Decimal]:
    vistos: set[str] = set()
    creditos = Decimal("0.00")
    debitos = Decimal("0.00")
    for evento in eventos:
        if evento.evento_id in vistos:
            continue
        vistos.add(evento.evento_id)
        delta = delta_do_lancamento(evento.tipo, evento.valor)
        creditos += delta.creditos
        debitos += delta.debitos
    return creditos, debitos, creditos - debitos
