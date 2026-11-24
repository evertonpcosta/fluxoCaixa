from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain import (
    DomainError,
    TipoLancamento,
    aplicar_no_saldo,
    parse_evento,
)


def test_credito_soma():
    assert aplicar_no_saldo(Decimal("10"), TipoLancamento.CREDITO, Decimal("2.5")) == Decimal(
        "12.50"
    )


def test_debito_subtrai():
    assert aplicar_no_saldo(Decimal("10"), TipoLancamento.DEBITO, Decimal("3")) == Decimal(
        "7.00"
    )


def test_parse_evento_ok():
    event_id = uuid4()
    lancamento_id = uuid4()
    evento = parse_evento(
        {
            "event_id": str(event_id),
            "lancamento_id": str(lancamento_id),
            "tipo": "CREDITO",
            "valor": "15.00",
            "data_lancamento": "2026-11-24",
        }
    )
    assert evento.event_id == event_id
    assert evento.tipo is TipoLancamento.CREDITO
    assert evento.data_lancamento == date(2026, 11, 24)


def test_parse_evento_invalido():
    with pytest.raises(DomainError):
        parse_evento({"tipo": "CREDITO"})


def test_parse_evento_valor_zero():
    with pytest.raises(DomainError, match="maior que zero"):
        parse_evento(
            {
                "event_id": str(uuid4()),
                "lancamento_id": str(uuid4()),
                "tipo": "DEBITO",
                "valor": "0",
                "data_lancamento": "2026-11-24",
            }
        )
