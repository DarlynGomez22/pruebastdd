from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional


class EstadoPago(Enum):
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    ERROR_PASARELA = "ERROR_PASARELA"


@dataclass(frozen=True)
class Pedido:
    id: str
    cliente_id: str
    monto: Decimal


@dataclass(frozen=True)
class Pago:
    pedido_id: str
    monto: Decimal
    estado: EstadoPago
    referencia: Optional[str] = None
    detalle: Optional[str] = None
    comision: Decimal = Decimal("0.00")
