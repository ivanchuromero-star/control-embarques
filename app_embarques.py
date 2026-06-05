import sqlite3
import pandas as pd
import streamlit as st
import webbrowser

DB_PATH = "embarques.db"

# =========================
# DB
# =========================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        # 🔥 BORRA LA TABLA COMPLETAMENTE (FIX CLAVE)
        conn.execute("DROP TABLE IF EXISTS embarques")

        conn.execute("""
        CREATE TABLE embarques (
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
# ALERTAS (CLAVE DEL SISTEMA)
# =========================
def calcular_alerta(row):
    try:
        if row["avance"] < 50:
            return "🔴 URGENTE"
        elif row["avance"] < 80:
            return "🟠 ATENCIÓN"
        return "🟢 EN TIEMPO"
    except:
        return "⚪ SIN DATOS"

# =========================
# CARGA INTELIGENTE EXCEL
# =========================
def load_excel(file):
    df_raw = pd.read_excel(file, header=None)

    start_row = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains("FACTURA").any():
            start_row = i
            break

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

        for fila in data:
            if len(fila) != 12:
                st.error(f"❌ Error en fila: {fila}")
                return

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

    st.title("📦 CONTROL DE EMBARQUES PRO")

    menu = st.sidebar.radio("Menú", [
        "📊 Dashboard",
        "🔍 Buscador",
        "📂 Cargar Excel"
    ])

    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM embarques", conn)

    if not df.empty:
        df["Alerta"] = df.apply(calcular_alerta, axis=1)

    # =========================
    # DASHBOARD
    # =========================
    if menu == "📊 Dashboard":

        if df.empty:
            st.warning("No hay datos")
            return

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total", len(df))
        col2.metric("Liberados", len(df[df["status"] == "LIBERADOS"]))
        col3.metric("Pendientes", len(df[df["status"] == "PENDIENTE"]))
        col4.metric("Avance Promedio", f"{df['avance'].mean():.1f}%")

        st.divider()

        st.subheader("🚨 Panel de Alertas")

        st.write("🔴 Urgentes:", len(df[df["Alerta"] == "🔴 URGENTE"]))
        st.write("🟠 Atención:", len(df[df["Alerta"] == "🟠 ATENCIÓN"]))
        st.write("🟢 En tiempo:", len(df[df["Alerta"] == "🟢 EN TIEMPO"]))

        st.divider()

        st.subheader("📋 Embarques")

        st.dataframe(df, use_container_width=True)

        # DESCARGA
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar Excel", csv, "embarques.csv")

    # =========================
    # BUSCADOR
    # =========================
    elif menu == "🔍 Buscador":

        query = st.text_input("Buscar por cualquier campo")

        if query:
            resultado = df[df.apply(
                lambda row: query.lower() in str(row).lower(), axis=1
            )]

            st.dataframe(resultado)

            if not resultado.empty:
                selected = resultado.iloc[0]

                if st.button("🌐 Ver tracking"):
                    if selected["bl"]:
                        url = f"https://www.track-trace.com/container?number={selected['bl']}"
                        webbrowser.open(url)

    # =========================
    # CARGA
    # =========================
    elif menu == "📂 Cargar Excel":

        file = st.file_uploader("Sube tu Excel", type=["xlsx"])

        if file:
            data = load_excel(file)

            st.success(f"{len(data)} registros listos")

            if st.button("✅ Confirmar carga"):
                insert_data(data)
                st.success("Datos cargados")
                st.rerun()

# =========================
if __name__ == "__main__":
    main()
