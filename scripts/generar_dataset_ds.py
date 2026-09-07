"""
Generador del dataset ventas_ds.csv — Predicción de recompra a 90 días
Proyecto Data Science I · Coderhouse · Luciano
-------------------------------------------------------------------------
Continuación del proyecto de Data Analytics (ecommerce_ar). Reutiliza el
catálogo de productos, los canales, la lógica de precios con inflación,
los eventos (Hot Sale / CyberMonday) y la suba de comisión de Mercado
Libre (oct-2025), pero reemplaza la capa de CLIENTES por un modelo de
comportamiento: cada cliente tiene una fidelidad latente que determina
cada cuánto vuelve a comprar y cuándo deja de hacerlo.

¿Por qué no usar directamente ventas.csv del proyecto anterior?
  Ese dataset fue diseñado para un dashboard de facturación y margen:
  900 clientes con ~26 compras cada uno. Con esa densidad, el 98% de las
  compras tiene una recompra en 90 días y el target no discrimina nada.
  Además, las compras se asignaban a clientes al azar sin respetar la
  fecha de alta. Para un problema predictivo la unidad de análisis es
  el cliente en un momento dado, y eso exige simular trayectorias.

Diseño del comportamiento (hipótesis plantadas para que el EDA las encuentre):
  H1 Recurrencia genera recurrencia: fidelidad alta -> gaps cortos y menos churn.
  H2 Compras en Hot Sale / CyberMonday retienen menos ("cazadores de ofertas").
  H3 Recencia: a más días desde la última compra, menor recompra (emerge del modelo de gaps).
  H4 Canal: Tienda propia y WhatsApp retienen más que Mercado Libre.
  H5 Categoría: Indumentaria retiene menos desde marzo 2026 (caída de la categoría).
  H6 Los recurrentes compran más unidades por ticket (replica el insight del dashboard).

Anti-leakage:
  - Las features de comportamiento (compras_previas, dias_desde_ultima_compra,
    gasto_previo_acum, antiguedad_dias) se calculan SOLO con compras anteriores
    a la fila. Se simula historia desde ene-2024 para que los clientes
    "viejos" tengan pasado real, pero se exportan solo filas de ene-2025 a jun-2026.
  - recompra_90d mira SOLO hacia adelante. Si la ventana de 90 días queda
    truncada por el fin del período y no se observó recompra, el target es
    NaN (no se conoce), nunca 0.

Uso:  python scripts/generar_dataset_ds.py   (escribe data/ventas_ds.csv)
Semilla fija: 42.
"""

from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
RUTA_SALIDA = Path(__file__).resolve().parent.parent / "data" / "ventas_ds.csv"

# -----------------------------------------------------------------------
# 1. Canales (idénticos al proyecto de Data Analytics)
# -----------------------------------------------------------------------
canales = pd.DataFrame([
    (1, "Tienda propia",  "Web propia",    0.06),
    (2, "Mercado Libre",  "Marketplace",   0.14),   # sube a 0.17 desde oct-2025
    (3, "Instagram Shop", "Redes",         0.08),
    (4, "WhatsApp",       "Venta directa", 0.03),
], columns=["id_canal", "canal", "tipo_canal", "comision_base_pct"])
nombre_canal = dict(zip(canales["id_canal"], canales["canal"]))
comision_base = dict(zip(canales["id_canal"], canales["comision_base_pct"]))

