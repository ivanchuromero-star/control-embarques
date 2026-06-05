import sqlite3
import pandas as pd
import streamlit as st

# =========================
# DB
# =========================
DB_PATH = "embarques.db"

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
# LECTOR INTELIGENTE
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
        st.error("❌ No se encontró la tabla en el Excel")
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
# SEMÁFORO
# =========================
def estado(avance):
    if avance >= 80:
        return "🟢 ALTO"
    elif avance >= 50:
        return "🟡 MEDIO"
    return "🔴 BAJO"

# =========================
# APP
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

    # 🔥 SESSION STATE (FIX CLAVE)
    if "data" not in st.session_state:
        df = pd.read_sql_query("SELECT * FROM embarques", conn)
        st.session_state.data = df
    else:
        df = st.session_state.data

    # =========================
    # DASHBOARD
    # =========================
    if menu == "📊 Dashboard":

        if df.empty:
            st.warning("No hay datos")
            return

        df["Estado"] = df["avance"].apply(estado)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", len(df))
        col2.metric("Liberados", len(df[df["status"] == "LIBERADOS"]))
        col3.metric("Pendientes", len(df[df["status"] == "PENDIENTE"]))
        col4.metric("Avance Promedio", f"{df['avance'].mean():.1f}%")

        st.divider()

        st.dataframe(df, use_container_width=True)

        # DESCARGA
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar Excel", csv, "embarques.csv")

    # =========================
    # BUSQUEDA
    # =========================
    elif menu == "🔍 Búsqueda":

        if df.empty:
            st.warning("No hay datos")
            return

        query = st.text_input("Buscar")

        if query:
            res = df[df.apply(
                lambda row: query.lower() in str(row).lower(),
                axis=1
            )]
            st.dataframe(res)

    # =========================
    # CARGA
    # =========================
    elif menu == "📂 Cargar Excel":

        file = st.file_uploader("Sube tu Excel", type=["xlsx"])

        if file:
            data = load_excel(file)

            st.write(f"📊 Registros detectados: {len(data)}")

            if len(data) > 0:
                if st.button("✅ Confirmar carga"):

                    insert_data(data)

                    df_new = pd.DataFrame(data, columns=[
                        "factura","tracking","bl","booking","status",
                        "proveedor","po","cliente","naviera",
                        "eta","llegada","avance"
                    ])

                    # 🔥 GUARDAR EN MEMORIA
                    st.session_state.data = df_new

                    st.success("✅ Datos cargados correctamente")
                    st.info("👉 Ve al Dashboard")

# =========================
if __name__ == "__main__":
    main()
