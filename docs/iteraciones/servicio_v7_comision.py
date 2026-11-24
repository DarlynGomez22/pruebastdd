from decimal import Decimal

from .comision import CalculadoraComision
from .excepciones import (MontoInvalidoError, PagoDuplicadoError,
                          PasarelaNoDisponibleError)
from .modelos import EstadoPago, Pago, Pedido
from .puertos import PasarelaPago, RepositorioPagos, RespuestaPasarela


class ServicioPagos:
    """Orquesta el cobro de un pedido.

    Depende de abstracciones (PasarelaPago, RepositorioPagos), no de
    implementaciones concretas: inyección por constructor (DIP).
    """

    COMISION_POR_DEFECTO = Decimal("0.025")

    def __init__(self, pasarela: PasarelaPago, repositorio: RepositorioPagos,
                 calculadora: CalculadoraComision | None = None):
        self._pasarela = pasarela
        self._repositorio = repositorio
        self._calculadora = calculadora or CalculadoraComision(self.COMISION_POR_DEFECTO)

    def procesar_pago(self, pedido: Pedido, token_tarjeta: str) -> Pago:
        self._validar_monto(pedido)
        self._validar_no_duplicado(pedido)
        comision = self._calculadora.sobre(pedido.monto)
        respuesta = self._cobrar(pedido, comision, token_tarjeta)
        return self._registrar(self._construir_pago(pedido, comision, respuesta))

    # --- pasos privados: cada uno con una única razón de cambio ---
    @staticmethod
    def _validar_monto(pedido: Pedido) -> None:
        if pedido.monto <= 0:
            raise MontoInvalidoError("El monto debe ser mayor que cero")

    def _validar_no_duplicado(self, pedido: Pedido) -> None:
        previo = self._repositorio.buscar_por_pedido(pedido.id)
        if previo is not None and previo.estado == EstadoPago.APROBADO:
            raise PagoDuplicadoError(f"El pedido {pedido.id} ya fue pagado")

    def _cobrar(self, pedido: Pedido, comision: Decimal, token_tarjeta: str) -> RespuestaPasarela:
        try:
            return self._pasarela.cobrar(pedido.monto + comision, token_tarjeta)
        except ConnectionError as exc:
            self._registrar(Pago(pedido.id, pedido.monto,
                                 EstadoPago.ERROR_PASARELA, detalle=str(exc)))
            raise PasarelaNoDisponibleError("La pasarela no respondió") from exc

    @staticmethod
    def _construir_pago(pedido: Pedido, comision: Decimal,
                        respuesta: RespuestaPasarela) -> Pago:
        if respuesta.aprobada:
            return Pago(pedido.id, pedido.monto, EstadoPago.APROBADO,
                        respuesta.referencia, comision=comision)
        return Pago(pedido.id, pedido.monto, EstadoPago.RECHAZADO,
                    detalle=respuesta.motivo, comision=comision)

    def _registrar(self, pago: Pago) -> Pago:
        self._repositorio.guardar(pago)
        return pago
