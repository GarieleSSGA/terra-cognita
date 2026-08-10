# 🧪 DEMO TEST SCRIPT — Terra Cognita

Ordered tests (from the simplest to the most impressive) with exact
steps and expected results. All from the repo root, with Docker up and
the MCP server running.

**Always first:** `Remove-Item Env:CURL_CA_BUNDLE`

## 0. System status

```powershell
# 5 healthy containers:
docker ps
# endpoints respond:
(Invoke-WebRequest http://localhost:8000/health -UseBasicParsing).StatusCode   # 200 MCP
(Invoke-WebRequest http://localhost:9002 -UseBasicParsing).StatusCode          # 200 DataHub UI
```

**Expected:** 200 / 200 and 5 containers `Up`.

## 1. Point analysis (snapshot)

```powershell
.venv\Scripts\python.exe scripts\demo_rapida.py "cual es el NDVI de Lima"
```

**Expected:** plan via `opencode`, % below threshold, state OK or WATCH,
and a catalogued URN in DataHub at the end.

## 2. 7-day trend (the star)

```powershell
.venv\Scripts\python.exe scripts\demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"
```

**Expected:** table of 7 dates (area below threshold 37.7→40.8 %, declining
mean NDVI), delta +3.1 pp, "WATCH: slight deterioration", series catalogued
with multiple lineage and **a message on your Telegram** (formatted report
with table).

## 3. Another trend: 15 days (more deterioration)

```powershell
.venv\Scripts\python.exe scripts\demo_temporal.py "como esta evolucionando la sequia en Lima los ultimos 15 dias"
```

**Expected:** 15-raster series, larger delta, same structure.

## 4. Another index: rainfall (alert)

```powershell
.venv\Scripts\python.exe scripts\demo_rapida.py "cuanta lluvia caera en Iquitos"
```

**Expected:** `rainfall` plan, max value in mm; if it exceeds the threshold
(50 mm) → **Telegram ALERT** (🚨). This is the test that triggers a real alert.

## 5. Soil moisture

```powershell
.venv\Scripts\python.exe scripts\demo_rapida.py "como esta la humedad del suelo en Lima"
```

**Expected:** `soil moisture` plan, % of dry area, state OK/ALERT.

## 6. Dashboard + maps (visual, for the video)

```powershell
.venv\Scripts\python.exe -m streamlit run dashboard\app.py   # http://localhost:8501
```

1. Run "dame la vegetacion de Lima de los ultimos 7 dias".
2. **Expected:** metrics (analysis/zone/interpreter `opencode`), WATCH
   state, trend table, **2 charts** (area below threshold and NDVI),
   **day selector** (changes the map), folium map with green/yellow/red legend.

## 7. Narrated flow (to RECORD the video)

```powershell
.venv\Scripts\python.exe scripts\flujo_paso_a_paso.py --presentacion "dame la vegetacion de Lima de los ultimos 7 dias"
```

**Expected:** 8 stages with a 6 s pause and 🎙 narration next to each one:
query → interpretation → MCP context → rasters → computation → GEE code →
write-back → Telegram report. Explain each screen to the camera while it runs.

## 8. View the DataHub graph (key pitch figure)

1. Open **http://localhost:9002** → login `datahub` / `datahub`.
2. Search `tendencia` → open an `analisis_*_tendencia_*`.
3. **Lineage** tab → the summary points to its 7 daily rasters.
4. Search `lima` → total 29+ (the agent's accumulated memory).

**Expected:** visible graph with upstreams; that proves the agent
"writes memory with lineage" (hackathon criterion).

## 9. Robustness (sell it in the pitch)

| Test | How | Expected result |
|---|---|---|
| No MCP server | Kill the :8000 process, run the demo | The demo continues: context with notice, rest OK |
| No Ollama/API | Don't have ollama nor key | Via: opencode or heuristic; never hangs |
| Write-back down | Stop GMS, run the demo | Local fallback in `data/resultados_catalogados/` |

## 10. Telegram (reports)

1. Trend query → formatted report arrives (day-by-day table).
2. High-value rainfall query → 🚨 alert.
3. Or manually: `scripts` + "Send test message" button on the dashboard.

**Expected:** messages with readable text (no raw JSON or code).

---

**Video tip:** record in order 6 → 7 → 8 → 4: dashboard in action,
narrated flow (architecture), DataHub graph (memory with lineage) and
Telegram alert (loop closure).