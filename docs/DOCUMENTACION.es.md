# 📚 DOCUMENTACIÓN DEL PROYECTO — Terra Cognita

Agente de inteligencia espacial: consulta en lenguaje natural → plan (IA) →
contexto en memoria (DataHub vía MCP) → análisis geoespacial (NDVI, lluvia,
humedad, NDWI, LST, EVI) → write-back con linaje → reporte Telegram +
dashboard con mapa.

**Hackathon:** DataHub Community Hackathon — "Agents that do real work".

---

## 1. Lo que usamos y por qué (bondades de cada pieza)

| Componente | Rol en el sistema | Bondad / aporte |
|---|---|---|
| **opencode (CLI)** | Intérprete principal del agente | IA potente con **0 RAM local**: en máquinas de 8 GB (con Docker encima) el agente sigue siendo inteligente. Demuestra que un geo-agente potente no requiere GPU. |
| **Ollama + gemma3:1b** | Intérprete local privado | Cuando hay RAM suficiente, todo el razonamiento es 100 % local/privado (sin enviar datos fuera). |
| **API LLM (DeepSeek/OpenAI-compatible)** | Respaldo | Comodín si opencode y Ollama no están: sigue funcionando con cualquier proveedor. |
| **Heurística local** | Último rescate | La demo **nunca se cuelga**: si todos los intérpretes fallan, una heurística arma el plan y el flujo termina siempre. |
| **DataHub (GMS + UI)** | Memoria del sistema | Grafo de datasets con **linaje**: cada análisis queda registrado y trazable (qué vino de qué). 29+ datasets, 5 de tendencia. |
| **MCP Server DataHub (HTTP :8000)** | Puente de conocimiento | El agente **pregunta antes de actuar**: search, get_entities, schema, lineage → no alucina, razona sobre el grafo real. |
| **DataHub write-back** | Cierre del ciclo | Los resultados **se escriben de vuelta al grafo** con `upstreamLineage`: otros agentes pueden heredar el análisis (requisito central del hackathon). |
| **Google Earth Engine** | Datos reales | Código JS auto-generado (7 plantillas: NDVI/lluvia/humedad/NDWI/LST/EVI/serie) con bbox pequeño (~2 km) y **descarga automática** (`getDownloadURL`). |
| **Rasters sintéticos** | Demo reproducible | Misma pipeline que los reales pero sin depender de APIs externas que fallan o demoran; cambiar a GEE real es una línea (`fuente_default: gee`). |
| **Telegram bot** | Alerta/reporte | El agente **decide el mensaje**: alerta razonada según severidad o reporte siempre (`reporte_siempre: true`). Informe legible con tabla por día. |
| **Streamlit + folium + branca** | Dashboard | Mapa NDVI interactivo con leyenda, selectbox por día de la serie, gráficos de tendencia, estado del stack en vivo. Todo local (localhost:8501). |
| **rasterio + numpy** | Cálculo geoespacial | % de área bajo umbral, medias, desvíos, deltas y tendencia por día sobre GeoTIFF. |
| **requests / yaml** | Infra | Llamadas MCP/DataHub/Telegram y configuración central (secretos fuera de git). |

## 2. Arquitectura en una imagen

```
Usuario (español)
   │
   ▼
[AGENTE: opencode → Ollama → API → heurística]      ← cadena que nunca se rompe
   │   plan: {analisis, zona, dias}
   ├──► [DataHub MCP :8000]  ¿qué datasets hay? ¿de dónde vienen?  (no alucina)
   ├──► [rasters sintéticos | GEE real Sentinel-2/CHIRPS/SMAP/MODIS]
   ├──► [cálculo: % bajo umbral, medias, delta, tendencia, estado]
   ├──► [código GEE auto-generado (descarga con getDownloadURL)]
   ├──► [write-back DataHub: dataset por fecha + upstreamLineage]
   └──► [Telegram: informe razonado] + [Dashboard: mapa/chat/gráficos]
```

## 3. Instalación desde cero

```powershell
# 1) Entorno
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2) Config (sin secretos en git)
copy config\config.example.yaml config\config.yaml   # rellenar tokens

# 3) DataHub (Docker Desktop)
docker start datahub-mysql-1 datahub-opensearch-1 datahub-kafka-broker-1 `
    datahub-datahub-gms-quickstart-1 datahub-frontend-quickstart-1
$env:DATAHUB_GMS_HOST="localhost"; $env:DATAHUB_GMS_PORT="8080"; $env:DATAHUB_GMS_PROTOCOL="http"
Start-Process .venv\Scripts\mcp-server-datahub.exe -ArgumentList "--transport","http" -WindowStyle Hidden

# 4) Comandos útiles
Remove-Item Env:CURL_CA_BUNDLE     # SIEMPRE al empezar sesión (CA del entorno rota)
.venv\Scripts\python.exe scripts\demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"
.venv\Scripts\python.exe scripts\flujo_paso_a_paso.py --presentacion "dame la vegetacion de Lima"
.venv\Scripts\python.exe -m streamlit run dashboard\app.py    # http://localhost:8501
```

## 4. Estructura del repo

```
terra_cognita/
├── terra_cognita/
│   ├── agent/          # orquestador: intérpretes + ciclo completo
│   ├── datahub_mcp/    # cliente MCP HTTP (search, entities, lineage)
│   ├── datahub_write/  # write-back: escribir_resultado / escribir_serie
│   ├── geo/            # sinteticos, analisis, gee (código JS), gee_codegen
│   └── alertas/        # telegram_bot (sendMessage/sendPhoto/sendDocument)
├── dashboard/app.py    # Streamlit: mapa, chat, tendencia, estado
├── scripts/            # flujo_paso_a_paso, demo_temporal, demo_rapida, probar_mcp
├── config/             # config.yaml (local, ignorado) + config.example.yaml
├── docs/               # ESTADO, BITACORA, FLUJO, BENEFICIOS, DOCUMENTACION, PRUEBAS
├── data/               # rasters, series, descargas
└── examples/           # salidas del agente (carpeta exigida por DataHub)
```

## 5. Resolver dudas frecuentes

- **¿Los 29/30 "datasets en el grafo"?** Total de datasets escritos por el
  agente (análisis puntuales + tendencias + rasters por fecha).
- **¿DataHub UI pide login?** quickstart por defecto: `datahub` / `datahub`.
- **¿El NDVI mostrado es promedio?** Es el raster del día seleccionado en la
  serie (o el último día); en GEE real sería la mediana de Sentinel-2 del período.
- **¿Por qué Ollama sale "apagado"?** Docker consume casi toda la RAM (8 GB);
  por eso el intérprete activo es opencode (0 RAM local). Con Docker apagado,
  Ollama funciona como intérprete local.

Véase también: `docs/FLUJO.md` (pipelines), `docs/PRUEBAS.md` (guion de
pruebas), `docs/BENEFICIOS.md` (bondades para el pitch), `docs/BITACORA.md`
(trampas del entorno).