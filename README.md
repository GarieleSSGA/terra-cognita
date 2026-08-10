# 🌍 Terra Cognita

Agente de **inteligencia espacial** que entiende consultas en lenguaje
natural, consulta la memoria del sistema (DataHub vía MCP), ejecuta análisis
geoespacial (NDVI, lluvia, humedad, NDWI, LST, EVI — puntual o tendencia),
**escribe los resultados de vuelta al grafo con linaje** y cierra el ciclo
enviando alertas/reportes por **Telegram**, con mapa y dashboard.

**Problema que resuelve:** el análisis de riesgo espacial para planificadores
urbanos toma días (datos fragmentados, SIG complejo, sin contexto). Terra
Cognita lo reduce a minutos: pregunta en español → respuesta con mapa,
valores, tendencia y alerta.

**Hackathon:** DataHub Community Hackathon — Categoría: "Agents that do real
work".

## Demo en vivo (rápida)

```powershell
# 1) Ranking del stack (ver docs/ESTADO.md para el detalle)
Remove-Item Env:CURL_CA_BUNDLE     # SIEMPRE primero (CA rota del entorno)
docker start datahub-mysql-1 datahub-opensearch-1 datahub-kafka-broker-1 datahub-datahub-gms-quickstart-1 datahub-frontend-quickstart-1
Start-Process .venv\Scripts\mcp-server-datahub.exe -ArgumentList "--transport","http" -WindowStyle Hidden

# 2) Flujo completo con las 8 etapas internas (para jurado/video)
.venv\Scripts\python.exe scripts\flujo_paso_a_paso.py "dame la vegetacion de Lima de los ultimos 7 dias"

# 3) Informe de tendencia directo
.venv\Scripts\python.exe scripts\demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"

# 4) Dashboard (mapa + chat + estado del stack)
.venv\Scripts\python.exe -m streamlit run dashboard\app.py  # -> http://localhost:8501
```

## Arquitectura

```
Usuario (español)
   │
   ▼
[AGENTE: opencode → Ollama local → API → heurística]   ← cadena que nunca se rompe
   │  "plan": {analisis, zona, dias}
   ├──► [DataHub MCP :8000]  contexto: datasets/schema/linaje (no alucina)
   ├──► [rasters sintéticos | GEE real (Sentinel-2/CHIRPS/SMAP/MODIS)]
   ├──► [cálculo: % bajo umbral, medias, delta, tendencia]
   ├──► [código GEE auto-generado: bbox pequeño + getDownloadURL]
   ├──► [write-back DataHub: 1 dataset por fecha + upstreamLineage]
   └──► [Telegram: alerta razonada | Dashboard: mapa + chat + tendencia]
```

Flujo detallado (paso a paso con código): [`docs/FLUJO.md`](docs/FLUJO.md).
Beneficios según criterios del hackathon: [`docs/BENEFICIOS.md`](docs/BENEFICIOS.md).

## Requisitos

- Docker Desktop (DataHub en `http://localhost:9002`, GMS :8080)
- Python 3.11 (usar `.venv\Scripts\python.exe` — el 3.14 del sistema NO sirve)
- Opcional: Ollama (modelo local) u opencode (intérprete IA sin RAM local)

## Instalación

```bash
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
copy config\config.example.yaml config\config.yaml   # y rellena tokens
```

## Estructura

```
terra_cognita/
├── agent/          # Orquestador: intérpretes (opencode/Ollama/API/heurística)
├── datahub_mcp/    # Cliente MCP de DataHub (search, schema, lineage)
├── geo/            # Sintéticos, GEE (código JS auto-generado), índices
├── alertas/        # Reportes + bot de Telegram
├── datahub_write/  # Write-back de resultados al grafo (linaje)
├── dashboard/      # Frontend visual (mapa folium + chat + tendencia)
├── config/         # config.yaml (fuera de git) + config.example.yaml
├── scripts/        # flujo_paso_a_paso, demo_temporal, demo_rapida, probar_mcp
├── examples/       # Outputs del agente (carpeta exigida por DataHub)
└── docs/           # ESTADO, BITACORA, FLUJO, BENEFICIOS, MCP_SERVERS
```

## Licencia

Apache License 2.0