from .excepciones import MontoInvalidoError, PasarelaNoDisponibleError
from .modelos import EstadoPago, Pago


class ServicioPagos:
    def __init__(self, pasarela, repositorio):
        self._pasarela = pasarela
        self._repositorio = repositorio

    def procesar_pago(self, pedido, token_tarjeta):
        if pedido.monto <= 0:
            raise MontoInvalidoError("El monto debe ser mayor que cero")
        try:
            respuesta = self._pasarela.cobrar(pedido.monto, token_tarjeta)
        except ConnectionError as exc:
            self._repositorio.guardar(
                Pago(pedido.id, pedido.monto, EstadoPago.ERROR_PASARELA, detalle=str(exc)))
            raise PasarelaNoDisponibleError("La pasarela no respondió") from exc
        if respuesta.aprobada:
            pago = Pago(pedido.id, pedido.monto, EstadoPago.APROBADO, respuesta.referencia)
        else:
            pago = Pago(pedido.id, pedido.monto, EstadoPago.RECHAZADO, detalle=respuesta.motivo)
        self._repositorio.guardar(pago)
        return pago
