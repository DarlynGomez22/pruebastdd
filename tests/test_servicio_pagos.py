import unittest
from decimal import Decimal
from unittest.mock import Mock

from pagos.excepciones import (MontoInvalidoError, PagoDuplicadoError,
                               PasarelaNoDisponibleError)
from pagos.modelos import EstadoPago, Pago, Pedido
from pagos.puertos import PasarelaPago, RepositorioPagos, RespuestaPasarela
from pagos.servicio import ServicioPagos


class BaseServicioPagos(unittest.TestCase):
    def setUp(self):
        # Dobles de las dependencias externas (nunca se toca red ni BD real)
        self.pasarela = Mock(spec=PasarelaPago)          # STUB (+ verificación puntual)
        self.repo = Mock(spec=RepositorioPagos)          # MOCK (se verifica interacción)
        self.repo.buscar_por_pedido.return_value = None  # STUB: no hay pago previo
        self.servicio = ServicioPagos(self.pasarela, self.repo)
        self.pedido = Pedido(id="P-1", cliente_id="C-9", monto=Decimal("100.00"))


class TestPagoAprobado(BaseServicioPagos):
    def setUp(self):
        super().setUp()
        self.pasarela.cobrar.return_value = RespuestaPasarela(True, "REF-1")

    def test_devuelve_pago_aprobado_con_referencia(self):
        pago = self.servicio.procesar_pago(self.pedido, "tok_123")
        self.assertEqual(pago.estado, EstadoPago.APROBADO)
        self.assertEqual(pago.referencia, "REF-1")

    def test_cobra_el_monto_del_pedido(self):
        # Actualizado por el cambio de requisito v2 (antes: 100.00 sin comisión)
        self.servicio.procesar_pago(self.pedido, "tok_123")
        self.pasarela.cobrar.assert_called_once_with(Decimal("102.50"), "tok_123")

    def test_persiste_el_pago_una_sola_vez(self):
        pago = self.servicio.procesar_pago(self.pedido, "tok_123")
        self.repo.guardar.assert_called_once_with(pago)



class TestMontoInvalido(BaseServicioPagos):
    def test_monto_cero_lanza_error_y_no_cobra(self):
        pedido = Pedido("P-2", "C-9", Decimal("0"))
        with self.assertRaises(MontoInvalidoError):
            self.servicio.procesar_pago(pedido, "tok_123")
        self.pasarela.cobrar.assert_not_called()
        self.repo.guardar.assert_not_called()

    def test_monto_negativo_lanza_error(self):
        pedido = Pedido("P-3", "C-9", Decimal("-5"))
        with self.assertRaises(MontoInvalidoError):
            self.servicio.procesar_pago(pedido, "tok_123")



class TestPagoRechazado(BaseServicioPagos):
    def setUp(self):
        super().setUp()
        self.pasarela.cobrar.return_value = RespuestaPasarela(
            False, None, "fondos insuficientes")

    def test_devuelve_pago_rechazado_con_motivo(self):
        pago = self.servicio.procesar_pago(self.pedido, "tok_123")
        self.assertEqual(pago.estado, EstadoPago.RECHAZADO)
        self.assertEqual(pago.detalle, "fondos insuficientes")

    def test_el_rechazo_tambien_se_persiste(self):
        pago = self.servicio.procesar_pago(self.pedido, "tok_123")
        self.repo.guardar.assert_called_once_with(pago)



class TestPasarelaCaida(BaseServicioPagos):
    def setUp(self):
        super().setUp()
        self.pasarela.cobrar.side_effect = ConnectionError("timeout")

    def test_lanza_error_de_dominio(self):
        with self.assertRaises(PasarelaNoDisponibleError):
            self.servicio.procesar_pago(self.pedido, "tok_123")

    def test_registra_el_intento_como_error_de_pasarela(self):
        with self.assertRaises(PasarelaNoDisponibleError):
            self.servicio.procesar_pago(self.pedido, "tok_123")
        self.repo.guardar.assert_called_once()
        guardado = self.repo.guardar.call_args.args[0]
        self.assertEqual(guardado.estado, EstadoPago.ERROR_PASARELA)



class TestPagoDuplicado(BaseServicioPagos):
    def test_no_cobra_dos_veces_un_pedido_ya_aprobado(self):
        self.repo.buscar_por_pedido.return_value = Pago(
            "P-1", Decimal("100.00"), EstadoPago.APROBADO, "REF-0")
        with self.assertRaises(PagoDuplicadoError):
            self.servicio.procesar_pago(self.pedido, "tok_123")
        self.pasarela.cobrar.assert_not_called()
        self.repo.guardar.assert_not_called()

    def test_un_pago_previo_rechazado_permite_reintentar(self):
        self.repo.buscar_por_pedido.return_value = Pago(
            "P-1", Decimal("100.00"), EstadoPago.RECHAZADO, detalle="fondos")
        self.pasarela.cobrar.return_value = RespuestaPasarela(True, "REF-2")
        pago = self.servicio.procesar_pago(self.pedido, "tok_123")
        self.assertEqual(pago.estado, EstadoPago.APROBADO)


class TestComision(BaseServicioPagos):
    """Requisito modificado (v2): se cobra monto + 2.5 % de comisión."""
    def setUp(self):
        super().setUp()
        self.pasarela.cobrar.return_value = RespuestaPasarela(True, "REF-1")

    def test_envia_a_la_pasarela_monto_mas_comision(self):
        self.servicio.procesar_pago(self.pedido, "tok_123")
        self.pasarela.cobrar.assert_called_once_with(Decimal("102.50"), "tok_123")

    def test_el_pago_registra_la_comision(self):
        pago = self.servicio.procesar_pago(self.pedido, "tok_123")
        self.assertEqual(pago.comision, Decimal("2.50"))
        self.assertEqual(pago.monto, Decimal("100.00"))


if __name__ == "__main__":
    unittest.main()
