import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "embarques.db"

# =========================
# DB
# =========================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS embarques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura TEXT,
            tracking TEXT,
            bl TEXT,
            booking TEXT,
            status TEXT,
            proveedor TEXT,
            po TEXT,
            cliente TEXT,
            naviera TEXT,
            eta TEXT,
            llegada TEXT,
            avance REAL
        )
        """)
        conn.commit()

# =========================
# HELPERS
# =========================
def clean(val):
    return "" if pd.isna(val) else str(val).strip()

def parse_avance(val):
    try:
        val = str(val).replace("%", "").strip()
        return float(val) if val else 0
    except:
        return 0

# =========================
# LECTOR INTELIGENTE EXCEL
# =========================
def load_excel(file):
    df_raw = pd.read_excel(file, header=None)

    start_row = None

    for i, row in df_raw.iterrows():
        texto = " ".join(row.astype(str)).upper()
        if "FACTURA" in texto and "TRACKING" in texto:
            start_row = i
            break

    if start_row is None:
        st.error("❌ No se encontró la tabla del Excel")
        return []

    df = pd.read_excel(file, header=start_row)

    df.columns = df.columns.astype(str).str.strip().str.upper()
    df = df.fillna("")

    data = []

    for _, row in df.iterrows():
        factura = clean(row.get("FACTURA"))

        if factura == "":
            continue

        data.append((
            factura,
            clean(row.get("TRACKING")),
            clean(row.get("BL")),
            clean(row.get("BOOKING")),
            clean(row.get("STATUS")),
            clean(row.get("PROVEEDOR")),
            clean(row.get("PO")),
            clean(row.get("CLIENTE")),
            clean(row.get("NAVIERA")),
            clean(row.get("ETA VERACRUZ")),
            clean(row.get("LLEGADA LOSIFRA")),
            parse_avance(row.get("% AVANCE"))
        ))

    return data

# =========================
# INSERT
# =========================
def insert_data(data):
    with get_conn() as conn:

        # validar estructura
        for fila in data:
            if len(fila) != 12:
                st.error(f"❌ Error en fila: {fila}")
                return

        conn.executemany("""
        INSERT INTO embarques (
            factura, tracking, bl, booking, status,
            proveedor, po, cliente, naviera,
            eta, llegada, avance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        conn.commit()

# =========================
# ALERTAS / SEMAFORO
# =========================
def calcular_estado(avance):
    if avance >= 80:
        return "🟢 ALTO"
    elif avance >= 50:
        return "🟡 MEDIO"
    else:
        return "🔴 BAJO"

# =========================
# UI
# =========================
def main():
    st.set_page_config(page_title="Embarques PRO", layout="wide")

    init_db()

    st.title("📦 CONTROL DE EMBARQUES PRO")

    menu = st.sidebar.radio("Menú", [
        "📊 Dashboard",
        "🔍 Búsqueda",
        "📂 Cargar Excel"
    ])

    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM embarques", conn)

    # =========================
    # DASHBOARD
    # =========================
    if menu == "📊 Dashboard":

        if df.empty:
            st.warning("No hay datos")
            return

        df["Estado"] = df["avance"].apply(calcular_estado)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total", len(df))

