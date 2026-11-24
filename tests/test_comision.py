import unittest
from decimal import Decimal

from pagos.comision import CalculadoraComision


class TestCalculadoraComision(unittest.TestCase):
    def test_calcula_porcentaje_con_dos_decimales(self):
        self.assertEqual(CalculadoraComision(Decimal("0.025")).sobre(Decimal("100.00")),
                         Decimal("2.50"))

    def test_redondea_half_up(self):
        self.assertEqual(CalculadoraComision(Decimal("0.025")).sobre(Decimal("10.10")),
                         Decimal("0.25"))

    def test_porcentaje_negativo_es_invalido(self):
        with self.assertRaises(ValueError):
            CalculadoraComision(Decimal("-0.01"))
