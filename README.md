# Predicción de recompra en un e-commerce argentino

Un e-commerce argentino multicanal (tienda propia, Mercado Libre, Instagram Shop y WhatsApp) ya sabe que sus clientes recurrentes gastan ~25% más por ticket que los nuevos. Lo que no sabe es **qué clientes van a volver a comprar en los próximos 90 días** y, por lo tanto, a quién conviene dirigir el presupuesto de retención. Este proyecto construye un dataset de 7.617 compras con features de comportamiento del cliente y un target `recompra_90d`, y lo usa para responder esa pregunta con machine learning.

> Proyecto de la carrera de **Data Science** en Coderhouse. Es la continuación en clave predictiva del proyecto de Data Analytics sobre el mismo negocio (SQL Server + Power BI). Aquel respondía *qué pasó*; este responde *qué va a pasar y qué hacer*.

## Proyecto final

**Notebook completo:** [`notebooks/proyecto_final_recompra.ipynb`](notebooks/proyecto_final_recompra.ipynb) · [abrir en Colab](https://colab.research.google.com/github/riveroluciano97-art/ecommerce-ar-data-science/blob/main/notebooks/proyecto_final_recompra.ipynb)

| Resultado en test | Accuracy | ROC-AUC |
|---|---|---|
| Clase mayoritaria | 59,8% | 0,500 |
| Regla "si ya compró antes, vuelve" | 66,6% | 0,670 |
| **Regresión logística (modelo elegido)** | **74,3%** | **0,785** |

- El modelo ordena bien: en el 20% de compras con mayor probabilidad predicha vuelve el 82,1% de los clientes; en el 20% más bajo, el 14,7%.
- Recomendación: no regalar margen en la zona de probabilidad alta, concentrar el presupuesto de retención en la zona media y medirlo con un grupo de control.
- Lo que el modelo no hace: con el umbral de 0,5 no supera a la regla simple en F1. Su aporte es la probabilidad, que permite ordenar clientes y elegir el umbral.

## El problema

En el proyecto anterior se demostró que el margen se comprime en eventos (Hot Sale, CyberMonday) y en canales con comisión alta, y que retener clientes rinde más que captarlos. La decisión pendiente: **en qué clientes invertir descuentos, remarketing o envío gratis para que vuelvan, y en cuáles no regalar margen porque iban a volver igual**.

- **Tipo de problema:** clasificación binaria supervisada.
- **Target:** `recompra_90d` = 1 si el cliente vuelve a comprar dentro de los 90 días posteriores a la compra observada; 0 si no.
- **Unidad de observación:** una compra. Cada fila describe la compra y el estado del cliente *en ese momento*.

## Los datos

Dataset **sintético**, generado en Python (`numpy` + `pandas`) con lógica de negocio realista: inflación mensual decreciente, comisiones por canal (con la suba de Mercado Libre en octubre 2025), Hot Sale y CyberMonday con descuentos agresivos, caída de Indumentaria desde marzo 2026, y un modelo de comportamiento por cliente (fidelidad latente, churn y recencia). El script y la semilla (`42`) están en el repo: el dataset es 100% reproducible.

| Ítem | Valor |
|---|---|
| Archivo | [`data/ventas_ds.csv`](data/ventas_ds.csv) |
| Período | Enero 2025 – Junio 2026 (18 meses) |
| Filas | 7.617 compras |
| Columnas | 23 (22 features + target) |
| Clientes | 4.208 |
| Tasa de recompra a 90 días | 42,1% |
| Nulos deliberados | `dias_desde_ultima_compra` (primeras compras), `medio_pago` (~3%), `recompra_90d` (ventana truncada en los últimos 90 días) |

Diccionario completo en [`data/diccionario_datos.md`](data/diccionario_datos.md).

**Regla anti-leakage:** ninguna feature usa información posterior a `fecha`. `compras_previas`, `dias_desde_ultima_compra` y `gasto_previo_acum` se calculan solo con compras anteriores. El target se calcula solo con compras posteriores; cuando la ventana de 90 días queda cortada por el fin del período y no se observó recompra, el target es `NaN` (desconocido), nunca 0.

## Hipótesis a validar en el EDA

1. Los clientes que ya compraron antes tienen una tasa de recompra mucho mayor que los nuevos.
2. Las compras hechas en Hot Sale / CyberMonday tienen **menor** recompra: atraen cazadores de ofertas.
3. A más días desde la última compra, menor recompra.
4. La tienda propia retiene más que Mercado Libre.
5. Indumentaria retiene menos desde su caída en 2026.
6. El ticket en pesos constantes de los recurrentes es mayor que el de los nuevos.

## Proceso

- Generación del dataset (`scripts/generar_dataset_ds.py`) → ingesta y radiografía inicial (`notebooks/01_ingesta_y_radiografia.ipynb`) → limpieza, EDA, preprocesamiento, modelado y recomendaciones (`notebooks/proyecto_final_recompra.ipynb`).

## Estructura del repositorio

```
ecommerce-ar-data-science/
├── README.md
├── requirements.txt
├── data/
│   ├── ventas_ds.csv            # dataset principal
│   └── diccionario_datos.md
├── scripts/
│   └── generar_dataset_ds.py    # generador reproducible (semilla 42)
├── notebooks/
│   ├── 01_ingesta_y_radiografia.ipynb   # pre-entrega 2
│   └── proyecto_final_recompra.ipynb    # proyecto final
├── docs/
│   └── preentrega_1.docx
├── kaggle/
│   ├── dataset-metadata.json
│   └── descripcion_kaggle.md
└── img/
```

## Proyecto hermano

Dashboard de Power BI del mismo negocio (Data Analytics): `https://github.com/riveroluciano97-art/ecommerce-argentina-analytics`

## Cómo reproducirlo

```bash
pip install -r requirements.txt
python scripts/generar_dataset_ds.py   # regenera data/ventas_ds.csv de forma idéntica
```

Los notebooks cargan el CSV desde la URL raw del repo, así que corren en Colab sin descargar nada.

---
*Autor: Luciano · Datos sintéticos declarados como tales · 2026*
