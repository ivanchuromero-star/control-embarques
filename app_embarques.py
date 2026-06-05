import pandas as pd
import streamlit as st

st.set_page_config(page_title="Embarques PRO", layout="wide")

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

def estado(avance):
    if avance >= 80:
        return "🟢 ALTO"
    elif avance >= 50:
        return "🟡 MEDIO"
    return "🔴 BAJO"


# =========================
# LECTOR EXCEL (ROBUSTO)
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
        st.error("❌ No se encontró encabezado en el Excel")
        return pd.DataFrame()

    df = pd.read_excel(file, header=start_row)
    df.columns = df.columns.astype(str).str.strip().str.upper()
    df = df.fillna("")

    registros = []

    for _, row in df.iterrows():
        factura = clean(row.get("FACTURA"))

        if factura == "":
            continue

        registros.append({
            "factura": factura,
            "tracking": clean(row.get("TRACKING")),
            "bl": clean(row.get("BL")),
            "booking": clean(row.get("BOOKING")),
            "status": clean(row.get("STATUS")),
            "proveedor": clean(row.get("PROVEEDOR")),
            "po": clean(row.get("PO")),
            "cliente": clean(row.get("CLIENTE")),
            "naviera": clean(row.get("NAVIERA")),
            "eta": clean(row.get("ETA VERACRUZ")),
            "llegada": clean(row.get("LLEGADA LOSIFRA")),
            "avance": parse_avance(row.get("% AVANCE"))
        })

    return pd.DataFrame(registros)


# =========================
# SESSION STATE
# =========================
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()

df = st.session_state.data


# =========================
# UI
# =========================
st.title("📦 CONTROL DE EMBARQUES PRO")

menu = st.sidebar.radio("Menú", [
    "📊 Dashboard",
    "🔍 Búsqueda",
    "📂 Cargar Excel"
])


# =========================
# DASHBOARD
# =========================
if menu == "📊 Dashboard":

    if df.empty:
        st.warning("No hay datos cargados")
    else:
        df["estado"] = df["avance"].apply(estado)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", len(df))
        col2.metric("Alto", len(df[df["avance"] >= 80]))
        col3.metric("Medio", len(df[(df["avance"] >= 50) & (df["avance"] < 80)]))
        col4.metric("Bajo", len(df[df["avance"] < 50]))

        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar CSV", csv, "embarques.csv")


# =========================
# BÚSQUEDA
# =========================
elif menu == "🔍 Búsqueda":

    if df.empty:
        st.warning("No hay datos")
    else:
        query = st.text_input("Buscar")

        if query:
            res = df[df.apply(
                lambda row: query.lower() in str(row).lower(),
                axis=1
            )]

            st.dataframe(res, use_container_width=True)


# =========================
# CARGA EXCEL
# =========================
elif menu == "📂 Cargar Excel":

    file = st.file_uploader("Sube tu Excel", type=["xlsx"])

    if file is not None:

        df_new = load_excel(file)

        st.write("📊 Registros detectados:", len(df_new))

        st.dataframe(df_new.head())

        if not df_new.empty:

            if st.button("✅ Confirmar carga"):

                st.session_state.data = df_new.copy()

                st.success("✅ Datos cargados correctamente")

                st.rerun()
