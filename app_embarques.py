import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path('comercio_embarques.db')


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS embarques (
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
        eta_veracruz TEXT,
        ven_demoras TEXT,
        pedimento TEXT,
        contenedores TEXT,
        sol_impuestos TEXT,
        pago_impuestos TEXT,
        carga_gondola TEXT,
        pantaco TEXT,
        ven_dem_pantaco TEXT,
        orden_compra TEXT,
        transporte_um TEXT,
        llegada_losifra TEXT,
        avance REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS ordenes_compra (
        oc_id INTEGER PRIMARY KEY AUTOINCREMENT,
        orden_compra TEXT,
        sku TEXT,
        descripcion TEXT,
        cantidad_pedida REAL,
        cantidad_recibida REAL DEFAULT 0,
        unidad TEXT,
        proveedor TEXT,
        cliente TEXT,
        estatus TEXT
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS detalle_embarque (
        detalle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        embarque_id INTEGER,
        orden_compra TEXT,
        sku TEXT,
        descripcion TEXT,
        cantidad_embarcada REAL,
        factura TEXT,
        bl TEXT,
        booking TEXT,
        pedimento TEXT,
        FOREIGN KEY (embarque_id) REFERENCES embarques(embarque_id)
        )"""
    )
    conn.commit()
    conn.close()


def seed_from_excel('OPERACIONES COMERCIO.xlsx'):
    if not Path(file_path).exists():
        return
    conn = get_conn()
    count_val = pd.read_sql_query('select count(*) as total from embarques', conn).iloc[0, 0]
    if count_val > 0:
        conn.close()
        return
    raw_df = pd.read_excel(file_path, sheet_name='EMBARQUES_PRO', header=None)
    data_df = raw_df.iloc[7:].copy()
    data_df.columns = data_df.iloc[0]
    data_df = data_df.iloc[1:].reset_index(drop=True)
    data_df = data_df.dropna(how='all')
    data_df.columns = [str(col).strip() for col in data_df.columns]
    data_df = data_df.loc[:, ~data_df.columns.duplicated()].copy()
    data_df = data_df[data_df['FACTURA'].notna()].copy()
    data_df = data_df[data_df['FACTURA'].astype(str).str.upper() != 'FACTURA'].copy()
    keep_cols = ['FACTURA','BL','BOOKING','STATUS','PROVEEDOR','PO','CLIENTE','AGENTE ADUANAL','REF. AGENTE','NAVIERA','ETA VERACRUZ','VEN. DEMORAS','PEDIMENTO','CONTENEDORES','SOL. IMPUESTOS','PAGO IMPUESTOS','CARGA GONDOLA','PANTACO','VEN. DEM. PANTACO','ORDEN DE COMPRA','TRANSPORTE UM','LLEGADA LOSIFRA','% AVANCE']
    data_df = data_df[keep_cols].copy()
    data_df.columns = ['factura','bl','booking','status','proveedor','po','cliente','agente_aduanal','ref_agente','naviera','eta_veracruz','ven_demoras','pedimento','contenedores','sol_impuestos','pago_impuestos','carga_gondola','pantaco','ven_dem_pantaco','orden_compra','transporte_um','llegada_losifra','avance']
    for col_name in data_df.columns:
        data_df[col_name] = data_df[col_name].astype(str).replace('nan', '').replace('NaT', '')
    data_df['avance'] = pd.to_numeric(data_df['avance'], errors='coerce')
    data_df.to_sql('embarques', conn, if_exists='append', index=False)
    conn.close()


def load_table(table_name):
    conn = get_conn()
    df_local = pd.read_sql_query('select * from ' + table_name, conn)
    conn.close()
    return df_local


def insert_record(table_name, record):
    conn = get_conn()
    cols_sql = ','.join(record.keys())
    placeholders = ','.join(['?'] * len(record))
    conn.execute('insert into ' + table_name + ' (' + cols_sql + ') values (' + placeholders + ')', list(record.values()))
    conn.commit()
    conn.close()


def actualizar_oc():
    conn = get_conn()
    detalle_df = pd.read_sql_query('select orden_compra, sku, sum(cantidad_embarcada) as recibido from detalle_embarque group by orden_compra, sku', conn)
    oc_df = pd.read_sql_query('select * from ordenes_compra', conn)
    if len(oc_df) > 0:
        merged_df = oc_df.merge(detalle_df, how='left', on=['orden_compra', 'sku'])
        merged_df['recibido'] = merged_df['recibido'].fillna(0)
        merged_df['estatus_calc'] = merged_df.apply(lambda row_val: 'COMPLETO' if row_val['recibido'] >= row_val['cantidad_pedida'] else 'PENDIENTE', axis=1)
        cur = conn.cursor()
        for _, row_val in merged_df.iterrows():
            cur.execute('update ordenes_compra set cantidad_recibida = ?, estatus = ? where oc_id = ?', (float(row_val['recibido']), row_val['estatus_calc'], int(row_val['oc_id'])))
        conn.commit()
    conn.close()


def panel_resumen():
    embarques_df = load_table('embarques')
    oc_df = load_table('ordenes_compra')
    detalle_df = load_table('detalle_embarque')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Embarques', len(embarques_df))
    c2.metric('OC registradas', len(oc_df))
    c3.metric('OC pendientes', int((oc_df['estatus'].fillna('PENDIENTE') != 'COMPLETO').sum()) if len(oc_df) > 0 else 0)
    c4.metric('Partidas embarcadas', len(detalle_df))
    st.subheader('Últimos embarques')
    st.dataframe(embarques_df.sort_values('embarque_id', ascending=False).head(10), use_container_width=True)


def panel_alta_embarque():
    st.subheader('Alta de embarque')
    with st.form('alta_embarque'):
        factura = st.text_input('Factura')
        bl = st.text_input('BL')
        booking = st.text_input('Booking')
        status = st.selectbox('Status', ['PENDIENTE', 'EN TRANSITO', 'LIBERADO', 'ENTREGADO'])
        proveedor = st.text_input('Proveedor')
        po = st.text_input('PO')
        cliente = st.text_input('Cliente', value='LOSIFRA')
        agente_aduanal = st.text_input('Agente aduanal')
        ref_agente = st.text_input('Referencia agente')
        naviera = st.text_input('Naviera')
        pedimento = st.text_input('Pedimento')
        orden_compra = st.text_input('Orden de compra')
        transporte_um = st.text_input('Transporte UM')
        submitted = st.form_submit_button('Guardar embarque')
        if submitted:
            insert_record('embarques', {
                'factura': factura, 'bl': bl, 'booking': booking, 'status': status, 'proveedor': proveedor, 'po': po, 'cliente': cliente,
                'agente_aduanal': agente_aduanal, 'ref_agente': ref_agente, 'naviera': naviera, 'eta_veracruz': '', 'ven_demoras': '',
                'pedimento': pedimento, 'contenedores': '', 'sol_impuestos': '', 'pago_impuestos': '', 'carga_gondola': '', 'pantaco': '',
                'ven_dem_pantaco': '', 'orden_compra': orden_compra, 'transporte_um': transporte_um, 'llegada_losifra': '', 'avance': 0
            })
            st.success('Embarque guardado correctamente')


def panel_alta_oc():
    st.subheader('Alta de orden de compra')
    with st.form('alta_oc'):
        orden_compra = st.text_input('Orden de compra')
        sku = st.text_input('SKU')
        descripcion = st.text_input('Descripción')
        cantidad_pedida = st.number_input('Cantidad pedida', min_value=0.0, step=1.0)
        unidad = st.text_input('Unidad', value='PZA')
        proveedor = st.text_input('Proveedor')
        cliente = st.text_input('Cliente', value='LOSIFRA')
        submitted = st.form_submit_button('Guardar orden de compra')
        if submitted:
            insert_record('ordenes_compra', {
                'orden_compra': orden_compra, 'sku': sku, 'descripcion': descripcion, 'cantidad_pedida': cantidad_pedida,
                'cantidad_recibida': 0, 'unidad': unidad, 'proveedor': proveedor, 'cliente': cliente, 'estatus': 'PENDIENTE'
            })
            st.success('Orden de compra guardada correctamente')


def panel_relacionar():
    st.subheader('Relacionar mercancía con embarque')
    embarques_df = load_table('embarques')
    if len(embarques_df) == 0:
        st.info('Primero registra un embarque')
        return
    option_map = {}
    for _, row_val in embarques_df.iterrows():
        label_val = str(row_val['embarque_id']) + ' | ' + str(row_val['factura']) + ' | ' + str(row_val['bl'])
        option_map[label_val] = int(row_val['embarque_id'])
    with st.form('relacionar'):
        selected_label = st.selectbox('Embarque', list(option_map.keys()))
        orden_compra = st.text_input('Orden de compra')
        sku = st.text_input('SKU')
        descripcion = st.text_input('Descripción')
        cantidad_embarcada = st.number_input('Cantidad embarcada', min_value=0.0, step=1.0)
        factura = st.text_input('Factura documento')
        bl = st.text_input('BL documento')
        booking = st.text_input('Booking documento')
        pedimento = st.text_input('Pedimento documento')
        submitted = st.form_submit_button('Guardar detalle')
        if submitted:
            insert_record('detalle_embarque', {
                'embarque_id': option_map[selected_label], 'orden_compra': orden_compra, 'sku': sku, 'descripcion': descripcion,
                'cantidad_embarcada': cantidad_embarcada, 'factura': factura, 'bl': bl, 'booking': booking, 'pedimento': pedimento
            })
            actualizar_oc()
            st.success('Detalle asociado correctamente')


def panel_cotejo():
    actualizar_oc()
    oc_df = load_table('ordenes_compra')
    detalle_df = load_table('detalle_embarque')
    if len(oc_df) == 0:
        st.info('No hay órdenes de compra registradas')
        return
    resumen_df = oc_df.copy()
    resumen_df['remanente'] = resumen_df['cantidad_pedida'].fillna(0) - resumen_df['cantidad_recibida'].fillna(0)
    resumen_df['estatus_visual'] = resumen_df['remanente'].apply(lambda val: 'INCOMPLETO' if val > 0 else 'COMPLETO')
    st.subheader('Cotejo contra recepción')
    st.dataframe(resumen_df[['orden_compra', 'sku', 'descripcion', 'cantidad_pedida', 'cantidad_recibida', 'remanente', 'estatus_visual', 'proveedor']], use_container_width=True)
    st.subheader('Trazabilidad documental')
    st.dataframe(detalle_df, use_container_width=True)


def panel_busqueda():
    st.subheader('Buscador general')
    query_val = st.text_input('Buscar por factura, BL, pedimento, booking u orden de compra')
    if query_val:
        embarques_df = load_table('embarques')
        detalle_df = load_table('detalle_embarque')
        emb_mask = embarques_df.astype(str).apply(lambda col_val: col_val.str.contains(query_val, case=False, na=False))
        st.write('Resultados en embarques')
        st.dataframe(embarques_df[emb_mask.any(axis=1)], use_container_width=True)
        if len(detalle_df) > 0:
            det_mask = detalle_df.astype(str).apply(lambda col_val: col_val.str.contains(query_val, case=False, na=False))
            st.write('Resultados en detalle')
            st.dataframe(detalle_df[det_mask.any(axis=1)], use_container_width=True)


def main():
    st.set_page_config(page_title='Control de Embarques', layout='wide')
    st.title('Control de comercio y rastreo de embarques')
    init_db()
    seed_from_excel('OPERACIONES COMERCIO.xlsx')
    module_val = st.sidebar.radio('Módulos', ['Resumen', 'Alta embarque', 'Alta orden de compra', 'Relacionar embarque', 'Cotejo y remanentes', 'Buscador'])
    if module_val == 'Resumen':
        panel_resumen()
    elif module_val == 'Alta embarque':
        panel_alta_embarque()
    elif module_val == 'Alta orden de compra':
        panel_alta_oc()
    elif module_val == 'Relacionar embarque':
        panel_relacionar()
    elif module_val == 'Cotejo y remanentes':
        panel_cotejo()
    else:
        panel_busqueda()


if __name__ == '__main__':
    main()
