"""Dashboard Streamlit: mapa + chat + resultados del agente."""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from terra_cognita.agent.orquestador import Orquestador

st.set_page_config(page_title="Terra Cognita", layout="wide")
st.title("Terra Cognita - Inteligencia Espacial")

consulta = st.chat_input("Pregunta geoespacial (ej: NDVI en Lima):")

if consulta:
    with st.spinner("El agente piensa..."):
        resultado = Orquestador().ejecutar(consulta)
    st.session_state["ultimo"] = resultado
    st.success(f"Zona: {resultado.get('zona')} | Estado: {resultado.get('estado')}")

ultimo = st.session_state.get("ultimo")
if ultimo:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Resultado")
        st.write(ultimo.get("estado"))
        st.write(ultimo.get("raster"))
    with col2:
        st.subheader("Resumen")

# TODO: renderizar raster como mapa (folium/plotly) y chat de sesion.

st.sidebar.header("Estado")
st.sidebar.write("DataHub : localhost:9002")
st.sidebar.write("Ollama  : localhost:11434")