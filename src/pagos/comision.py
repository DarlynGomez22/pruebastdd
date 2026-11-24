from decimal import ROUND_HALF_UP, Decimal


class CalculadoraComision:
    """Política de comisión (Strategy). Se inyecta: abierto a extensión (OCP)."""

    def __init__(self, porcentaje: Decimal):
        if porcentaje < 0:
            raise ValueError("El porcentaje no puede ser negativo")
        self._porcentaje = porcentaje

    def sobre(self, monto: Decimal) -> Decimal:
        return (monto * self._porcentaje).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