# -----------------------------------------------------------------------
# 2. Productos (misma lógica y misma semilla que el proyecto anterior:
#    el catálogo de 60 productos queda idéntico)
# -----------------------------------------------------------------------
categorias = {
    "Tecnología":   (60, 220, 0.32),
    "Hogar":        (25, 120, 0.42),
    "Indumentaria": (15, 75,  0.48),
    "Deportes":     (20, 110, 0.40),
    "Belleza":      (8,  45,  0.52),
}
nombres_base = {
    "Tecnología":   ["Auriculares BT", "Smartwatch", "Teclado mecánico", "Mouse gamer", "Parlante portátil", "Cargador rápido", "Webcam HD", "Tablet 10\"", "Power bank", "Hub USB-C", "Soporte notebook", "Micrófono USB"],
    "Hogar":        ["Cafetera espresso", "Pava eléctrica", "Set sábanas", "Lámpara escritorio", "Organizador cocina", "Difusor aromas", "Vajilla x12", "Manta polar", "Espejo LED", "Reloj pared", "Cortina blackout", "Silla escritorio"],
    "Indumentaria": ["Remera oversize", "Buzo canguro", "Jean mom", "Campera puffer", "Zapatillas urbanas", "Gorra trucker", "Vestido midi", "Camisa lino", "Short deportivo", "Medias x3", "Cinturón cuero", "Mochila urbana"],
    "Deportes":     ["Colchoneta yoga", "Mancuernas 5kg", "Botella térmica", "Banda elástica set", "Pelota fútbol", "Rodillera neopreno", "Soga saltar pro", "Guantes gym", "Bolso deportivo", "Tobillera ajustable", "Roller abdominal", "Cinta kinesiológica"],
    "Belleza":      ["Sérum vitamina C", "Crema hidratante", "Kit brochas x8", "Perfume 100ml", "Máscara pestañas", "Plancha pelo", "Aceite argán", "Protector solar 50", "Esmalte gel", "Limpiador facial", "Bálsamo labial", "Kit skincare"],
}
rows, pid = [], 1
for cat, (pmin, pmax, margen) in categorias.items():
    for nombre in nombres_base[cat]:
        precio_lista = round(rng.uniform(pmin, pmax) * 1000, -2)
        costo = round(precio_lista * (1 - margen) * rng.uniform(0.95, 1.05), -2)
        rows.append((pid, nombre, cat, precio_lista, costo))
        pid += 1
productos = pd.DataFrame(rows, columns=["id_producto", "producto", "categoria", "precio_lista_base", "costo_base"])
prod_tec = productos.index[productos["categoria"] == "Tecnología"].to_numpy()
prod_all = productos.index.to_numpy()
productos_rec = productos.to_dict("records")   # acceso rápido por índice

# -----------------------------------------------------------------------
# 3. Calendario e inflación
#    Se simula desde ene-2024 (historia) pero se exporta desde ene-2025.
#    El índice se normaliza para que ene-2025 = 1.0450, igual que la
#    columna indice_precios del dashboard de Power BI.
# -----------------------------------------------------------------------
INICIO_HISTORIA = pd.Timestamp("2024-01-01")
INICIO_PERIODO  = pd.Timestamp("2025-01-01")
FIN_PERIODO     = pd.Timestamp("2026-06-30")
VENTANA_TARGET  = 90  # días

meses = pd.date_range(INICIO_HISTORIA, FIN_PERIODO, freq="MS")
infl_2024 = np.linspace(0.075, 0.050, 12)          # 2024: inflación más alta
infl_2526 = np.linspace(0.045, 0.022, 18)          # 2025-26: decreciente (igual que DA)
indice = np.cumprod(1 + np.concatenate([infl_2024, infl_2526]))
indice = indice / indice[12] * 1.0450               # ene-2025 == 1.0450
indice_por_mes = dict(zip(meses.to_period("M"), indice))

factor_mes = {1: 0.85, 2: 0.82, 3: 0.95, 4: 0.92, 5: 1.55, 6: 1.00,
              7: 1.05, 8: 0.95, 9: 0.92, 10: 1.00, 11: 1.45, 12: 1.35}

def share_canales(fecha):
    """Participación de canales: ML crece con el tiempo (insight 1 del dashboard)."""
    i = max(0, (fecha.year - 2025) * 12 + fecha.month - 1)
    ml = min(0.32 + 0.012 * i, 0.53)
    resto = 1 - ml
    return np.array([resto * 0.45, ml, resto * 0.33, resto * 0.22])

def es_evento(fecha):
    return fecha.month in (5, 11)

def comision(canal_id, fecha):
    if canal_id == 2 and fecha >= pd.Timestamp("2025-10-01"):
        return 0.17
    return comision_base[canal_id]

# -----------------------------------------------------------------------
# 4. Clientes: modelo de comportamiento
# -----------------------------------------------------------------------
provincias = ["Buenos Aires", "CABA", "Córdoba", "Santa Fe", "Mendoza", "Tucumán", "Entre Ríos", "Salta", "Neuquén", "Misiones"]
pesos_prov  = [0.30, 0.20, 0.12, 0.10, 0.07, 0.05, 0.04, 0.04, 0.04, 0.04]
medios_pago = ["Tarjeta de crédito", "Tarjeta de débito", "Transferencia", "Billetera virtual"]

N_CLIENTES = 6300

