import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path("comercio_embarques.db")


# =========================
# CONEXIÓN
# =========================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# =========================
# BASE DE DATOS
# =========================
def init_db():
    with get_conn() as conn:
    conn.execute("DELETE FROM embarques")
    
        conn.commit()


# =========================
# EXCEL → NORMALIZADOR
# =========================
def seed_from_excel(uploaded_file):
    conn = get_conn()

    count = pd.read_sql_query(
        "SELECT COUNT(*) as total FROM embarques",
        conn
    ).iloc[0, 0]

    if count > 0:
        conn.close()
        return

    df = pd.read_excel(uploaded_file, sheet_name=0)

    # normalizar columnas
    df.columns = df.columns.astype(str).str.strip().str.upper()

    def get(col):
        return df[col] if col in df.columns else ""

    for i in range(len(df)):
        conn.execute("""
        INSERT INTO embarques (
            factura, tracking, bl, booking, status, proveedor, po, cliente,
            agente_aduanal, ref_agente, naviera, eta_veracruz,
            ven_demoras, pedimento, contenedores, sol_impuestos,
            pago_impuestos, carga_gondola, pantaco, ven_dem_pantaco,
            orden_compra, transporte_um, llegada_losifra, avance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(get("FACTURA").iloc[i]) if "FACTURA" in df.columns else "",
            str(get("TRACKING").iloc[i]) if "TRACKING" in df.columns else "",
            str(get("BL").iloc[i]) if "BL" in df.columns else "",
            str(get("BOOKING").iloc[i]) if "BOOKING" in df.columns else "",
            str(get("STATUS").iloc[i]) if "STATUS" in df.columns else "",
            str(get("PROVEEDOR").iloc[i]) if "PROVEEDOR" in df.columns else "",
            str(get("PO").iloc[i]) if "PO" in df.columns else "",
            str(get("CLIENTE").iloc[i]) if "CLIENTE" in df.columns else "",
            str(get("AGENTE ADUANAL").iloc[i]) if "AGENTE ADUANAL" in df.columns else "",
            str(get("REF. AGENTE").iloc[i]) if "REF. AGENTE" in df.columns else "",
            str(get("NAVIERA").iloc[i]) if "NAVIERA" in df.columns else "",
            str(get("ETA VERACRUZ").iloc[i]) if "ETA VERACRUZ" in df.columns else "",
            str(get("VEN. DEMORAS").iloc[i]) if "VEN. DEMORAS" in df.columns else "",
            str(get("PEDIMENTO").iloc[i]) if "PEDIMENTO" in df.columns else "",
            str(get("CONTENEDORES").iloc[i]) if "CONTENEDORES" in df.columns else "",
            str(get("SOL. IMPUESTOS").iloc[i]) if "SOL. IMPUESTOS" in df.columns else "",
            str(get("PAGO IMPUESTOS").iloc[i]) if "PAGO IMPUESTOS" in df.columns else "",
            str(get("CARGA GONDOLA").iloc[i]) if "CARGA GONDOLA" in df.columns else "",
            str(get("PANTACO").iloc[i]) if "PANTACO" in df.columns else "",
            str(get("VEN. DEM. PANTACO").iloc[i]) if "VEN. DEM. PANTACO" in df.columns else "",
            str(get("ORDEN DE COMPRA").iloc[i]) if "ORDEN DE COMPRA" in df.columns else "",
            str(get("TRANSPORTE UM").iloc[i]) if "TRANSPORTE UM" in df.columns else "",
            str(get("LLEGADA LOSIFRA").iloc[i]) if "LLEGADA LOSIFRA" in df.columns else "",
            float(str(get("% AVANCE").iloc[i]).replace("%","") or 0) if "% AVANCE" in df.columns else 0
        ))

    conn.commit()
    conn.close()


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

    st.subheader("📊 Tabla general")
    st.dataframe(df, use_container_width=True)


# =========================
# CARGA EXCEL
# =========================
def upload_excel():
    st.subheader("📥 Cargar Excel")

    file = st.file_uploader("Sube tu Excel", type=["xlsx"])

    if file:
        seed_from_excel(file)
        st.success("Datos cargados correctamente")
        st.rerun()


# =========================
# CAPTURA MANUAL
# =========================
def manual_entry():
    st.subheader("✍️ Captura manual")

    with st.form("manual"):
        factura = st.text_input("Factura")
        tracking = st.text_input("Tracking")
        bl = st.text_input("BL")
        booking = st.text_input("Booking")
        status = st.selectbox("Status", ["PENDIENTE", "EN TRANSITO", "ENTREGADO"])
        proveedor = st.text_input("Proveedor")
        po = st.text_input("PO")
        cliente = st.text_input("Cliente")

        submit = st.form_submit_button("Guardar")

        if submit:
            with get_conn() as conn:
                conn.execute("""
                INSERT INTO embarques (
                    factura, tracking, bl, booking, status, proveedor, po, cliente
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    factura, tracking, bl, booking, status, proveedor, po, cliente
                ))
                conn.commit()

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
