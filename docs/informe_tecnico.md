# Informe Técnico — TDD aplicado a un Módulo de Procesamiento de Pagos

**Asignatura:** Desarrollo basado en pruebas tdd
**Integrantes:** _[Darlyn Rafael Gomez Jimenez]_  **Fecha:** 23-11-2026
**Repositorio:** _[https://github.com/DarlynGomez22/pruebastdd.git]_
**Stack:** Python 3.12 · `unittest` · `unittest.mock`

---

## 1. Escenario

`ServicioPagos` cobra un `Pedido` a través de una **pasarela de pago de terceros** y registra el resultado en un **repositorio (base de datos)**. Ambas dependencias son externas, lentas y no deterministas, por lo que se aíslan con dobles de prueba.

Reglas de negocio (se descubrieron una por ciclo):

| Ciclo | Requisito | Tests |
|---|---|---|
| 1 | Un pedido válido se cobra y el pago queda `APROBADO` y persistido | 3 |
| 2 | Monto ≤ 0 → `MontoInvalidoError`, sin tocar pasarela ni BD | 2 |
| 3 | Si la pasarela rechaza → pago `RECHAZADO` con motivo, persistido | 2 |
| 4 | Si la pasarela no responde → `ERROR_PASARELA` registrado + `PasarelaNoDisponibleError` | 2 |
| 5 | Un pedido ya `APROBADO` no se cobra otra vez; uno `RECHAZADO` sí puede reintentarse | 2 |
| Regresión | Cambio de requisito: comisión del 2.5 % sobre el monto | 2 + 3 |

## 2. Ciclo Red-Green-Refactor (30 %)

En cada ciclo se escribió **primero** la prueba y se ejecutó para verlarla fallar (`docs/evidencias/cicloN_RED.txt`); después se escribió el código mínimo (`cicloN_GREEN.txt`). La evolución del servicio queda en `docs/iteraciones/servicio_v1…v7`.

| Ciclo | Resultado RED | Resultado GREEN |
|---|---|---|
| 1 | `ImportError`: no existía `pagos.servicio` (errors=1) | 3 tests OK |
| 2 | 2 failures (`MontoInvalidoError` no se lanzaba) | 5 tests OK |
| 3 | 1 failure (devolvía `APROBADO` siempre) | 7 tests OK |
| 4 | 2 errors (`ConnectionError` se propagaba sin traducir) | 9 tests OK |
| 5 | 1 failure (cobraba pedidos ya pagados) | 11 tests OK |
| Refactor | — | 11 tests OK (sin cambiar comportamiento) |

**Nota de honestidad:** en los ciclos 3 y 5 uno de los dos tests nuevos ya pasaba en RED, porque verifica una propiedad que el código previo ya cumplía (`guardar` se llama siempre; reintento tras rechazo). Se conservaron como tests de caracterización/protección.

**Código mínimo.** El ciclo 1 retornó siempre `APROBADO` sin validar nada (versión v1); cada rama se añadió solo cuando un test fallido la exigió.

**Refactor (v6).** `procesar_pago` pasó de un método con 4 responsabilidades mezcladas a un guion legible de 4 pasos (`_validar_monto`, `_validar_no_duplicado`, `_cobrar`, `_registrar`), con la barra verde antes y después (11/11).

## 3. Mocks y Stubs (25 %)

Se usó `Mock(spec=…)` sobre las **abstracciones** (`PasarelaPago`, `RepositorioPagos`). El `spec` hace que el doble falle si se invoca un método que la interfaz real no tiene, evitando tests que pasan contra una API inventada.

| Doble | Rol | Dónde | Justificación |
|---|---|---|---|
| `pasarela.cobrar.return_value = RespuestaPasarela(…)` | **Stub** | aprobado / rechazado | Solo aporta datos de entrada; no interesa *cómo* se llamó |
| `pasarela.cobrar.side_effect = ConnectionError` | **Stub** (error) | pasarela caída | Reproduce un fallo de red imposible de provocar de forma fiable con un servicio real |
| `repo.buscar_por_pedido.return_value = None / Pago(…)` | **Stub** | duplicados | Controla el estado previo de la BD |
| `repo.guardar.assert_called_once_with(pago)` | **Mock** | persistencia | El *efecto observable* del servicio es la escritura; se verifica la interacción |
| `pasarela.cobrar.assert_not_called()` | **Mock** (verificación negativa) | monto inválido, duplicado | Garantiza que **nunca se cobra** al cliente en esos casos (riesgo de negocio crítico) |
| `pasarela.cobrar.assert_called_once_with(monto, token)` | **Mock** | monto cobrado | Verifica el contrato con la pasarela |

Criterio aplicado: **stub para lo que entra, mock para lo que sale con efecto**. No se mockean las entidades (`Pedido`, `Pago`) ni `CalculadoraComision`, que son objetos de valor/lógica pura. Ningún test usa red ni BD real, por lo que la suite corre en ~5 ms y es determinista.

## 4. Diseño Orientado a Objetos (25 %)

- **S – Responsabilidad única:** `ServicioPagos` orquesta; `CalculadoraComision` solo calcula comisión; `modelos` solo contiene datos; los puertos solo declaran contratos.
- **O – Abierto/Cerrado:** la comisión se añadió **sin modificar la lógica de decisión** (solo se compuso una nueva colaboración). Cambiar a comisión escalonada = nueva clase con método `sobre`, sin tocar el servicio.
- **L – Liskov:** cualquier implementación de `PasarelaPago`/`RepositorioPagos` (Stripe, PayPal, SQL, memoria, mock con `spec`) es sustituible sin cambiar el servicio.
- **I – Segregación de interfaces:** dos puertos pequeños y separados (cobrar / persistir) en vez de uno grande.
- **D – Inversión de dependencias:** el servicio depende de abstracciones inyectadas por constructor; esto es lo que hace posible el aislamiento con dobles.
- **Cohesión alta / acoplamiento bajo:** el servicio no conoce SDKs ni SQL; `Pago` y `Pedido` son `dataclass(frozen=True)` (inmutables, sin efectos laterales).
- **Errores de dominio:** `ConnectionError` (detalle de infraestructura) se traduce a `PasarelaNoDisponibleError`, de modo que los llamadores no dependen de la librería HTTP usada.

## 5. Pruebas de regresión (20 %)

**Requisito modificado:** *"Todo cobro lleva una comisión del 2.5 % que se suma al monto enviado a la pasarela."*

Procedimiento:
1. Se escribieron los tests del nuevo requisito (RED): `regresion1_RED_nuevo_requisito.txt` → `failures=1, errors=2`.
2. Se implementó el cambio (`CalculadoraComision`, campo `Pago.comision`, `ServicioPagos` la usa) y se ejecutó **la batería completa (16 tests)**: `regresion2_tras_cambio_BATERIA_COMPLETA.txt` → `FAILED (failures=1)`.
3. **Análisis del fallo:** la única prueba que cayó fue `test_cobra_el_monto_del_pedido`, que codificaba el requisito anterior (`cobrar(100.00)`). Es un **fallo esperado por requisito obsoleto**, no un efecto colateral. Los otros **15 tests pasaron**: validación de monto, duplicados, rechazo, pasarela caída y persistencia siguen intactos.
4. Se actualizó esa aserción a `102.50` (comentada en el código) y se re-ejecutó todo: `regresion3_FINAL_GREEN.txt` → **16 tests, OK**.

La regresión demuestra dos cosas: (a) la suite detecta de inmediato qué comportamiento cambió, y (b) el cambio no rompió ninguna regla previa.

## 6. Resultado final

```
Ran 16 tests in 0.005s
OK
```

## 7. Conclusiones

- Escribir la prueba primero obligó a definir el contrato (qué devuelve, qué no debe llamarse) antes de decidir la implementación.
- La inyección de dependencias fue la decisión de diseño que habilitó todo el aislamiento.
- Los `assert_not_called` protegen el riesgo más caro del dominio: cobrar indebidamente a un cliente.
- Limitación: no hay tests de integración contra una pasarela/BD reales (fuera del alcance de la actividad; irían en una capa separada).

## 8. Capturas (Green bar)
![Barra verde](green.png)
![Fase roja](red.png)
