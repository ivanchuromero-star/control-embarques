import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path("comercio_embarques.db")


# ---------------------------
# CONEXIÓN
# ---------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# ---------------------------
# BASE DE DATOS
# ---------------------------
def init_db():
    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS embarques (
            embarque_id INTEGER PRIMARY KEY AUTOINCREMENT,
            factura TEXT,
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
            avance REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS detalle_embarque (
            detalle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            embarque_id INTEGER,
            orden_compra TEXT,
            sku TEXT,
            descripcion TEXT,
            cantidad_embarcada REAL
        )
        """)

        conn.commit()


# ---------------------------
# CARGA EXCEL (DINÁMICA)
# ---------------------------
def seed_from_excel(uploaded_file):
    conn = get_conn()

    count = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM embarques",
        conn
    ).iloc[0, 0]

    if count > 0:
        conn.close()
        return

    df = pd.read_excel(uploaded_file, sheet_name="EMBARQUES_PRO")

    df.columns = [str(c).strip().lower() for c in df.columns]

    # mapeo flexible (ajústalo a tu Excel real)
    df = df.rename(columns={
        "factura": "factura",
        "bl": "bl",
        "booking": "booking",
        "status": "status",
        "proveedor": "proveedor",
        "po": "po",
        "cliente": "cliente",
        "agente aduanal": "agente_aduanal",
        "orden de compra": "orden_compra",
        "% avance": "avance"
    })

    df = df.fillna("")

    df.to_sql("embarques", conn, if_exists="append", index=False)
    conn.close()


# ---------------------------
# DASHBOARD
# ---------------------------
def dashboard():
    st.title("📦 Control de Embarques")

    conn = get_conn()

    df = pd.read_sql_query("SELECT * FROM embarques", conn)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total embarques", len(df))
    col2.metric("En tránsito", (df["status"] == "EN TRANSITO").sum())
    col3.metric("Entregados", (df["status"] == "ENTREGADO").sum())

    st.subheader("📊 Últimos embarques")
    st.dataframe(df.tail(20), use_container_width=True)


# ---------------------------
# CARGA DE EXCEL EN UI
# ---------------------------
def upload_excel():
    st.subheader("📥 Cargar Excel")

    file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

    if file:
        seed_from_excel(file)
        st.success("Datos cargados correctamente")
        st.rerun()


# ---------------------------
# BUSCADOR
# ---------------------------
def search():
    st.subheader("🔎 Buscador")

    q = st.text_input("Buscar factura, BL, booking o pedimento")

    if q:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM embarques", conn)

        result = df[df.astype(str).apply(
            lambda x: x.str.contains(q, case=False, na=False)
        ).any(axis=1)]

        st.dataframe(result, use_container_width=True)


# ---------------------------
# APP PRINCIPAL
# ---------------------------
def main():
    st.set_page_config(page_title="Embarques", layout="wide")

    init_db()

    menu = st.sidebar.radio(
        "📌 Menú",
        ["Dashboard", "Cargar Excel", "Buscador"]
    )

    if menu == "Dashboard":
        dashboard()

    elif menu == "Cargar Excel":
        upload_excel()

    elif menu == "Buscador":
        search()


if __name__ == "__main__":
    main()
