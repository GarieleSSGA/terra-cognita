# ESTADO â€” Terra Cognita (DÃ­a 2, cierre)

Ãšltima sesiÃ³n: resuelto el "bug silencioso" de `ciclo_completo.py`, aÃ±adido
respaldo de interpretaciÃ³n por API LLM (`llm_api`), documentados los MCP
servers geoespaciales externos (docs/MCP_SERVERS.md) y construido el **modo
TENDENCIA** del agente espacial-temporal (serie de N dÃ­as + informe).

## ðŸ†• Modo TENDENCIA (nuevo hoy, verificado ejecutando)

`scripts/demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"`
produce un informe detallado: tabla por fecha (Ã¡rea bajo umbral %, NDVI medio,
barra visual), delta total, direcciÃ³n de la tendencia y conclusiÃ³n:

```
[Plan] ndvi en lima | dias=7
 Periodo: 2026-08-03 -> 2026-08-09 (7 dias)
 Cambio total: area bajo umbral 37.7% -> 40.8% (delta +3.1pp); NDVI medio -0.012
 Conclusion  : vegetacion estable. OBSERVACION: deterioro leve
```

Piezas:
- `terra_cognita/geo/sinteticos.py::generar_serie_ndvi` â€” N GeoTIFFs por fecha
  (foco de degradaciÃ³n creciente + declive global progresivo).
- `terra_cognita/geo/analisis.py::evaluar_tendencia` â€” serie pct/NDVI + delta +
  estado ALERTA/OBSERVACION/OK.
- `orquestador.ejecutar()` â€” si plan trae `dias` (>1) â†’ tendencia; si no â†’ snapshot.
- Prompts (Ollama y heurÃ­stica) entienden "ultimos N dias"/"evolucion".
- `scripts/demo_temporal.py` â€” informe en texto plano listo para copiar.

## Lo que quedÃ³ CORRIDO Y VERIFICADO hoy (evidencia REAL de DataHub)

- **Ciclo completo con DataHub arriba, de punta a punta**: contexto MCP,
  anÃ¡lisis 47.7%, **write-back real** (sin fallback local) creÃ³
  `analisis_lima_d6bf36` y la verificaciÃ³n MCP confirmÃ³ **total:5 datasets**
  en el grafo. Todo con prints en vivo (fix de flush).
- MCP server HTTP persistente + GMS 200 + 5 contenedores sanos.
- RAM libre tras el arranque: ~0.3 GB â†’ los imports van lento pero el ciclo
  termina (~3-4 min, la mayor parte en el timeout de Ollama).

## RESUMEN DEL DÃA

1. Causa raÃ­z del "hang": prints sin flush + proceso de 3-4.5 min = salida
   invisible al matar por timeout. NO era encoding.
2. Fix: flush en scripts + timeouts (Ollama 90s â†’ heurÃ­stica; MCP 45s) +
   write-back con fallback local que ya no crashea.
3. `llm_api`: intÃ©rprete de respaldo OpenAI-compatible (env LLM_API_KEY/BASE/MODEL)
   probado su skip correcto cuando no hay clave.
4. MCP externos: docs/MCP_SERVERS.md con 5 servidores evaluados + plan.
5. Modo tendencia: NUEVO y funcionando (arriba).

## Piezas tocadas hoy

- `scripts/ciclo_completo.py` â€” reescrito (decir() con flush, avisos claros).
- `terra_cognita/agent/orquestador.py` â€” cadena interpretar (Ollamaâ†’llm_apiâ†’
  heurÃ­stica), regex de dÃ­as, ejecutar() con rama tendencia.
- `terra_cognita/datahub_mcp/cliente.py` â€” asyncio.wait_for 45s.
- `terra_cognita/datahub_write/catalogar.py` â€” asegurar_raster_fuente dentro
  del try/except (fallback local, no crash).
- `terra_cognita/geo/sinteticos.py`, `geo/analisis.py` â€” serie + tendencia.
- `terra_cognita/config.py`/`config.yaml` â€” ollama.timeout_s, llm_api.
- `scripts/demo_rapida.py`, `scripts/probar_mcp.py` â€” line_buffering.
- `scripts/demo_temporal.py` â€” NUEVO: informe de tendencia.
- `docs/MCP_SERVERS.md` â€” NUEVO. `docs/ESTADO.md` â€” este.

## Comandos rÃ¡pidos