# Fecha de primera compra: ponderada por la estacionalidad (los eventos captan más clientes nuevos)
pesos_alta = np.array([factor_mes[m.month] * (1.25 if es_evento(m) else 1.0) for m in meses])
pesos_alta = pesos_alta / pesos_alta.sum()

def sortear_fecha_en_mes(mes):
    """Día del mes; en eventos se concentra en la semana del evento (igual que en DA)."""
    dias = pd.Period(mes, freq="M").days_in_month
    if mes.month == 5 and rng.random() < 0.55:
        dia = int(rng.integers(12, 19))
    elif mes.month == 11 and rng.random() < 0.50:
        dia = int(rng.integers(3, 10))
    else:
        dia = int(rng.integers(1, dias + 1))
    return mes.replace(day=dia)

ventas_rows = []
oid = 1

for cid in range(1, N_CLIENTES + 1):
    provincia = rng.choice(provincias, p=pesos_prov)
    mes_alta = meses[rng.choice(len(meses), p=pesos_alta)]
    fecha = sortear_fecha_en_mes(mes_alta)

    # Canal preferido: se define en la primera compra según el share del mes
    canal_pref = int(rng.choice([1, 2, 3, 4], p=share_canales(fecha)))

    # Fidelidad latente (0-1): mezcla de "compradores de una vez" y "fieles"
    fidelidad = rng.beta(2.2, 2.8)
    if es_evento(fecha):          # H2: captado en evento -> cazador de ofertas
        fidelidad *= 0.62
    fidelidad *= {1: 1.18, 2: 0.80, 3: 0.95, 4: 1.12}[canal_pref]   # H4: canal
    fidelidad = float(np.clip(fidelidad, 0.02, 0.95))

    # Medio de pago habitual
    if canal_pref == 2:
        medio_hab = "Billetera virtual" if rng.random() < 0.6 else "Tarjeta de crédito"
    elif canal_pref == 4:
        medio_hab = str(rng.choice(["Transferencia", "Billetera virtual"]))
    else:
        medio_hab = str(rng.choice(medios_pago, p=[0.45, 0.25, 0.15, 0.15]))

    fecha_alta = fecha
    compras_previas, gasto_prev, ultima = 0, 0.0, None

    while fecha <= FIN_PERIODO:
        mes = fecha.replace(day=1)
        idx = indice_por_mes[mes.to_period("M")]
        evento = es_evento(fecha)

        # Canal de esta compra: mayormente el preferido
        canal = canal_pref if rng.random() < 0.72 else int(rng.choice([1, 2, 3, 4], p=share_canales(fecha)))

        # Producto: en eventos, Tecnología concentra más
        prod = productos_rec[rng.choice(prod_tec)] if (evento and rng.random() < 0.42) else productos_rec[rng.choice(prod_all)]

        # Cantidad: los recurrentes llevan más unidades (H6)
        cantidad = int(rng.choice([1, 2, 3], p=[0.62, 0.28, 0.10]))
        if compras_previas > 0 and rng.random() < 0.35:
            cantidad += 1

        # Precios con inflación + ruido
        precio_unit = prod["precio_lista_base"] * idx * rng.uniform(0.97, 1.03)
        costo_unit  = prod["costo_base"]        * idx * rng.uniform(0.98, 1.04)

        # Descuentos agresivos en eventos
        if fecha.month == 5:
            desc = rng.choice([0.10, 0.15, 0.20, 0.25], p=[0.25, 0.35, 0.30, 0.10])
        elif fecha.month == 11:
            desc = rng.choice([0.10, 0.15, 0.20, 0.25], p=[0.35, 0.35, 0.20, 0.10])
        else:
            desc = rng.choice([0.0, 0.05, 0.10, 0.15], p=[0.55, 0.20, 0.15, 0.10])

        monto = cantidad * precio_unit * (1 - desc)

        # Medio de pago y cuotas (con nulos realistas en medio_pago)
        medio = medio_hab if rng.random() < 0.8 else str(rng.choice(medios_pago))
        cuotas = int(rng.choice([1, 3, 6, 12], p=[0.35, 0.30, 0.25, 0.10])) if medio == "Tarjeta de crédito" else 1
        if rng.random() < 0.03:
            medio = None

        ventas_rows.append({
            "id_venta": oid,
            "fecha": fecha,
            "id_cliente": cid,
            "provincia": provincia,
            "fecha_alta_cliente": fecha_alta,
            "antiguedad_dias": (fecha - fecha_alta).days,
            "compras_previas": compras_previas,
            "dias_desde_ultima_compra": (fecha - ultima).days if ultima is not None else np.nan,
            "gasto_previo_acum": round(gasto_prev, 2),
            "canal": nombre_canal[canal],
            "comision_canal_pct": comision(canal, fecha),
            "categoria": prod["categoria"],
            "producto": prod["producto"],
            "precio_unitario": round(precio_unit, 2),
            "costo_unitario": round(costo_unit, 2),
            "cantidad": cantidad,
            "monto": round(monto, 2),
            "descuento_pct": float(desc),
            "medio_pago": medio,
            "cuotas": cuotas,
            "es_evento": evento,
            "indice_inflacion": round(idx, 4),
        })
        oid += 1

        # ---- ¿vuelve a comprar? (churn) ----
        p_seguir = fidelidad
        if evento:
            p_seguir *= 0.72                      # H2: la compra de evento retiene menos
        if prod["categoria"] == "Indumentaria" and fecha >= pd.Timestamp("2026-03-01"):
            p_seguir *= 0.55                      # H5: caída de Indumentaria
        if canal == 2:
            p_seguir *= 0.90                      # H4: la relación es con la plataforma
        if compras_previas >= 2:
            p_seguir = min(0.97, p_seguir + 0.12) # H1: recurrencia genera recurrencia

        compras_previas += 1
        gasto_prev += monto
        ultima = fecha

        if rng.random() > p_seguir:
            break  # el cliente se va (churn)

        # ---- ¿cuándo vuelve? gap en días según fidelidad (H3) ----
        gap_medio = 20 + 110 * (1 - fidelidad)
        gap = int(max(1, rng.lognormal(np.log(gap_medio), 0.55)))
        fecha = fecha + pd.Timedelta(days=gap)

