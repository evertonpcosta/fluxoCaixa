from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import LancamentoCreate


def test_schema_aceita_payload_valido():
    body = LancamentoCreate(
        tipo="CREDITO",
        valor=Decimal("99.99"),
        descricao="teste",
        data_lancamento=date(2026, 11, 24),
    )
    assert body.tipo.value == "CREDITO"


def test_schema_rejeita_valor_zero():
    with pytest.raises(ValidationError):
        LancamentoCreate(
            tipo="DEBITO",
            valor=Decimal("0"),
            descricao="x",
            data_lancamento=date(2026, 11, 24),
        )