```powershell
Remove-Item Env:CURL_CA_BUNDLE   # SIEMPRE primero, por sesiÃ³n

# Toda la pila (Docker -> GMS -> MCP server -> demos)
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
docker start datahub-mysql-1 datahub-opensearch-1 datahub-kafka-broker-1 datahub-datahub-gms-quickstart-1 datahub-frontend-quickstart-1
$env:DATAHUB_GMS_HOST="localhost"; $env:DATAHUB_GMS_PORT="8080"; $env:DATAHUB_GMS_PROTOCOL="http"
Start-Process -FilePath "<ROOT>\.venv\Scripts\mcp-server-datahub.exe" -ArgumentList "--transport","http" -WindowStyle Hidden
# health: http://localhost:8080/health y http://localhost:8000/health

# Demos (el quoting de PowerShell con & NO se rompe; Start-Process SÃ parte args con espacios)
<ROOT>\.venv\Scripts\python.exe scripts\ciclo_completo.py "dame el NDVI de Lima"     # ciclo con DataHub
<ROOT>\.venv\Scripts\python.exe scripts\demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"
<ROOT>\.venv\Scripts\python.exe scripts\demo_rapida.py "cual es el NDVI de Lima"

# IntÃ©rprete por API (recomendado con Docker arriba, Ollama no aguanta la RAM):
$env:LLM_API_BASE="https://api.deepseek.com/v1"; $env:LLM_API_KEY="<clave>"; $env:LLM_API_MODEL="deepseek-chat"
```

## Trampas del entorno (vigentes del dÃ­a 1 + de hoy)

1. `CURL_CA_BUNDLE` roto â†’ Remove-Item Env:CURL_CA_BUNDLE.
2. PROJ_LIB/GDAL_DATA â†’ los limpia `terra_cognita/__init__.py`.
3. RAM 7.65 GB: Docker arriba = ~0.3 GB libres â†’ Ollama timeouts, imports lentos.
   Con Docker abajo hay espacio para Ollama (gemma3:1b) â€” elegir uno u otro.
4. **Start-Process parte argumentos con espacios** â†’ usar `& python.exe ...` con
   comillas para las demos.
5. No detener kafka-broker. Python 3.11 del venv es el bueno.

## Siguientes pasos (por orden)

1. ðŸ”´ Probar `llm_api` con clave real (le da al agente el "cerebro" estando
   Docker arriba; hoy cayÃ³ a heurÃ­stica por timeout de Ollama).
2. âœ… **SERIE temporal en DataHub â€” HECHO y verificado**: `escribir_serie`
   crea 1 dataset por fecha (`raster_<zona>_<fecha>`) + resumen
   `analisis_<zona>_tendencia` con upstreamLineage mÃºltiple. Evidencia vÃ­a
   MCP: search "tendencia" total=5, search "lima" total=22 (rasters por dÃ­a
   incluidos). Fix extra: `demo_temporal.py` desempaca `["urn_datahub"]`
   (cerrar_ciclo devuelve dict, no URN -> print cp1252 morÃ­a).
   ðŸ”’ AdemÃ¡s: `config/config.yaml` (tokens reales) fuera de git + nuevo
   `config/config.example.yaml` sanitizado â€” revisar antes del push pÃºblico.
3. ðŸŸ¡ Zona real: geocodificar "tal lugar" (Nominatim/geopy) en vez de "lima"
   fija; con eso GEE real + bbox funcionarÃ­a para cualquier ciudad.
4. ðŸŸ¡ gis-mcp (docs/MCP_SERVERS.md) + puente stdio.
5. ðŸŸ¡ Telegram real (token BotFather + chat_id).
6. ðŸŸ¡ Dashboard Streamlit (mapa folium + chat + tendencia).
7. ðŸŸ¢ GitHub pÃºblico + push (LICENSE Apache 2.0 ya estÃ¡).

## Pitch que vende (para el video â€” el usuario lo graba Ã©l)

> "Modelo local pequeÃ±o + DataHub como memoria = agente que NO alucina.
> Preguntas en espaÃ±ol â†’ bÃºsqueda real en el grafo (MCP), anÃ¡lisis de riesgo
> geoespacial â€”puntual o por tendencia de N dÃ­asâ€”, resultado escrito DE VUELTA
> a DataHub con linaje para que otros agentes lo hereden, y alerta por Telegram
> si hay riesgo."
