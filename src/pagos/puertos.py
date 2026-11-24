"""Puertos (abstracciones) de las dependencias externas: DIP."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .modelos import Pago


@dataclass(frozen=True)
class RespuestaPasarela:
    aprobada: bool
    referencia: Optional[str] = None
    motivo: Optional[str] = None


class PasarelaPago(ABC):
    @abstractmethod
    def cobrar(self, monto: Decimal, token_tarjeta: str) -> RespuestaPasarela: ...


class RepositorioPagos(ABC):
    @abstractmethod
    def guardar(self, pago: Pago) -> None: ...

    @abstractmethod
    def buscar_por_pedido(self, pedido_id: str) -> Optional[Pago]: ...
