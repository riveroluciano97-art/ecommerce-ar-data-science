# Diccionario de datos — `ventas_ds.csv`

Una fila = una compra. Período: enero 2025 – junio 2026. 7.617 filas, 23 columnas. Montos en pesos argentinos (ARS) nominales del momento de la compra.

## Identificación y tiempo

| Columna | Tipo | Descripción |
|---|---|---|
| `id_venta` | int | Identificador único de la compra, correlativo por fecha |
| `fecha` | date | Fecha de la compra (YYYY-MM-DD) |
| `id_cliente` | int | Identificador del cliente |
| `es_evento` | bool | `True` si la compra ocurrió en Hot Sale (mayo) o CyberMonday (noviembre) |
| `indice_inflacion` | float | Índice de precios acumulado del mes (base: enero 2025 = 1,045). Dividir `monto` por este índice da pesos constantes |

## Estado del cliente al momento de la compra (calculado solo con el pasado)

| Columna | Tipo | Descripción |
|---|---|---|
| `provincia` | categórica | Provincia del cliente |
| `fecha_alta_cliente` | date | Fecha de la primera compra del cliente (puede ser anterior a 2025) |
| `antiguedad_dias` | int | Días entre `fecha_alta_cliente` y `fecha`. 0 = primera compra |
| `compras_previas` | int | Cantidad de compras anteriores a esta. 0 = cliente nuevo |
| `dias_desde_ultima_compra` | float | Recencia: días desde la compra anterior. **NaN en la primera compra** (no existe compra anterior) |
| `gasto_previo_acum` | float | ARS nominales acumulados en compras anteriores. 0 en la primera compra |

## La compra

| Columna | Tipo | Descripción |
|---|---|---|
| `canal` | categórica | Tienda propia · Mercado Libre · Instagram Shop · WhatsApp |
| `comision_canal_pct` | float | Comisión del canal vigente en esa fecha (Mercado Libre pasa de 0,14 a 0,17 en octubre 2025) |
| `categoria` | categórica | Tecnología · Hogar · Indumentaria · Deportes · Belleza |
| `producto` | categórica | Nombre del producto (60 productos) |
| `precio_unitario` | float | Precio unitario ARS vigente a la fecha (incluye inflación) |
| `costo_unitario` | float | Costo unitario ARS |
| `cantidad` | int | Unidades compradas |
| `monto` | float | `cantidad × precio_unitario × (1 − descuento_pct)` |
| `descuento_pct` | float | Descuento aplicado (0 a 0,25) |
| `medio_pago` | categórica | Tarjeta de crédito · Tarjeta de débito · Transferencia · Billetera virtual. **~3% de nulos** (dato no informado) |
| `cuotas` | int | Cantidad de cuotas (1, 3, 6 o 12; solo >1 con tarjeta de crédito) |

## Target

| Columna | Tipo | Descripción |
|---|---|---|
| `recompra_90d` | int (0/1) | **1** si el cliente hizo al menos una compra en los 90 días posteriores a `fecha`; **0** si no. **NaN** cuando la ventana de 90 días queda truncada por el fin del período (compras posteriores al 1 de abril de 2026) y no se observó recompra: el resultado es desconocido, no negativo |

## Reglas de construcción

- Ninguna feature usa información posterior a `fecha` (anti-leakage).
- Las features de comportamiento se calculan con historia simulada desde enero 2024, por eso hay clientes con `compras_previas > 0` en enero 2025.
- Semilla fija `42`; el archivo se regenera idéntico con `scripts/generar_dataset_ds.py`.
