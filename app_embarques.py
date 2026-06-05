import sqlite3
import pandas as pd
import streamlit as st

DB = "embarques.db"


# =========================
# DB
# =========================
def conn():
    return sqlite3.connect(DB, check_same_thread=False)


def init():
    with conn() as c:
        c.execute("""
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
            agente TEXT,
            ref_agente TEXT,
            naviera TEXT,
            pedimento TEXT,
            orden_compra TEXT,
            avance REAL
        )
        """)
        c.commit()


# =========================
# LIMPIADOR DE COLUMNAS
# =========================
def norm(c):
    return str(c).strip().upper()


def find(df, *keys):
    cols = {norm(c): c for c in df.columns}

    for k in keys:
        k = norm(k)
        for c in cols:
            if k in c:
                return df[cols[c]]
    return pd.Series([""] * len(df))


# =========================
# EXCEL IMPORT (ROBUSTO)
# =========================
def load_excel(file):
    df = pd.read_excel(file, sheet_name=0)

    df.columns = [norm(c) for c in df.columns]

    data = []

    for i in range(len(df)):
        data.append((
            str(find(df, "FACTURA").iloc[i]),
            str(find(df, "TRACK").iloc[i]),
            str(find(df, "BL").iloc[i]),
            str(find(df, "BOOKING").iloc[i]),
            str(find(df, "STATUS").iloc[i]),
            str(find(df, "PROVEEDOR").iloc[i]),
            str(find(df, "PO").iloc[i]),
            str(find(df, "CLIENTE").iloc[i]),
            str(find(df, "AGENTE").iloc[i]),
            str(find(df, "REF").iloc[i]),
            str(find(df, "NAVIERA").iloc[i]),
            str(find(df, "PEDIMENTO").iloc[i]),
            str(find(df, "ORDEN").iloc[i]),
            float(str(find(df, "AVANCE").iloc[i] or 0).replace("%","0"))
        ))

    return data


# =========================
# INSERT
# =========================
def save(data):
    with conn() as c:
        c.executemany("""
        INSERT INTO embarques (
            factura, tracking, bl, booking, status, proveedor, po, cliente,
            agente, ref_agente, naviera, pedimento, orden_compra, avance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        c.commit()


# =========================
# APP
# =========================
def main():
    st.set_page_config(page_title="Embarques", layout="wide")

    init()

    st.title("📦 Sistema de Embarques")

    file = st.file_uploader("Sube Excel", type=["xlsx"])

    if file:
        data = load_excel(file)
        save(data)
        st.success("Excel cargado correctamente")
        st.rerun()

    with conn() as c:
        df = pd.read_sql_query("SELECT * FROM embarques", c)

    st.subheader("Datos")
    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
