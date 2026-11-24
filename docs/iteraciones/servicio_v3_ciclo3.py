from .excepciones import MontoInvalidoError
from .modelos import EstadoPago, Pago


class ServicioPagos:
    def __init__(self, pasarela, repositorio):
        self._pasarela = pasarela
        self._repositorio = repositorio

    def procesar_pago(self, pedido, token_tarjeta):
        if pedido.monto <= 0:
            raise MontoInvalidoError("El monto debe ser mayor que cero")
        respuesta = self._pasarela.cobrar(pedido.monto, token_tarjeta)
        if respuesta.aprobada:
            pago = Pago(pedido.id, pedido.monto, EstadoPago.APROBADO, respuesta.referencia)
        else:
            pago = Pago(pedido.id, pedido.monto, EstadoPago.RECHAZADO, detalle=respuesta.motivo)
        self._repositorio.guardar(pago)
        return pago
