import unittest
from decimal import Decimal

from app.domain import EventoConsolidacao, aplicar_eventos, delta_do_lancamento


class ConsolidacaoTest(unittest.TestCase):
    def test_saldo_e_credito_menos_debito(self):
        eventos = [
            EventoConsolidacao("1", "CREDITO", Decimal("100.00")),
            EventoConsolidacao("2", "DEBITO", Decimal("40.00")),
            EventoConsolidacao("3", "CREDITO", Decimal("10.50")),
        ]
        creditos, debitos, saldo = aplicar_eventos(eventos)
        self.assertEqual(creditos, Decimal("110.50"))
        self.assertEqual(debitos, Decimal("40.00"))
        self.assertEqual(saldo, Decimal("70.50"))

    def test_evento_repetido_nao_altera_o_saldo(self):
        eventos = [
            EventoConsolidacao("1", "CREDITO", Decimal("10.00")),
            EventoConsolidacao("1", "CREDITO", Decimal("10.00")),
            EventoConsolidacao("2", "DEBITO", Decimal("3.00")),
            EventoConsolidacao("2", "DEBITO", Decimal("3.00")),
        ]
        creditos, debitos, saldo = aplicar_eventos(eventos)
        self.assertEqual(creditos, Decimal("10.00"))
        self.assertEqual(debitos, Decimal("3.00"))
        self.assertEqual(saldo, Decimal("7.00"))

    def test_rejeita_tipo_desconhecido(self):
        with self.assertRaises(ValueError):
            delta_do_lancamento("PIX", Decimal("10.00"))

    def test_rejeita_valor_nao_positivo(self):
        with self.assertRaises(ValueError):
            delta_do_lancamento("CREDITO", Decimal("0"))


if __name__ == "__main__":
    unittest.main()
