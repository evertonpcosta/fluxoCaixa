from datetime import date
from decimal import Decimal

import pytest

from app.domain import DomainError, TipoLancamento, validar_novo_lancamento


def test_valida_credito_ok():
    novo = validar_novo_lancamento(
        "CREDITO",
        Decimal("10.5"),
        "  venda  ",
        date(2026, 11, 24),
    )
    assert novo.tipo is TipoLancamento.CREDITO
    assert novo.valor == Decimal("10.50")
    assert novo.descricao == "venda"


def test_valida_debito_ok():
    novo = validar_novo_lancamento(
        "DEBITO",
        Decimal("1"),
        "compra",
        date(2026, 11, 24),
    )
    assert novo.tipo is TipoLancamento.DEBITO


def test_rejeita_tipo_invalido():
    with pytest.raises(DomainError, match="CREDITO ou DEBITO"):
        validar_novo_lancamento("PIX", Decimal("10"), "x", date(2026, 11, 24))


@pytest.mark.parametrize("valor", [Decimal("0"), Decimal("-1")])
def test_rejeita_valor_nao_positivo(valor: Decimal):
    with pytest.raises(DomainError, match="maior que zero"):
        validar_novo_lancamento("CREDITO", valor, "x", date(2026, 11, 24))


def test_rejeita_descricao_longa():
    with pytest.raises(DomainError, match="255"):
        validar_novo_lancamento(
            "CREDITO",
            Decimal("10"),
            "x" * 256,
            date(2026, 11, 24),
        )
