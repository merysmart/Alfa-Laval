import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import math

st.set_page_config(page_title="Herramienta interna", page_icon="🔒")

# ========== Control de acceso ==========
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔒 Introduce la contraseña")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Entrar"):
        if pwd == st.secrets["PASSWORD"]:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.info("Nota: si recargas la página, tendrás que volver a introducirla.")
    st.stop()

# ========== Conexión con Google Sheets ==========
conn = st.connection("gsheets", type=GSheetsConnection)

# ========== Cargar precios desde Secrets ==========
precios = {}
for clave, datos in st.secrets["precios"].items():
    if isinstance(datos, dict) and "nombre" in datos:
        precios[datos["nombre"]] = {
            "bastidor": float(datos["bastidor"]),
            "placa": float(datos["placa"]),
        }

try:
    FACTOR_1 = float(st.secrets["FACTOR_1"])
    FACTOR_2 = float(st.secrets["FACTOR_2"])
    DESCUENTO = float(st.secrets["DESCUENTO"])
except (KeyError, ValueError):
    st.error("Error de configuración. Avisa al administrador.")
    st.stop()

# ========== Función de redondeo ==========
def redondear_a_25_superior(valor):
    """Redondea siempre hacia arriba al múltiplo de 25 más cercano."""
    return int(math.ceil(valor / 25.0) * 25)

# ========== Formulario ==========
st.title("Calculadora de intercambiadores")

usuario = st.text_input("Tu nombre")
tipo = st.selectbox("Tipo de intercambiador", list(precios.keys()))
placas = st.number_input("Número de placas", min_value=1, step=1, value=1)

if st.button("Calcular"):
    if not usuario.strip():
        st.warning("Escribe tu nombre antes de calcular.")
    else:
        precio_bastidor = precios[tipo]["bastidor"]
        precio_placa = precios[tipo]["placa"]

        # Fórmula oculta
        precio_bruto = (precio_bastidor + (precio_placa * placas)) * FACTOR_1 * FACTOR_2
        precio_con_descuento = precio_bruto * (1 - DESCUENTO)

        # Redondeo a múltiplo de 25 por arriba
        precio_bruto_redondeado = redondear_a_25_superior(precio_bruto)
        precio_final_redondeado = redondear_a_25_superior(precio_con_descuento)

        # Mostrar resultados
        st.success(f"💰 Precio sin descuento: {precio_bruto_redondeado:,} €".replace(",", "."))
        st.success(f"🎉 Precio con descuento (50%): {precio_final_redondeado:,} €".replace(",", "."))

        # Guardar en Google Sheets
        nueva_fila = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": usuario,
            "tipo": tipo,
            "placas": placas,
            "precio_bruto": precio_bruto_redondeado,
            "precio_final": precio_final_redondeado,
        }
        try:
            df = conn.read()
            nueva_fila_df = pd.DataFrame([nueva_fila])
            df = pd.concat([df, nueva_fila_df], ignore_index=True)
            conn.update(data=df)
            st.caption("✅ Registro guardado.")
        except Exception as e:
            st.caption(f"⚠️ No se pudo guardar el registro: {e}")
