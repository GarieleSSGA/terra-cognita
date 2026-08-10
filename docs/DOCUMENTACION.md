# 📚 PROJECT DOCUMENTATION — Terra Cognita

Spatial intelligence agent: natural-language query → plan (AI) →
context from memory (DataHub via MCP) → geospatial analysis (NDVI,
rainfall, soil moisture, NDWI, LST, EVI) → write-back with lineage →
Telegram report + dashboard with map.

**Hackathon:** DataHub Community Hackathon — "Agents that do real work".

---

## 1. What we use and why (strengths of each piece)

| Component | Role in the system | Strength / contribution |
|---|---|---|
| **opencode (CLI)** | Main agent interpreter | Powerful AI with **0 local RAM**: on 8 GB machines (with Docker on top) the agent is still smart. Proves a powerful geo-agent doesn't need a GPU. |
| **Ollama + gemma3:1b** | Private local interpreter | When there is enough RAM, all reasoning is 100 % local/private (no data leaves the machine). |
| **LLM API (DeepSeek/OpenAI-compatible)** | Backup | Wildcard if opencode and Ollama are unavailable: works with any provider. |
| **Local heuristic** | Last resort | The demo **never hangs**: if every interpreter fails, a heuristic builds the plan and the flow always finishes. |
| **DataHub (GMS + UI)** | System memory | Dataset graph with **lineage**: every analysis is registered and traceable (what came from what). 29+ datasets, 5 trend summaries. |
| **DataHub MCP Server (HTTP :8000)** | Knowledge bridge | The agent **asks before acting**: search, get_entities, schema, lineage → it does not hallucinate, it reasons over the real graph. |
| **DataHub write-back** | Loop closure | Results **are written back into the graph** with `upstreamLineage`: other agents can inherit the analysis (central hackathon requirement). |
| **Google Earth Engine** | Real data | Auto-generated JS code (7 templates: NDVI/rain/soil moisture/NDWI/LST/EVI/series) with a small bbox (~2 km) and **automatic download** (`getDownloadURL`). |
| **Synthetic rasters** | Reproducible demo | Same pipeline as real data but without depending on APIs that fail or lag; switching to real GEE is one line (`source_default: gee`). |
| **Telegram bot** | Alert/report | The agent **decides the message**: reasoned alert by severity or always-report (`reporte_siempre: true`). Readable report with per-day table. |
| **Streamlit + folium + branca** | Dashboard | Interactive NDVI map with legend, day selector for the series, trend charts, live stack status. All local (localhost:8501). |
| **rasterio + numpy** | Geospatial computing | % of area below threshold, means, deviations, deltas and per-day trend over GeoTIFF. |
| **requests / yaml** | Infra | MCP/DataHub/Telegram calls and central config (secrets kept out of git). |

## 2. Architecture in one picture

```
User (Spanish)
   │
   ▼
[AGENT: opencode → Ollama → API → heuristic]      ← chain that never breaks
   │   plan: {analysis, zone, days}
   ├──► [DataHub MCP :8000]  which datasets exist? where do they come from?  (no hallucination)
   ├──► [synthetic rasters | real GEE Sentinel-2/CHIRPS/SMAP/MODIS]
   ├──► [computing: % below threshold, means, delta, trend, state]
   ├──► [auto-generated GEE code (download with getDownloadURL)]
   ├──► [DataHub write-back: dataset per date + upstreamLineage]
   └──► [Telegram: reasoned report] + [Dashboard: map/chat/charts]
```

## 3. Install from scratch

```powershell
# 1) Environment
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 2) Config (no secrets in git)
copy config\config.example.yaml config\config.yaml   # fill in tokens

# 3) DataHub (Docker Desktop)
docker start datahub-mysql-1 datahub-opensearch-1 datahub-kafka-broker-1 `
    datahub-datahub-gms-quickstart-1 datahub-frontend-quickstart-1
$env:DATAHUB_GMS_HOST="localhost"; $env:DATAHUB_GMS_PORT="8080"; $env:DATAHUB_GMS_PROTOCOL="http"
Start-Process .venv\Scripts\mcp-server-datahub.exe -ArgumentList "--transport","http" -WindowStyle Hidden

# 4) Useful commands
Remove-Item Env:CURL_CA_BUNDLE     # ALWAYS when starting a session (broken env CA)
.venv\Scripts\python.exe scripts\demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"
.venv\Scripts\python.exe scripts\flujo_paso_a_paso.py --presentacion "dame la vegetacion de Lima"
.venv\Scripts\python.exe -m streamlit run dashboard\app.py    # http://localhost:8501
```

## 4. Repository structure

```
terra_cognita/
├── terra_cognita/
│   ├── agent/          # orchestrator: interpreters + full loop
│   ├── datahub_mcp/    # HTTP MCP client (search, entities, lineage)
│   ├── datahub_write/  # write-back: escribir_resultado / escribir_serie
│   ├── geo/            # synthetic data, analysis, gee (JS code), gee_codegen
│   └── alertas/        # telegram_bot (sendMessage/sendPhoto/sendDocument)
├── dashboard/app.py    # Streamlit: map, chat, trend, status
├── scripts/            # flujo_paso_a_paso, demo_temporal, demo_rapida, probar_mcp
├── config/             # config.yaml (local, ignored) + config.example.yaml
├── docs/               # status, changelog, flow, benefits, documentation, tests
├── data/               # rasters, series, downloads
└── examples/           # agent outputs (folder required by DataHub)
```

## 5. FAQ

- **"29/30 datasets in the graph"?** Total datasets written by the agent
  (point analyses + trends + per-date rasters).
- **Does the DataHub UI ask for login?** quickstart default: `datahub` / `datahub`.
- **Is the displayed NDVI an average?** It is the raster of the selected day
  in the series (or the last day); with real GEE it would be the Sentinel-2
  period median.
- **Why is Ollama shown as "off"?** Docker consumes almost all RAM (8 GB);
  that is why the active interpreter is opencode (0 local RAM). With Docker
  off, Ollama works as the local interpreter.

See also: `docs/FLUJO.md` (pipelines), `docs/PRUEBAS.md` (test script),
`docs/BENEFICIOS.md` (benefits for the pitch), `docs/BITACORA.md`
(environment traps).