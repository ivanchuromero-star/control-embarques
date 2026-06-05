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
            agente_aduanal TEXT,
            ref_agente TEXT,
            naviera TEXT,
            pedimento TEXT,
            orden_compra TEXT,
            avance REAL
        )
        """)
        conn.commit()


# =========================
# LIMPIEZA EXCEL
# =========================
def load_excel(file):
    df = pd.read_excel(file, sheet_name=0)

    df.columns = df.columns.astype(str).str.strip().str.upper()

    def col(name):
        return df[name] if name in df.columns else pd.Series([""] * len(df))

    data = []

    for i in range(len(df)):
        data.append((
            str(col("FACTURA").iloc[i]),
            str(col("TRACKING").iloc[i]),
            str(col("BL").iloc[i]),
            str(col("BOOKING").iloc[i]),
            str(col("STATUS").iloc[i]),
            str(col("PROVEEDOR").iloc[i]),
            str(col("PO").iloc[i]),
            str(col("CLIENTE").iloc[i]),
            str(col("AGENTE ADUANAL").iloc[i]),
            str(col("REF. AGENTE").iloc[i]),
            str(col("NAVIERA").iloc[i]),
            str(col("PEDIMENTO").iloc[i]),
            str(col("ORDEN DE COMPRA").iloc[i]),
            float(str(col("% AVANCE").iloc[i] or 0).replace("%","0"))
        ))

    return data


# =========================
# INSERT
# =========================
def insert_data(data):
    with get_conn() as conn:
        conn.executemany("""
        INSERT INTO embarques (
            factura, tracking, bl, booking, status, proveedor, po, cliente,
            agente_aduanal, ref_agente, naviera, pedimento,
            orden_compra, avance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()


# =========================
# UI
# =========================
def main():
    st.set_page_config(page_title="Embarques Limpio", layout="wide")

    init_db()

    st.title("📦 Sistema de Embarques (Limpio)")

    menu = st.sidebar.radio("Menú", ["Dashboard", "Cargar Excel"])

    if menu == "Dashboard":
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM embarques", conn)

        st.metric("Total registros", len(df))
        st.dataframe(df, use_container_width=True)

    elif menu == "Cargar Excel":
        file = st.file_uploader("Sube Excel", type=["xlsx"])

        if file:
            data = load_excel(file)
            insert_data(data)

            st.success("Datos cargados correctamente")
            st.rerun()


if __name__ == "__main__":
    main()
