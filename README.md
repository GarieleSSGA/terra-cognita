# 🌍 Terra Cognita

Spatial-intelligence agent that understands **natural-language queries**,
looks up the system's memory (DataHub via MCP), runs geospatial analysis
(NDVI, rainfall, soil moisture, NDWI, LST, EVI — single-date or time
series), **writes results back into the data graph with lineage**, and
closes the loop by sending **Telegram** alerts/reports, maps and a
dashboard.

**Problem it solves:** risk analysis for urban planners takes days
(fragmented data, complex GIS tooling, no context). Terra Cognita
reduces it to minutes: ask a question → get a map, values, trend and
alert.

**Hackathon:** DataHub Community Hackathon — Category: "Agents that do
real work".

## Live demo (quick)

- **Interactive simulation (EN):** https://garielessga.github.io/terra-cognita-live-demo/
- **Real run:** run the steps below.

```powershell
# 1) Start the stack (see docs/ESTADO.md for details)
Remove-Item Env:CURL_CA_BUNDLE     # ALWAYS first (broken CA in this environment)
docker start datahub-mysql-1 datahub-opensearch-1 datahub-kafka-broker-1 datahub-datahub-gms-quickstart-1 datahub-frontend-quickstart-1
Start-Process .venv\Scripts\mcp-server-datahub.exe -ArgumentList "--transport","http" -WindowStyle Hidden

# 2) Full pipeline with all 8 internal stages (for the jury/video)
.venv\Scripts\python.exe scripts\flujo_paso_a_paso.py "dame la vegetacion de Lima de los ultimos 7 dias"

# 3) Direct trend report
.venv\Scripts\python.exe scripts\demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"

# 4) Dashboard (map + chat + stack status)
.venv\Scripts\python.exe -m streamlit run dashboard\app.py  # -> http://localhost:8501
```

> The query language used in the examples is Spanish (the agent's demo
> language); the system accepts any language supported by the
> interpreter chain.

## Architecture

```
User (natural language)
   │
   ▼
[AGENT: opencode → local Ollama → API → heuristic]   ← chain that never breaks
   │  "plan": {analysis, zone, days}
   ├──► [DataHub MCP :8000]  context: datasets/schema/lineage (no hallucination)
   ├──► [synthetic rasters | real GEE (Sentinel-2/CHIRPS/SMAP/MODIS)]
   ├──► [computing: % below threshold, means, delta, trend]
   ├──► [auto-generated GEE code: small bbox + getDownloadURL]
   ├──► [DataHub write-back: 1 dataset per date + upstreamLineage]
   └──► [Telegram: reasoned alert | Dashboard: map + chat + trend]
```

Step-by-step flow (with code): [`docs/FLUJO.md`](docs/FLUJO.md).
Benefits mapped to the hackathon criteria:
[`docs/BENEFICIOS.md`](docs/BENEFICIOS.md).

## Requirements

- Docker Desktop (DataHub at `http://localhost:9002`, GMS :8080)
- Python 3.11 (use `.venv\Scripts\python.exe` — system Python 3.14 does NOT work)
- Optional: Ollama (local model) or opencode (AI interpreter without local RAM)

## Installation

```bash
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
copy config\config.example.yaml config\config.yaml   # then fill in tokens
```

## Repository structure

```
terra_cognita/
├── agent/          # Orchestrator: interpreters (opencode/Ollama/API/heuristic)
├── datahub_mcp/    # DataHub MCP client (search, schema, lineage)
├── geo/            # Synthetic data, GEE (auto-generated JS), indices
├── alertas/        # Reports + Telegram bot
├── datahub_write/  # Write-back of results to the graph (lineage)
├── dashboard/      # Visual frontend (folium map + chat + trend)
├── config/         # config.yaml (out of git) + config.example.yaml
├── scripts/        # flujo_paso_a_paso, demo_temporal, demo_rapida, probar_mcp
├── examples/       # Real agent outputs (folder required by DataHub)
└── docs/           # Status, changelog, flow, benefits, MCP docs
```

## License

Apache License 2.0