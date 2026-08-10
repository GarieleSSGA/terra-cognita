# 📸 Galería del proyecto — imágenes a capturar (15 máx, 3:2 recomendado, ≤5 MB)

> Formato aceptado: **JPG / PNG / GIF** · Tamaño máx **5 MB** c/u ·
> Relación de aspecto recomendada: **3:2** (ej. 1500×1000 px).
> Sube de 10 a 15 imágenes; con 12 está perfecto.

## Imágenes que SÍ necesitamos (en orden de importancia)

> **Pie de página (caption)**: el formulario pide el texto en **inglés**.
> Copia el caption de la última columna junto a cada imagen que subas.

| # | Qué capturar | Dónde / cómo | Ratio ideal | **Caption (EN)** — copiar y pegar |
|---|--------------|--------------|-------------|-----------------------------------|
| 1 | **Dashboard con mapa NDVI** | `http://localhost:8501` — ejecuta `dame la vegetacion de Lima de los ultimos 7 dias`, espera el resultado y captura la sección con el mapa + métricas | 3:2 | `Terra Cognita dashboard: NDVI map of Lima with legend, metrics and agent chat.` |
| 2 | **Gráficos de tendencia** (pct bajo umbral + NDVI medio) | Mismo dashboard, scroll a los 2 gráficos de línea | 3:2 | `7-day vegetation trend: % of area below threshold and mean NDVI, day by day.` |
| 3 | **Tabla de tendencia + conclusión** (7 fechas, delta, OBSERVACIÓN) | Dashboard, scroll a la tabla | 3:2 | `Trend table for Lima: area below threshold rose from 37.7% to 40.8% (+3.1 pp) → state: WATCH.` |
| 4 | **Chat del agente respondido** (consulta + respuesta razonada) | Dashboard, sección del chat | 3:2 | `Natural-language query → reasoned answer by the agent (opencode interpreter).` |
| 5 | **Arquitectura del pipeline (consola)** | PowerShell: `.venv\Scripts\python.exe scripts\flujo_paso_a_paso.py "dame la vegetacion de Lima de los ultimos 7 dias"` — captura la ventana con las 8 etapas | 16:9 ok | `End-to-end pipeline in 8 stages: query → interpretation → DataHub context (MCP) → rasters → compute → GEE code → write-back → Telegram.` |
| 6 | **Grafo de linaje en DataHub** ⭐ | `http://localhost:9002` → login `datahub`/`datahub` → buscar `tendencia` → abrir `analisis_*_tendencia_*` → pestaña **Lineage** (flechas hacia los 7 rasters) | 3:2 | `Lineage in DataHub: the trend summary points to its 7 source rasters — the agent writes memory with full lineage.` |
| 7 | **Búsqueda en DataHub** (memoria del agente) | Buscar `lima` → lista de 29+ datasets | 3:2 | `The agent's memory: 29+ datasets catalogued by the agent in the DataHub graph.` |
| 8 | **Alerta Telegram (reporte)** 📱 | Tu teléfono/celular con el informe del bot `@ERRADICADORBOT` abierto | 9:16 (vertical, crop ok) | `Telegram alert: formatted daily report sent by the agent (per-day table + conclusion + DataHub URN).` |
| 9 | **Demo simulada interactiva** | `https://garielessga.github.io/terra-cognita-live-demo/` → botón **Run demo** a la mitad (pipeline animado) | 3:2 | `Interactive simulation: the agent pipeline running (LLM plan → DataHub MCP → NDVI compute).` |
| 10 | **Demo simulada completa** (mapa + TG + linaje) | Misma página, al final de la ejecución | 3:2 | `Interactive simulation result: NDVI map, trend chart, lineage and Telegram report — identical to the real run.` |
| 11 | **Config GEE / código generado** | Pantalla de `codigo_gee_ndvi.js` en tu editor, o la sección "GEE code" si tu dashboard lo muestra | 3:2 | `Auto-generated Google Earth Engine code: small bbox + getDownloadURL to fetch real Sentinel-2 data.` |
| 12 | **Screenshots de la demo real?** (TG + mapa en una) | Si quieres llegar a 12-15: recorta capturas del video o de la demo simulada en distintos días (selectbox de día) | 3:2 | `NDVI map for a different day of the series (day selector) — same map, different date.` |

## Tips

- **3:2:** si la captura sale de otra proporción, recórtala con Paint / Photos antes de subir (1500×1000 estándar).
- **Sin caras/leaks:** no muestres el token de Telegram ni credenciales (las URNs están bien).
- **Orden:** sube como imagen 1 la más impactante (mapa + tendencia) — es la portada del proyecto.
- **Ya hay 8 capturas automáticas** en `docs/formulario/galeria/` (01_dashboard_inicio, 03_dashboard_mapas, 07_datahub_home, 08_datahub_search, 09_demo_inicio, 10_demo_pipeline, 12_demo_completa) por si quieres usarlas como base o completar con las manuales.

## Checklist final

- [ ] Mapa NDVI + métricas (1)
- [ ] Gráficos de tendencia (2)
- [ ] Tabla + conclusión (3)
- [ ] Chat del agente (4)
- [ ] Consola pipeline 8 etapas (5)
- [ ] Lineage DataHub ⭐ (6)
- [ ] Búsqueda DataHub (7)
- [ ] Telegram real (8)
- [ ] Demo simulada (9 y 10)
- [ ] Código GEE (11)
- [ ] Extra: 1-3 más a tu gusto (12)