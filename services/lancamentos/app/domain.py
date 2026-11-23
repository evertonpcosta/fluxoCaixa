from decimal import Decimal, InvalidOperation
from enum import Enum

CENTAVOS = Decimal("0.01")


class TipoLancamento(str, Enum):
    CREDITO = "CREDITO"
    DEBITO = "DEBITO"


class LancamentoInvalido(ValueError):
    pass


def normalizar_valor(valor: Decimal) -> Decimal:
    try:
        quantizado = Decimal(valor).quantize(CENTAVOS)
    except (InvalidOperation, ValueError) as exc:
        raise LancamentoInvalido("valor inválido") from exc
    if quantizado != Decimal(valor):
        raise LancamentoInvalido("valor deve ter no máximo 2 casas decimais")
    if quantizado <= 0:
        raise LancamentoInvalido("valor deve ser maior que zero")
    return quantizado
