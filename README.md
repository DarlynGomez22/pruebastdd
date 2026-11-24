# Módulo de Procesamiento de Pagos — TDD con dobles de prueba

Actividad: TDD (Red-Green-Refactor) + Mocks/Stubs + Pruebas de regresión.

## Ejecutar
    PYTHONPATH=src python3 -m unittest discover -s tests -v      # Linux/Mac
    set PYTHONPATH=src && python -m unittest discover -s tests -v # Windows (cmd)

## Estructura
    src/pagos/modelos.py      Entidades (Pedido, Pago, EstadoPago)
    src/pagos/puertos.py      Abstracciones de dependencias externas (PasarelaPago, RepositorioPagos)
    src/pagos/comision.py     Política de comisión (Strategy)
    src/pagos/servicio.py     ServicioPagos (lógica de negocio)
    tests/                    Pruebas unitarias con unittest.mock
    docs/informe_tecnico.md   Informe técnico
    docs/evidencias/          Salida de cada fase Red / Green / Regresión
    docs/iteraciones/         Versión del servicio tras cada ciclo
