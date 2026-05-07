import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import uuid
import os
import random
import streamlit.components.v1 as components

# --- CONFIGURACIÓN BASE DE DATOS ---
DB_NAME = "ilusion_v14.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventario 
                          (producto TEXT, modelo TEXT, color TEXT, talla TEXT, 
                           stock INTEGER, p_compra REAL, p_venta REAL, imagen TEXT,
                           PRIMARY KEY (producto, modelo, color, talla))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS ventas 
                          (transaccion_id TEXT, fecha TEXT, hora TEXT, producto TEXT, modelo TEXT, 
                           color TEXT, talla TEXT, cantidad INTEGER, p_venta REAL, total REAL, estado TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS apartados 
                          (id TEXT, cliente TEXT, fecha TEXT, producto TEXT, modelo TEXT, 
                           color TEXT, talla TEXT, cantidad INTEGER, estado TEXT)''')
        conn.commit()

def run_query(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()

def get_df(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params)

# --- CARGA DE 70 REGISTROS ÚNICOS (1 AL 70) ---
def cargar_70_datos_unicos():
    productos_lista = ["Bra Push Up", "Panty Encaje", "Faja Reductora", "Pijama Seda", "Baby Doll", "Bra Deportivo", "Body Control", "Bralette Lux"]
    colores = ["Negro", "Blanco", "Nude", "Rojo", "Azul", "Rosa", "Vino", "Gris", "Beige", "Lila"]
    tallas = ["CH", "M", "G", "XG", "32B", "34B", "36B", "38B"]

    datos_inventario = []
    
    for i in range(1, 71):
        prod = random.choice(productos_lista)
        modelo = f"MOD-{i:03d}"  # Crea MOD-001, MOD-002... hasta MOD-070
        color = random.choice(colores)
        talla = random.choice(tallas)
        stock = random.randint(10, 50)
        p_compra = round(random.uniform(100.0, 400.0), 2)
        p_venta = round(p_compra * 1.75, 2)
        
        datos_inventario.append((prod, modelo, color, talla, stock, p_compra, p_venta, ""))

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.executemany('INSERT OR REPLACE INTO inventario VALUES (?,?,?,?,?,?,?,?)', datos_inventario)
        conn.commit()

# --- FUNCIÓN DE IMPRESIÓN ---
def ejecutar_impresion(html_content):
    unique_id = str(uuid.uuid4())[:8]
    component_script = f"""
    <div id="ticket-{unique_id}" style="display:none;">{html_content}</div>
    <script>
        (function() {{
            var content = document.getElementById('ticket-{unique_id}').innerHTML;
            var win = window.open('', 'PRINT', 'height=600,width=400');
            win.document.write('<html><head><title>Imprimir</title></head><body>' + content + '</body></html>');
            win.document.close();
            win.focus();
            win.print();
            win.close();
        }})();
    </script>
    """
    components.html(component_script, height=0)

def generar_ticket_html(titulo, id_doc, items, total, cliente=None):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    rows = "".join([f"<tr><td>{it['modelo']}</td><td align='center'>{it['cantidad']}</td><td align='right'>${it['subtotal']:,.2f}</td></tr>" for it in items])
    return f"""
    <div style="font-family: 'Courier New', monospace; width: 250px; padding: 10px; background: white; color: black; border: 1px solid #ddd;">
        <center><h2 style="margin:0;">ILUSIÓN</h2><p style="font-size:12px; margin:0;">Punto de Venta</p></center>
        <hr>
        <p style="font-size:11px;"><b>{titulo}</b>: #{id_doc}<br><b>Fecha:</b> {fecha}</p>
        {f'<p style="font-size:11px;"><b>Cliente:</b> {cliente}</p>' if cliente else ''}
        <table style="width:100%; font-size:10px;">{rows}</table>
        <hr><h3 align="right">TOTAL: ${total:,.2f}</h3>
    </div>
    """

# --- INICIALIZACIÓN ---
st.set_page_config(page_title="Ilusion Pro V14", layout="wide")
init_db()

if 'carrito' not in st.session_state: st.session_state.carrito = []
if 'ticket_a_imprimir' not in st.session_state: st.session_state.ticket_a_imprimir = None

# --- NAVEGACIÓN ---
st.sidebar.title("SISTEMA ILUSION")
menu = ["📦 Inventario", "🛒 Punto de Venta", "📝 Apartados", "📊 Corte de Caja", "📉 Historial", "🛠 Admin"]
choice = st.sidebar.selectbox("Opciones", menu)

if st.session_state.ticket_a_imprimir:
    ejecutar_impresion(st.session_state.ticket_a_imprimir)
    st.session_state.ticket_a_imprimir = None

# --- SECCIONES ---
if choice == "📦 Inventario":
    st.header("Inventario de Prendas")
    df_inv = get_df("SELECT * FROM inventario")
    if df_inv.empty:
        st.info("Inventario vacío. Ve a 'Admin' para cargar los 70 registros.")
    else:
        st.dataframe(df_inv, use_container_width=True)

elif choice == "🛒 Punto de Venta":
    st.header("Nueva Operación")
    df_inv = get_df("SELECT * FROM inventario WHERE stock > 0")
    if not df_inv.empty:
        c1, c2 = st.columns(2)
        with c1:
            mod_sel = st.selectbox("Modelo", sorted(df_inv['modelo'].unique()))
            df_f = df_inv[df_inv['modelo'] == mod_sel]
            col_sel = st.selectbox("Color", sorted(df_f['color'].unique()))
            talla_sel = st.selectbox("Talla", sorted(df_f[df_f['color'] == col_sel]['talla'].unique()))
            item = df_f[(df_f['color'] == col_sel) & (df_f['talla'] == talla_sel)].iloc[0]
            
            st.info(f"Stock: {item['stock']} | Precio: ${item['p_venta']:,.2f}")
            cant = st.number_input("Cantidad", 1, int(item['stock']))
            
            if st.button("➕ Agregar al Carrito", use_container_width=True):
                st.session_state.carrito.append({
                    'producto': item['producto'], 'modelo': item['modelo'], 'color': item['color'],
                    'talla': item['talla'], 'cantidad': cant, 'precio': item['p_venta'], 'subtotal': item['p_venta']*cant
                })
                st.rerun()

        with c2:
            if st.session_state.carrito:
                st.table(pd.DataFrame(st.session_state.carrito)[['modelo', 'talla', 'cantidad', 'subtotal']])
                total_v = sum(i['subtotal'] for i in st.session_state.carrito)
                if st.button(f"✅ Finalizar Venta (${total_v:,.2f})", type="primary"):
                    t_id = str(uuid.uuid4())[:8].upper()
                    for i in st.session_state.carrito:
                        run_query("INSERT INTO ventas VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                                  (t_id, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), i['producto'], i['modelo'], i['color'], i['talla'], i['cantidad'], i['precio'], i['subtotal'], "COMPLETADA"))
                        run_query("UPDATE inventario SET stock = stock - ? WHERE modelo=? AND color=? AND talla=?", (i['cantidad'], i['modelo'], i['color'], i['talla']))
                    st.session_state.ticket_a_imprimir = generar_ticket_html("TICKET VENTA", t_id, st.session_state.carrito, total_v)
                    st.session_state.carrito = []
                    st.rerun()
    else: st.error("No hay stock disponible.")

elif choice == "📊 Corte de Caja":
    st.header("Corte de Caja")
    df_corte = get_df("""SELECT v.*, i.p_compra FROM ventas v 
                         LEFT JOIN inventario i ON v.modelo = i.modelo AND v.color = i.color AND v.talla = i.talla""")
    if not df_corte.empty:
        st.metric("Total Ventas", f"${df_corte['total'].sum():,.2f}")
        st.dataframe(df_corte, use_container_width=True)

elif choice == "🛠 Admin":
    st.header("Administración del Sistema")
    if st.button("🚀 CARGAR 70 REGISTROS (DEL 1 AL 70)"):
        cargar_70_datos_unicos()
        st.success("Se han cargado 70 modelos únicos (MOD-001 al MOD-070).")
        st.rerun()
    
    if st.button("🗑️ Limpiar Base de Datos"):
        run_query("DELETE FROM inventario")
        run_query("DELETE FROM ventas")
        st.warning("Base de datos vaciada.")
        st.rerun() 