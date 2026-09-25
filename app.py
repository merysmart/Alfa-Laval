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

# ========== Cargar precios y factores desde Secrets ==========
precios_secret = st.secrets["precios"]

precios = {}
for clave, datos in precios_secret.items():
    if hasattr(datos, "get") and datos.get("nombre") and datos.get("bastidor"):
        precios[datos["nombre"]] = {
            "bastidor": float(datos["bastidor"]),
            "placa": float(datos["placa"]),
        }

if not precios:
    st.error("No se han encontrado precios configurados. Avisa al administrador.")
    st.stop()

FACTOR_1 = float(precios_secret["FACTOR_1"])
FACTOR_2 = float(precios_secret["FACTOR_2"])
DESCUENTO = float(precios_secret["DESCUENTO"])

# ========== Funciones auxiliares ==========
def redondear_a_25_superior(valor):
    """Redondea siempre hacia arriba al múltiplo de 25 más cercano."""
    return int(math.ceil(valor / 25.0) * 25)

def formatear_euros(valor, decimales=0):
    """Devuelve el número en formato español: 1.234,56 €"""
    if decimales == 0:
        return f"{int(valor):,}".replace(",", ".") + " €"
    else:
        return f"{valor:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"

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

        # Redondeo SOLO del precio bruto, al múltiplo de 25 por arriba
        precio_bruto_redondeado = redondear_a_25_superior(precio_bruto)

        # El descuento se aplica sobre el bruto YA redondeado, sin redondear
        precio_final = precio_bruto_redondeado * (1 - DESCUENTO)

        # Mostrar resultados
        st.success(f"💰 Precio sin descuento: {formatear_euros(precio_bruto_redondeado, 0)}")
        st.success(f"🎉 Precio con descuento (50%): {formatear_euros(precio_final, 2)}")

        # Guardar en Google Sheets
        nueva_fila = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": usuario,
            "tipo": tipo,
            "placas": placas,
            "precio_bruto": precio_bruto_redondeado,
            "precio_final": round(precio_final, 2),
        }
        try:
            df = conn.read()
            nueva_fila_df = pd.DataFrame([nueva_fila])
            df = pd.concat([df, nueva_fila_df], ignore_index=True)
            conn.update(data=df)
            st.caption("✅ Registro guardado.")
        except Exception as e:
            st.caption(f"⚠️ No se pudo guardar el registro: {e}")
