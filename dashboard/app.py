"""Terra Cognita — Dashboard Streamlit.

Interfaz del agente espacial: chat en espanol -> plan (Ollama|API|heuristica)
-> contexto DataHub (MCP) -> analisis -> mapa -> codigo GEE -> write-back.

Ejecutar:  streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.stdout.reconfigure(line_buffering=True)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Terra Cognita", page_icon="🛰️", layout="wide")

st.html("""
<style>
  .stApp {
    background: radial-gradient(1200px 600px at 20% -10%, #12303f 0%, #0e1117 45%);
    font-family: 'Segoe UI', system-ui, sans-serif;
  }
  [data-testid="stAppViewContainer"] {
    background: radial-gradient(1200px 600px at 20% -10%, #12303f 0%, #0e1117 45%);
  }
  h1 { font-weight: 800; letter-spacing: -0.5px; }
  h1, h2, h3 { color: #36c1a0 !important; }
  [data-testid="stMetric"] {
    background: linear-gradient(160deg, #13202c 0%, #0d141d 100%);
    border: 1px solid #1e3a4a; border-radius: 14px; padding: 14px 16px;
    box-shadow: 0 4px 14px rgba(0,0,0,.35);
  }
  [data-testid="stMetricValue"] { color: #40e0b0; font-size: 1.7rem !important; }
  [data-testid="stMetricLabel"] { color: #7ec8ff; text-transform: uppercase;
    letter-spacing: .06em; font-size: .78rem !important; }
  .stButton>button {
    background: linear-gradient(90deg, #16a085, #36c1a0);
    color: #04121a; font-weight: 700; border: none; border-radius: 10px;
    padding: .55rem 2rem;
  }
  .stButton>button:hover { filter: brightness(1.12); }
  [data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(19,31,43,.55);
    border: 1px solid #1e3a4a; border-radius: 16px;
  }
  [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
  .stCaption { color: #7f94a5; }
</style>
""")

st.markdown("# 🌍 Terra Cognita")
st.markdown(
    "**Agente espacial** · IA (opencode/local) + DataHub MCP + Google Earth "
    "Engine · alertas Telegram")


# ------------------------------------------------------------------ estado
@st.cache_resource
def get_orq():
    from terra_cognita.agent.orquestador import Orquestador
    return Orquestador()


@st.cache_data(ttl=10)
def estado_stack():
    import requests
    def _vivo(url, tope=3):
        try:
            return requests.get(url, timeout=tope).status_code == 200
        except Exception:
            return False
    return {
        "mcp": _vivo("http://localhost:8000/health"),
        "gms": _vivo("http://localhost:8080/health"),
        "ollama": _vivo("http://localhost:11434/api/tags"),
    }


def _mapa_ndvi(ruta_tif):
    """Folium con colormap del raster y leyenda."""
    import numpy as np
    import rasterio
    import folium
    from folium.raster_layers import ImageOverlay
    from branca.colormap import LinearColormap

    with rasterio.open(ruta_tif) as src:
        arr = src.read(1)
        b = src.bounds
    lat0, lat1 = b.bottom, b.top
    lon0, lon1 = b.left, b.right
    m = folium.Map(location=[(lat0 + lat1) / 2, (lon0 + lon1) / 2], zoom_start=11)
    x = np.linspace(lon0, lon1, arr.shape[1])
    y = np.linspace(lat1, lat0, arr.shape[0])   # fila 0 = norte
    xx, yy = np.meshgrid(x, y)
    vmin, vmax = float(np.nanmin(arr)), float(np.nanmax(arr))
    cmap = LinearColormap(colors=["#8B0000", "#FFD700", "#228B22"],
                          vmin=vmin, vmax=vmax)
    cmap.caption = "NDVI"
    m.add_child(cmap)
    img = _rgbizar(arr, vmin, vmax)
    ImageOverlay(
        image=img,
        bounds=[[lat0, lon0], [lat1, lon1]], opacity=0.75,
    ).add_to(m)
    return m


def _rgbizar(arr, vmin, vmax, nan_color=(230, 230, 230)):
    """Convierte un raster a imagen RGB (HxWx3) con degradado rojo->amarillo->verde."""
    import numpy as np
    validos = ~np.isnan(arr)
    norm = np.zeros_like(arr, dtype=float)
    if vmax > vmin:
        norm[validos] = (arr[validos] - vmin) / (vmax - vmin)
    stops = np.array([[0x8B, 0x00, 0x00], [0xFF, 0xD7, 0x00], [0x22, 0x8B, 0x22]],
                     dtype=float)
    pos = np.clip(norm, 0, 1) * (len(stops) - 1)
    i0 = np.floor(pos).astype(int)
    i1 = np.minimum(i0 + 1, len(stops) - 1)
    frac = (pos - i0)[..., None]
    img = stops[i0] * (1 - frac) + stops[i1] * frac
    img[~validos] = nan_color
    return img.astype(np.uint8)


# ------------------------------------------------------------------ cuerpo
col_l, col_r = st.columns([2, 1])

with col_l:
    st.subheader("🤖 Pregúntale al agente")
    st.caption("Ej: 'dame la vegetacion de Lima de los ultimos 7 dias' · 'humedad en Lima' · 'lluvia en Iquitos'")
    consulta = st.text_input("Tu pregunta:", placeholder="dame el NDVI de Lima",
                             label_visibility="collapsed")
    if consulta and st.button("▶ Ejecutar", type="primary"):
        orq = get_orq()
        with st.spinner("Run Terra Cognita: plan -> contexto MCP -> análisis..."):
            res = orq.ejecutar(consulta)
        st.session_state["ultimo"] = res
    elif "ultimo" not in st.session_state:
        st.info("Escribe una consulta y ejecuta. El agente planifica, consulta "
                "DataHub vía MCP, analiza el raster y muestra mapa + código GEE.")

    res = st.session_state.get("ultimo")
    if res:
        plan = res.get("plan", {})
        via = plan.get("via", "heurística" if plan.get("ollama_error") else "cerebro local")
        st.markdown("---")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric("Análisis", plan.get("analisis", "?"))
            c2.metric("Zona", res.get("zona", "?"))
            c3.metric("Intérprete", via)
            d = res.get("contexto_datahub", {})
            if isinstance(d, dict) and d.get("error"):
                st.warning(f"DataHub: {d['error'][:90]}")
            else:
                st.success("DataHub consultado vía MCP (contexto sin alucinar)")

            estado = res.get("estado", "OK")
            if "ALERTA" in str(estado):
                st.error(f"🚨 {estado}")
            elif "OBSERVACION" in str(estado):
                st.warning(f"👀 {estado}")
            else:
                st.success(f"✅ {estado}")
            st.write(res.get("resumen", res.get("detalle", "")))

        if res.get("serie"):
            with st.container(border=True):
                st.markdown("**Tendencia (área bajo umbral y NDVI medio por día):**")
                st.dataframe(res["serie"], use_container_width=True)
                try:
                    import pandas as pd
                    df = pd.DataFrame(res["serie"])
                    if "fecha" in df.columns:
                        df = df.set_index("fecha")
                    gra1, gra2 = st.columns(2)
                    with gra1:
                        st.caption("Área bajo umbral %")
                        st.line_chart(df[["pct_bajo"]], height=220)
                    with gra2:
                        st.caption("NDVI medio")
                        st.line_chart(df[["media_ndvi"]], height=220)
                except Exception as exc:
                    st.warning(f"Grafico de tendencia no disponible: {exc}")
                st.write(f"Delta: {res.get('delta_pct'):+.1f}pp · "
                         f"NDVI medio {res.get('delta_media_ndvi'):+.3f} · "
                         f"Conclusión: {res.get('tendencia')}")

        dias_map = {}
        if res.get("serie") and res.get("serie_rasters"):
            for p, r in zip(res["serie"], res["serie_rasters"]):
                if Path(r).exists():
                    dias_map[p["fecha"]] = r
        ruta_mapa = res.get("raster")
        if dias_map:
            dia = st.selectbox("🗓️ Elige el día a visualizar:", list(dias_map.keys()))
            ruta_mapa = dias_map.get(dia)
        elif res.get("serie"):
            ruta_mapa = res.get("serie_rasters", [None])[-1] or res.get("raster")

        if ruta_mapa and Path(ruta_mapa).exists():
            with st.container(border=True):
                st.markdown(f"**Mapa NDVI** — `{Path(ruta_mapa).name}`")
                try:
                    m = _mapa_ndvi(ruta_mapa)
                    st.components.v1.html(m._repr_html_(), height=420)
                except Exception as exc:
                    st.warning(f"No se pudo renderizar el mapa: {exc}")

with col_r:
    st.subheader("🛰️ Estado del stack")
    st_ = estado_stack()
    st.write(f"• MCP Server (DataHub): {'✅ vivo' if st_['mcp'] else '❌ caído'}")
    st.write(f"• DataHub GMS: {'✅ vivo' if st_['gms'] else '❌ caído'}")
    st.write(f"• Ollama local: {'✅ vivo' if st_['ollama'] else '❌ apagado'}")
    st.caption("MCP + GMS requieren Docker; Ollama compite por RAM.")

    with st.expander("📦 DataHub (memoria del agente)"):
        try:
            orq = get_orq()
            r = orq.datahub.search_datasets("ndvi")
            total = 0
            for p in r.get("content", []):
                import json as _j
                try:
                    total = int(_j.loads(p[p.find("{"):]).get("total", 0))
                    break
                except Exception:
                    continue
            st.metric("Datasets en el grafo (búsqueda 'ndvi')", total)
        except Exception as exc:
            st.warning(str(exc)[:100])
        last_urn = st.session_state.get("ultimo", {}).get("urn_datahub")
        if last_urn:
            st.write(f"Último write-back: `{last_urn[:60]}…`")
        st.markdown("[Abrir DataHub UI :9002](http://localhost:9002)")

    with st.expander("🗨️ Código Google Earth Engine (generado por el agente)"):
        if res and res.get("codigo_gee"):
            st.code(res["codigo_gee"], language="javascript")
        else:
            st.caption("Ejecuta una consulta para ver el script GEE ad-hoc "
                       "(distinto por análisis/zona/fechas).")

    with st.expander("📣 Telegram"):
        cfg = get_orq().config["alertas"]
        if cfg.get("telegram_token") and cfg.get("chat_id"):
            st.success("Bot configurado ✅")
            if st.button("Enviar mensaje de prueba"):
                from terra_cognita.alertas.telegram_bot import enviar_mensaje
                try:
                    r = enviar_mensaje(cfg["telegram_token"], cfg["chat_id"],
                                       "🛰️ Terra Cognita online — bot de "
                                       "alerta conectado.")
                    st.success(f"Enviado ✓ (message_id {r.get('message_id')})")
                except Exception as exc:
                    st.error(f"Error: {exc}")
        else:
            st.warning("Sin token/chat_id en config.")

    with st.expander("⚙️ Config actual"):
        cfg = get_orq().config
        st.json({"modelo": cfg["ollama"]["model"],
                 "fuente_datos": cfg["gee"]["fuente_default"],
                 "proyecto_gee": cfg["gee"]["project_id"],
                 "umbral_ndvi": cfg["alertas"]["umbral_ndvi"],
                 "umbral_humedad": cfg["alertas"].get("umbral_humedad")})

st.caption("Terra Cognita · DataHub Community Hackathon · Apache 2.0")