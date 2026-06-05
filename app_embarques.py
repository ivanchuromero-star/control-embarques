import pandas as pd
import streamlit as st

st.set_page_config(page_title="Embarques PRO", layout="wide")

# =========================
# CACHE GLOBAL
# =========================
@st.cache_data
def guardar_df(df):
    return df

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
# LECTOR EXCEL
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
        st.error("❌ No se encontró tabla")
        return pd.DataFrame()

    df = pd.read_excel(file, header=start_row)
    df.columns = df.columns.astype(str).str.strip().str.upper()
    df = df.fillna("")

    registros = []

