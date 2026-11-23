import unittest
from decimal import Decimal

from app.domain import LancamentoInvalido, normalizar_valor


class NormalizarValorTest(unittest.TestCase):
    def test_aceita_valor_inteiro_e_normaliza_centavos(self):
        self.assertEqual(normalizar_valor(Decimal("10")), Decimal("10.00"))

    def test_aceita_valor_com_duas_casas(self):
        self.assertEqual(normalizar_valor(Decimal("10.50")), Decimal("10.50"))

    def test_rejeita_zero(self):
        with self.assertRaises(LancamentoInvalido):
            normalizar_valor(Decimal("0"))

    def test_rejeita_negativo(self):
        with self.assertRaises(LancamentoInvalido):
            normalizar_valor(Decimal("-1.00"))

    def test_rejeita_mais_de_duas_casas(self):
        with self.assertRaises(LancamentoInvalido):
            normalizar_valor(Decimal("1.005"))


if __name__ == "__main__":
    unittest.main()