ventas = pd.DataFrame(ventas_rows)

# -----------------------------------------------------------------------
# 5. Target recompra_90d (solo mira hacia adelante)
# -----------------------------------------------------------------------
ventas = ventas.sort_values(["id_cliente", "fecha"]).reset_index(drop=True)
proxima = ventas.groupby("id_cliente")["fecha"].shift(-1)
dias_hasta_proxima = (proxima - ventas["fecha"]).dt.days

hay_recompra = dias_hasta_proxima <= VENTANA_TARGET
ventana_completa = ventas["fecha"] <= FIN_PERIODO - pd.Timedelta(days=VENTANA_TARGET)

ventas["recompra_90d"] = np.select(
    [hay_recompra, ventana_completa],   # 1 si se observó recompra; 0 si la ventana cerró sin recompra
    [1.0, 0.0],
    default=np.nan,                     # ventana truncada y sin recompra observada: desconocido
)

# -----------------------------------------------------------------------
# 6. Exportar solo el período de análisis (ene-2025 a jun-2026)
# -----------------------------------------------------------------------
salida = ventas[ventas["fecha"] >= INICIO_PERIODO].copy()
salida = salida.sort_values(["fecha", "id_cliente"]).reset_index(drop=True)
salida["id_venta"] = np.arange(1, len(salida) + 1)   # ids correlativos por fecha
salida["fecha"] = salida["fecha"].dt.date
salida["fecha_alta_cliente"] = pd.to_datetime(salida["fecha_alta_cliente"]).dt.date
salida["recompra_90d"] = salida["recompra_90d"].astype("Int64")

RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
salida.to_csv(RUTA_SALIDA, index=False)

# -----------------------------------------------------------------------
# 7. Resumen de control
# -----------------------------------------------------------------------
print(f"Filas exportadas: {len(salida):,} | Columnas: {salida.shape[1]} | Clientes: {salida['id_cliente'].nunique():,}")
print(f"Período: {salida['fecha'].min()} a {salida['fecha'].max()}")
print(f"Target conocido: {salida['recompra_90d'].notna().sum():,} filas | NaN (ventana truncada): {salida['recompra_90d'].isna().sum():,}")
print(f"Tasa de recompra a 90 días: {salida['recompra_90d'].mean():.1%}")
print("Recompra por evento:\n", salida.groupby("es_evento")["recompra_90d"].mean().round(3).to_string())
print("Recompra por canal:\n", salida.groupby("canal")["recompra_90d"].mean().round(3).to_string())
print("Recompra primera compra vs recurrente:\n",
      salida.groupby(salida["compras_previas"] > 0)["recompra_90d"].mean().round(3).to_string())
