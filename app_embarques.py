import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path("comercio_embarques.db")


# =========================
# DB
# =========================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    with get_conn() as conn:
        conn.execute("""
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
        conn.commit()


# =========================
# NORMALIZADOR DE EXCEL
# =========================
def normalize_df(df):
    df.columns = [str(c).strip().lower() for c in df.columns]

    rename_map = {
        "factura": "factura",
        "bl": "bl",
        "booking": "booking",
        "status": "status",
        "proveedor": "proveedor",
        "po": "po",
        "cliente": "cliente",
        "agente aduanal": "agente_aduanal",
        "ref. agente": "ref_agente",
        "naviera": "naviera",
        "pedimento": "pedimento",
        "orden de compra": "orden_compra",
        "% avance": "avance"
    }

    df = df.rename(columns=rename_map)

    for col in rename_map.values():
        if col not in df.columns:
            df[col] = ""

    df["avance"] = pd.to_numeric(df.get("avance", 0), errors="coerce").fillna(0)

    return df[[
        "factura", "bl", "booking", "status", "proveedor", "po",
        "cliente", "agente_aduanal", "ref_agente", "naviera",
        "pedimento", "orden_compra", "avance"
    ]]


# =========================
# INSERT MANUAL
# =========================
def insert_manual(data):
    with get_conn() as conn:
        conn.execute("""
        INSERT INTO embarques (
            factura, bl, booking, status, proveedor, po, cliente,
            agente_aduanal, ref_agente, naviera, pedimento,
            orden_compra, avance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()


# =========================
# INSERT EXCEL
# =========================
def insert_excel(df):
    with get_conn() as conn:
        for _, row in df.iterrows():
            conn.execute("""
            INSERT INTO embarques (
                factura, bl, booking, status, proveedor, po, cliente,
                agente_aduanal, ref_agente, naviera, pedimento,
                orden_compra, avance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(row))
        conn.commit()


# =========================
# DASHBOARD
# =========================
def dashboard():
    st.title("📦 Control de Embarques")

    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM embarques", conn)

    col1, col2, col3 = st.columns(3)

    col1.metric("Total", len(df))
    col2.metric("En tránsito", (df["status"] == "EN TRANSITO").sum())
    col3.metric("Entregados", (df["status"] == "ENTREGADO").sum())

    st.subheader("📊 Embarques")
    st.dataframe(df, use_container_width=True)


# =========================
# CARGA EXCEL
# =========================
def upload_excel():
    st.subheader("📥 Cargar Excel")

    file = st.file_uploader("Sube archivo Excel", type=["xlsx"])

    if file:
        try:
            df = pd.read_excel(file, sheet_name=0)
            df = normalize_df(df)
            insert_excel(df)

            st.success("Excel cargado correctamente")
            st.rerun()

        except Exception as e:
            st.error(f"Error leyendo Excel: {e}")


# =========================
# CAPTURA MANUAL
# =========================
def manual_entry():
    st.subheader("✍️ Captura manual")

    with st.form("manual_form"):
        factura = st.text_input("Factura")
        bl = st.text_input("BL")
        booking = st.text_input("Booking")
        status = st.selectbox("Status", ["PENDIENTE", "EN TRANSITO", "ENTREGADO"])
        proveedor = st.text_input("Proveedor")
        po = st.text_input("PO")
        cliente = st.text_input("Cliente")
        agente = st.text_input("Agente aduanal")
        ref = st.text_input("Referencia agente")
        naviera = st.text_input("Naviera")
        pedimento = st.text_input("Pedimento")
        oc = st.text_input("Orden de compra")
        avance = st.number_input("Avance", 0.0, 100.0, 0.0)

        submit = st.form_submit_button("Guardar")

        if submit:
            insert_manual((
                factura, bl, booking, status, proveedor, po, cliente,
                agente, ref, naviera, pedimento, oc, avance
            ))
            st.success("Guardado correctamente")
            st.rerun()


# =========================
# BUSCADOR
# =========================
def search():
    st.subheader("🔎 Buscador")

    q = st.text_input("Buscar")

    if q:
        conn = get_conn()
        df = pd.read_sql_query("SELECT * FROM embarques", conn)

        res = df[df.astype(str).apply(
            lambda x: x.str.contains(q, case=False, na=False)
        ).any(axis=1)]

        st.dataframe(res, use_container_width=True)


# =========================
# MAIN
# =========================
def main():
    st.set_page_config(page_title="Embarques PRO", layout="wide")

    init_db()

    menu = st.sidebar.radio(
        "Menú",
        ["Dashboard", "Cargar Excel", "Captura manual", "Buscador"]
    )

    if menu == "Dashboard":
        dashboard()

    elif menu == "Cargar Excel":
        upload_excel()

    elif menu == "Captura manual":
        manual_entry()

    elif menu == "Buscador":
        search()


if __name__ == "__main__":
    main()
