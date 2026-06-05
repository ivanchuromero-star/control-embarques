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
        return float(val) if val else 0.0
    except:
        return 0.0

# =========================
# 🔥 LECTOR INTELIGENTE EXCEL
# (detecta donde empieza la tabla)
# =========================
def load_excel(file):
    df_raw = pd.read_excel(file, header=None)

    start_row = None
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains("FACTURA").any():
            start_row = i
            break

    if start_row is None:
        st.error("❌ No se encontró la tabla en el Excel")
        return []


