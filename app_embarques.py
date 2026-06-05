import sqlite3
from pathlib import Path
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
        return float(val) if val else 0.0
    except:
        return 0.0

# =========================
# 🔥 FIX REAL DEL EXCEL
# =========================
def load_excel(file):
    # Leer TODAS las filas
    df_raw = pd.read_excel(file, header=None)

    # Buscar fila donde empieza la tabla (donde aparece FACTURA)
    start_row = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains("FACTURA").any():
            start_row = i
            break

    if start_row is None:
        st.error("No se encontró la estructura del Excel")
        return []

    # Leer desde ahí
    df = pd.read_excel(file, header=start_row)

    df.columns = df.columns.astype(str).str.strip().str.upper()
    df = df.fillna("")

    data = []

    for _, row in df.iterrows():
        # Evitar filas basura
        if str(row.get("FACTURA")).strip() == "":
            continue

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
            eta, llegada, avance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()

# =========================
# UI
# =========================
def main():
    st.set_page_config(page_title="Embarques PRO", layout="wide")

    init_db()

    st.title("📦 Sistema de Embarques PRO")

    menu = st.sidebar.radio("Menú", [
        "Dashboard",
        "Búsqueda",
        "Cargar Excel"
    ])

    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM embarques", conn)

    # =========================
    # DASHBOARD
    # =========================
    if menu == "Dashboard":

        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Total", len(df))
            col2.metric("Liberados", len(df[df["status"] == "LIBERADOS"]))
            col3.metric("Pendientes", len(df[df["status"] == "PENDIENTE"]))
            col4.metric("Avance Promedio", f"{df['avance'].mean():.1f}%")

        st.divider()

        # SEMÁFORO
        def color_avance(val):
            if val >= 80:
                return "background-color: #c6efce"
            elif val >= 50:
                return "background-color: #ffeb9c"
            return "background-color: #ffc7ce"

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            # DESCARGA
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Descargar Excel", csv, "embarques.csv", "text/csv")

    # =========================
    # BUSQUEDA
    # =========================
    elif menu == "Búsqueda":

        query = st.text_input("Buscar")

        if query:
            df_filtrado = df[df.apply(
                lambda row: query.lower() in str(row).lower(), axis=1
            )]
            st.dataframe(df_filtrado)

    # =========================
    # CARGA
    # =========================
    elif menu == "Cargar Excel":

        file = st.file_uploader("Sube el Excel", type=["xlsx"])

        if file:
            data = load_excel(file)

            st.write(f"Registros detectados: {len(data)}")

            if st.button("Confirmar carga"):
                insert_data(data)
                st.success("✅ Carga exitosa")
                st.rerun()

# =========================
if __name__ == "__main__":
    main()
