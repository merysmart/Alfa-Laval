import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

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

# ========== Formulario ==========
st.title("Calculadora interna")

usuario = st.text_input("Tu nombre")
a = st.number_input("Valor A", value=0.0)
b = st.number_input("Valor B", value=0.0)

if st.button("Calcular"):
    if not usuario.strip():
        st.warning("Escribe tu nombre antes de calcular.")
    else:
        try:
            coef = float(st.secrets["COEFICIENTE"])  # conversión forzada
        except (KeyError, ValueError):
            st.error("Error de configuración. Avisa al administrador.")
            st.stop()

        resultado = a * coef + b / 4
        st.success(f"Resultado: {resultado:.4f}")

        # Guardar en Google Sheets (pandas moderno → pd.concat)
        nueva_fila = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": usuario,
            "valor_a": a,
            "valor_b": b,
            "resultado": round(resultado, 4),
        }
        try:
            df = conn.read()
            nueva_fila_df = pd.DataFrame([nueva_fila])
            df = pd.concat([df, nueva_fila_df], ignore_index=True)
            conn.update(data=df)
            st.caption("✅ Registro guardado.")
        except Exception as e:
            st.caption(f"⚠️ No se pudo guardar el registro: {e}")
