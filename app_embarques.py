import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path("embarques.db")

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
            pedimento TEXT,
            contenedores TEXT,
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
        return float(val) if val else 0.0
    except:
        return 0.0


# =========================
# LOAD EXCEL (adaptado a tu archivo)
# =========================
def load_excel(file):
    df = pd.read_excel(file)

    df.columns = df.columns.astype(str).str.strip().str.upper()

    df = df.fillna("")

    data = []

    for _, row in df.iterrows():
        data.append((
            clean(row.get("FACTURA")),
            clean(row.get("TRACKING")),
            clean(row.get("BL")),
            clean(row.get("BOOKING")),
            clean(row.get("STATUS")),
            clean(row.get("PROVEEDOR")),
            clean(row.get("PO")),
            clean(row.get("CLIENTE")),
            clean(row.get("NAVIERA")),
            clean(row.get("ETA VERACRUZ")),
            clean(row.get("PEDIMENTO")),
            clean(row.get("CONTENEDORES")),
            clean(row.get("LLEGADA LOSIFRA")),
            parse_avance(row.get("% AVANCE"))
        ))

    return data


# =========================
# INSERT
# =========================
def insert_data(data):
    with get_conn() as conn:
        conn.execute("DELETE FROM embarques")
        conn.executemany("""
        INSERT INTO embarques (
            factura, tracking, bl, booking, status,
            proveedor, po, cliente, naviera,
            eta, pedimento, contenedores,
            llegada, avance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()


# =========================
# EXPORT
# =========================
def download_excel(df):
    return df.to_excel(index=False, engine='openpyxl')


# =========================
# UI
# =========================
def main():
    st.set_page_config(page_title="Sistema de Embarques PRO", layout="wide")

    init_db()

    st.title("📦 Sistema de Embarques PRO")

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

        st.subheader("KPIs")

        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)

            total = len(df)
            liberados = len(df[df["status"] == "LIBERADOS"])
            pendientes = len(df[df["status"] == "PENDIENTE"])
            avance = df["avance"].mean()

            col1.metric("Total", total)
            col2.metric("Liberados", liberados)
            col3.metric("Pendientes", pendientes)
            col4.metric("Avance Promedio", f"{avance:.1f}%")

        st.divider()

        # ALERTAS
        st.subheader("Alertas")

        atrasados = df[df["avance"] < 50]
        st.write(f"🔴 Registros con bajo avance: {len(atrasados)}")

        st.divider()

        # TABLA
        st.subheader("Tabla")
        st.dataframe(df, use_container_width=True)

        # DESCARGA
        st.download_button(
            "⬇️ Descargar Excel",
            data=df.to_csv(index=False),
            file_name="embarques.csv",
            mime="text/csv"
        )

    # =========================
    # BUSQUEDA
    # =========================
    elif menu == "🔍 Búsqueda":

        st.subheader("Búsqueda rápida")

