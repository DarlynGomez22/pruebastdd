from .excepciones import (MontoInvalidoError, PagoDuplicadoError,
                          PasarelaNoDisponibleError)
from .modelos import EstadoPago, Pago, Pedido
from .puertos import PasarelaPago, RepositorioPagos, RespuestaPasarela


class ServicioPagos:
    """Orquesta el cobro de un pedido.

    Depende de abstracciones (PasarelaPago, RepositorioPagos), no de
    implementaciones concretas: inyección por constructor (DIP).
    """

    def __init__(self, pasarela: PasarelaPago, repositorio: RepositorioPagos):
        self._pasarela = pasarela
        self._repositorio = repositorio

    def procesar_pago(self, pedido: Pedido, token_tarjeta: str) -> Pago:
        self._validar_monto(pedido)
        self._validar_no_duplicado(pedido)
        respuesta = self._cobrar(pedido, token_tarjeta)
        return self._registrar(self._construir_pago(pedido, respuesta))

    # --- pasos privados: cada uno con una única razón de cambio ---
    @staticmethod
    def _validar_monto(pedido: Pedido) -> None:
        if pedido.monto <= 0:
            raise MontoInvalidoError("El monto debe ser mayor que cero")

    def _validar_no_duplicado(self, pedido: Pedido) -> None:
        previo = self._repositorio.buscar_por_pedido(pedido.id)
        if previo is not None and previo.estado == EstadoPago.APROBADO:
            raise PagoDuplicadoError(f"El pedido {pedido.id} ya fue pagado")

    def _cobrar(self, pedido: Pedido, token_tarjeta: str) -> RespuestaPasarela:
        try:
            return self._pasarela.cobrar(pedido.monto, token_tarjeta)
        except ConnectionError as exc:
            self._registrar(Pago(pedido.id, pedido.monto,
                                 EstadoPago.ERROR_PASARELA, detalle=str(exc)))
            raise PasarelaNoDisponibleError("La pasarela no respondió") from exc

    @staticmethod
    def _construir_pago(pedido: Pedido, respuesta: RespuestaPasarela) -> Pago:
        if respuesta.aprobada:
            return Pago(pedido.id, pedido.monto, EstadoPago.APROBADO, respuesta.referencia)
        return Pago(pedido.id, pedido.monto, EstadoPago.RECHAZADO, detalle=respuesta.motivo)

    def _registrar(self, pago: Pago) -> Pago:
        self._repositorio.guardar(pago)
        return pago
