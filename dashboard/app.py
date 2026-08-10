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

# ------------------------------------------------------------------ mascota
PLANETA_SVG = """
<svg width="150" height="150" viewBox="0 0 150 150" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="atmos" cx="35%" cy="35%">
      <stop offset="0%" stop-color="#7ec8ff"/>
      <stop offset="100%" stop-color="#1d4e89"/>
    </radialGradient>
    <radialGradient id="tierra" cx="40%" cy="35%">
      <stop offset="0%" stop-color="#5ac06b"/>
      <stop offset="55%" stop-color="#2e8b57"/>
      <stop offset="100%" stop-color="#145a32"/>
    </radialGradient>
  </defs>
  <circle cx="75" cy="75" r="62" fill="url(#atmos)" opacity="0.35"/>
  <circle cx="75" cy="75" r="50" fill="url(#tierra)"/>
  <path d="M35 88 Q55 70 78 80 Q100 90 118 72" stroke="#36c1a0" stroke-width="7"
        fill="none" opacity="0.85" stroke-linecap="round"/>
  <path d="M45 62 Q62 52 82 58 Q98 63 110 55" stroke="#d8f3dc" stroke-width="3"
        fill="none" opacity="0.6" stroke-linecap="round"/>
  <circle cx="105" cy="45" r="7" fill="#fffde7" opacity="0.9"/>
  <ellipse cx="75" cy="75" rx="52" ry="14" fill="none" stroke="#4d9bd6"
           stroke-width="2" opacity="0.7" transform="rotate(-8 75 75)"/>
  <circle cx="75" cy="75" r="52" fill="none" stroke="#bfe3ff" stroke-width="2"/>
</svg>
"""

st.markdown(
    f"""
    <div style="text-align:center; padding:8px;">
      {PLANETA_SVG}
      <h1 style="color:#1d4e89; font-family:sans-serif; margin:2px 0 0 0;">
        🌍 Terra Cognita</h1>
      <p style="color:#555; font-family:sans-serif; margin-top:0;">
        Agente espacial · IA local + DataHub MCP + Google Earth Engine</p>
    </div>
    """,
    unsafe_allow_html=True,
)


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
    from folium.plugins import Colormap

    with rasterio.open(ruta_tif) as src:
        arr = src.read(1)
        b = src.bounds
    lat0, lat1 = b.bottom, b.top
    lon0, lon1 = b.left, b.right
    m = folium.Map(location=[(lat0 + lat1) / 2, (lon0 + lon1) / 2], zoom_start=11)
    x = np.linspace(lon0, lon1, arr.shape[1])
    y = np.linspace(lat1, lat0, arr.shape[0])   # fila 0 = norte
    xx, yy = np.meshgrid(x, y)
    cmap = Colormap(colors=["#8B0000", "#FFD700", "#228B22"],
                    vmin=float(np.nanmin(arr)), vmax=float(np.nanmax(arr)))
    cmap.caption = "NDVI"
    m.add_child(cmap)
    folium.ImageOverlay(
        image=cmap(arr).reshape(arr.shape[0], arr.shape[1], 3),
        bounds=[[lat0, lon0], [lat1, lon1]], opacity=0.75,
    ).add_to(m)
    return m


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
        via = ("cerebro local" if not plan.get("ollama_error")
               else "heurística" if "Ollama" in str(plan.get("ollama_error"))
               else (plan.get("via", "heurística")))
        st.markdown("---")
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
            st.markdown("**Tendencia (área bajo umbral por día):**")
            st.dataframe(res["serie"], use_container_width=True)
            st.write(f"Delta: {res.get('delta_pct'):+.1f}pp · "
                     f"NDVI medio {res.get('delta_media_ndvi'):+.3f} · "
                     f"Conclusión: {res.get('tendencia')}")

        if res.get("raster") and Path(res["raster"]).exists():
            st.markdown("**Mapa NDVI (raster analizado):**")
            try:
                m = _mapa_ndvi(res["raster"])
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