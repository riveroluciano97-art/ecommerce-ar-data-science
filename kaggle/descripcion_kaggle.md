# Argentine E-commerce: 90-day Repurchase Prediction

**Synthetic** dataset of 7,617 purchases from a fictional Argentine multichannel e-commerce (own web store, Mercado Libre, Instagram Shop, WhatsApp), January 2025 – June 2026. Built for a supervised **binary classification** problem: will the customer buy again within 90 days?

## Why this dataset
Most e-commerce datasets ignore what makes LATAM retail different. This one bakes it in:
- Prices in Argentine pesos with a **monthly inflation index** (`indice_inflacion`) so you can deflate to constant pesos.
- **Marketplace commissions** that change over time (Mercado Libre goes from 14% to 17% in Oct-2025).
- **Hot Sale (May) and CyberMonday (Nov)** with aggressive discounts and event-driven customers.
- A category (Indumentaria) losing retention from March 2026.
- Installment payments (`cuotas`), a very Argentine feature.

## Target
`recompra_90d`: 1 if the customer purchased again within 90 days of this purchase, 0 otherwise. **NaN** when the 90-day window is truncated by the end of the period and no repurchase was observed (unknown, not negative). Positive rate: 42.1%.

## Leakage-safe design
Behavioural features (`compras_previas`, `dias_desde_ultima_compra`, `gasto_previo_acum`, `antiguedad_dias`) only use purchases **before** each row. The target only looks **forward**. Customer history is simulated from Jan-2024 so "old" customers have a real past.

## Columns (23)
`id_venta, fecha, id_cliente, provincia, fecha_alta_cliente, antiguedad_dias, compras_previas, dias_desde_ultima_compra, gasto_previo_acum, canal, comision_canal_pct, categoria, producto, precio_unitario, costo_unitario, cantidad, monto, descuento_pct, medio_pago, cuotas, es_evento, indice_inflacion, recompra_90d`

Full data dictionary and the generator script (seed 42, fully reproducible) live in the GitHub repo: https://github.com/riveroluciano97-art/ecommerce-ar-data-science

## Deliberate missing values
`dias_desde_ultima_compra` is NaN on first purchases; `medio_pago` has ~3% missing; `recompra_90d` is NaN for truncated windows. They're there so cleaning decisions have to be made and justified.

## Companion project
The same fictional business was analysed descriptively with SQL Server + Power BI (Data Analytics track, Coderhouse). This dataset is the predictive continuation.

*Author: Luciano · Synthetic data, declared as such · License CC0*
