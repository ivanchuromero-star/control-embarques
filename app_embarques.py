import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Embarques PRO",
    layout="wide"
)

# =====================================
# FUNCIONES
# =====================================

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
    else:
        return "🔴 BAJO"


# =====================================
# LECTOR EXCEL ROBUSTO
# =====================================

def load_excel(file):

    try:

        # Leer archivo completo sin encabezados
        df_raw = pd.read_excel(file, header=None)

        st.subheader("🔎 Diagnóstico Excel")

        st.write("Primeras filas encontradas:")
        st.dataframe(df_raw.head(10))

        start_row = None

        # Buscar fila que contenga FACTURA
        for i, row in df_raw.iterrows():

            texto = " ".join(
                row.fillna("").astype(str)
            ).upper()

            if "FACTURA" in texto:
                start_row = i
                break

        st.write("Fila detectada como encabezado:", start_row)

        if start_row is None:
            st.error(
                "❌ No se encontró una fila con la palabra FACTURA"
            )
            return pd.DataFrame()

        # Volver a leer usando esa fila como encabezado
        df = pd.read_excel(
            file,
            header=start_row
        )

        # Limpiar nombres de columnas
        df.columns = (
            df.columns.astype(str)
            .str.strip()
            .str.upper()
        )

        st.write("Columnas detectadas:")
        st.write(df.columns.tolist())

        df = df.fillna("")

        registros = []

        for _, row in df.iterrows():

            factura = clean(
                row.get("FACTURA", "")
            )

            if factura == "":
                continue

            registros.append({
                "factura": factura,
                "tracking": clean(row.get("TRACKING", "")),
                "bl": clean(row.get("BL", "")),
                "booking": clean(row.get("BOOKING", "")),
                "status": clean(row.get("STATUS", "")),
                "proveedor": clean(row.get("PROVEEDOR", "")),
                "po": clean(row.get("PO", "")),
                "cliente": clean(row.get("CLIENTE", "")),
                "naviera": clean(row.get("NAVIERA", "")),
                "eta": clean(row.get("ETA VERACRUZ", "")),
                "llegada": clean(row.get("LLEGADA LOSIFRA", "")),
                "avance": parse_avance(
                    row.get("% AVANCE", 0)
                )
            })

        resultado = pd.DataFrame(registros)

        st.success(
            f"✅ Registros procesados: {len(resultado)}"
        )

        return resultado

    except Exception as e:

        st.error(f"❌ Error leyendo Excel: {e}")

        return pd.DataFrame()


# =====================================
# SESSION STATE
# =====================================

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()

df = st.session_state.data


# =====================================
# TITULO
# =====================================

st.title("📦 CONTROL DE EMBARQUES PRO")


# =====================================
# MENU
# =====================================

menu = st.sidebar.radio(
    "Menú",
    [
        "📊 Dashboard",
        "🔍 Búsqueda",
        "📂 Cargar Excel"
    ]
)


# =====================================
# DASHBOARD
# =====================================

if menu == "📊 Dashboard":

    st.write(
        f"📊 Registros en memoria: {len(df)}"
    )

    if df.empty:

        st.warning(
            "⚠️ No hay datos cargados"
        )

    else:

        df["estado"] = df["avance"].apply(
            estado
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total",
            len(df)
        )

        col2.metric(
            "Alto",
            len(df[df["avance"] >= 80])
        )

        col3.metric(
            "Medio",
            len(
                df[
                    (df["avance"] >= 50)
                    & (df["avance"] < 80)
                ]
            )
        )

        col4.metric(
            "Bajo",
            len(df[df["avance"] < 50])
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Descargar CSV",
            csv,
            "embarques.csv"
        )


# =====================================
# BUSQUEDA
# =====================================

elif menu == "🔍 Búsqueda":

    if df.empty:

        st.warning(
            "⚠️ No hay datos cargados"
        )

    else:

        query = st.text_input(
            "Buscar factura, booking, BL, cliente..."
        )

        if query:

            resultado = df[
                df.apply(
                    lambda row:
                    query.lower()
                    in str(row).lower(),
                    axis=1
                )
            ]

            st.write(
                f"Resultados: {len(resultado)}"
            )

            st.dataframe(
                resultado,
                use_container_width=True
            )


# =====================================
# CARGA EXCEL
# =====================================

elif menu == "📂 Cargar Excel":

    file = st.file_uploader(
        "Selecciona un archivo Excel",
        type=["xlsx", "xls"]
    )

    if file is not None:

        st.info(
            f"Archivo cargado: {file.name}"
        )

        df_new = load_excel(file)

        st.write(
            f"📊 Registros encontrados: {len(df_new)}"
        )

        if not df_new.empty:

            st.subheader("Vista previa")

            st.dataframe(
                df_new.head(20),
                use_container_width=True
            )

            if st.button(
                "✅ Confirmar carga"
            ):

                st.session_state.data = (
                    df_new.copy()
                )

                st.success(
                    "Datos cargados correctamente"
                )

                st.rerun()
