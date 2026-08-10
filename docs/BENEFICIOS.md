# 🌎 Terra Cognita — BENEFITS

Agentic geospatial system: natural-language query → AI spatial analysis →
memory with lineage (DataHub) → alerts (Telegram). Designed for the
hackathon criteria: innovation, social impact, real integration and a
live demo.

## 1. Capable AI with ANY RAM budget

- **Cascading interpreter chain**: `opencode (powerful AI) → Ollama
  (private local model) → LLM API → heuristic`. The system NEVER hangs:
  if an interpreter is slow, the next one takes over and the demo always
  finishes.
- On an 8 GB RAM machine (like the demo one, with Docker eating almost
  everything), the agent is STILL smart: it uses opencode (~0 local RAM) —
  proof that "you can have a powerful geo-agent without a GPU".
- On a powerful machine (e.g. core i7 with 16+ GB), `Ollama` activates and
  all reasoning is 100 % local and private.

## 2. An agent that does NOT hallucinate (real memory with DataHub)

- Before answering, the agent **queries DataHub via MCP**: which datasets
  exist, which columns they have and where they come from (lineage).
- Reasoning starts from the **real graph**, not from "what the model thinks".
- Every analysis **is written back to DataHub with lineage**: one dataset
  per date + summary with `upstreamLineage`. Report numbers can be traced
  to their source raster — full audit trail.

## 3. From query to real data (Google Earth Engine)

- The agent **generates ad-hoc GEE JavaScript code** for each query:
  different per analysis (NDVI, CHIRPS rainfall, SMAP soil moisture, NDWI,
  MODIS LST, EVI), zone and dates.
- Small zone (~2 km) by default: fast downloads within the free quota.
  With `getDownloadURL` the code downloads the raster and the pipeline
  processes it the same way (synthetic and real share the same analysis).

## 4. Early warning with agent decision

- The agent **reasons about the result** and decides what to report:
  ALERT (risk), WATCH or OK — and optionally reports every query to
  Telegram (`reporte_siempre: true`).
- Not a fixed button: the same AI that understood the query decides the
  message, closing the action → notification loop.

## 5. Complete visualization

- **Streamlit dashboard**: NDVI map with legend + chat + daily trend
  (table and conclusion) + live stack status + linked DataHub UI.
- **`scripts/flujo_paso_a_paso.py`**: shows all 8 internal stages with
  real prints — perfect to explain the architecture to the jury.

## 6. Reproducibility and robustness

- Synthetic demo data → reproducible demo without depending on external
  APIs that fail or lag; the code for real data (GEE) changes in one line
  (`source_default: gee`).
- Cascading fallbacks: MCP down → continues with local context;
  failed write-back → local fallback without breaking the flow.
- Environment error log (`docs/BITACORA.md`) documenting every trap and
  its fix.

## Impact map (hypothesis)

| Problem | Terra Cognita |
|---------|---------------|
| Slow, manual monitoring | Natural-language query, answer in minutes |
| Non-expert remote-sensing eye | The agent translates to indices and thresholds |
| Results without traceability | Everything stays in DataHub with lineage |
| Generic alerts | Message reasoned by the agent by severity |
| Infrastructure cost | Local AI / opencode on common machines |