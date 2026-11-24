from .modelos import EstadoPago, Pago


class ServicioPagos:
    def __init__(self, pasarela, repositorio):
        self._pasarela = pasarela
        self._repositorio = repositorio

    def procesar_pago(self, pedido, token_tarjeta):
        respuesta = self._pasarela.cobrar(pedido.monto, token_tarjeta)
        pago = Pago(pedido.id, pedido.monto, EstadoPago.APROBADO, respuesta.referencia)
        self._repositorio.guardar(pago)
        return pago
