# ESTADO — Terra Cognita (Día 1)

Última sesión: completada la infraestructura MVP y el circuito de datos
fully functional. Este archivo es para que el agente retome mañana sin
perder el contexto.

## Lo que YA funciona (verificado ejecutando)

| Componente | Estado | Evidencia |
|---|---|---|
| DataHub en Docker | ✅ arriba | http://localhost:9002 (datahub/datahub) |
| MCP Server (`mcp-server-datahub` v0.6.0) modo HTTP | ✅ vivo | http://localhost:8000/health → ok; http://localhost:8000/mcp |
| Cerebro local Ollama | ✅ gemma3:1b | `scripts/demo_rapida.py` → plan `ndvi/Lima` sin fallback |
| Rasters sintéticos (NDVI, lluvia) | ✅ | data/ndvi_Lima.tif, 47.7% bajo umbral → OK |
| Búsqueda MCP→DataHub (GraphQL real) | ✅ | `search` devuelve JSON total:N (`scripts/probar_mcp.py`) |
| Write-back a DataHub | ✅ | `escribir_resultado()` crea dataset + linaje → buscar devuelve total:3, lineage upstreams:1 |
| Demo ciclo completo | 🔴 PENDIENTE | `scripts/ciclo_completo.py` se cuelga en silencio (bug sin resolver, ver abajo) |
| Telegram | ⏳ sin config | falta token/chat_id en config |

## Bug a resolver MAÑANA (primera tarea)

`scripts/ciclo_completo.py` se queda **sin imprimir nada** (exit 0, stdout vacío,
se cuelga antes del primer print). `demo_rapida.py` (mismos imports) funciona.
Investigación pendiente:
1. `python -u -X faulthandler ciclo_completo.py` → ver dónde se cuelga
2. `python -c "import ciclo_completo"` → si es el import, bisectar los módulos
3. Sospecha: `orq.cerrar_ciclo()` afecta, o el `import json as _json` dentro de main, o
   error silencioso de encoding al volcar resultados con acentos en f-string sobre
   stdout piped (probado `PYTHONIOENCODING=utf-8` sin éxito).
4. Fix probable: mover orquestación dentro de `if __name__`, activar stderr
   (log a archivo en vez de print) y revisar con `>` redirección real a fichero.

## Comandos rápidos

```powershell
# Subir DataHub (si apagado): necesita Kafka corriendo (GMS no arranca sin él)
docker start datahub-mysql-1 datahub-opensearch-1 datahub-kafka-broker-1 datahub-datahub-gms-quickstart-1 datahub-frontend-quickstart-1

# Subir servidor MCP HTTP (persistente, ~30 s de arranque)
$env:DATAHUB_GMS_HOST="localhost"; $env:DATAHUB_GMS_PORT="8080"; $env:DATAHUB_GMS_PROTOCOL="http"
Start-Process -FilePath "<ROOT>\.venv\Scripts\mcp-server-datahub.exe" -ArgumentList "--transport","http" -WindowStyle Hidden

# Demo núcleo (sin DataHub necesario)
<ROOT>\.venv\Scripts\python.exe scripts\demo_rapida.py "dame el NDVI de Lima"

# Prueba MCP (lista herramientas)
<ROOT>\.venv\Scripts\python.exe scripts\probar_mcp.py

# Ollama
ollama serve   # si no responde http://localhost:11434
```
Venov path: `.venv\Scripts\python.exe` (Python 3.11). El python 3.14 del sistema NO sirve (pydantic-core sin wheels).

## Trampas del entorno (IMPORTANTE - se rompen sin estos fixes)

1. **`CURL_CA_BUNDLE`** mal definido (apunta a cert de PostgreSQL inexistente).
   Rompe pip/requests (`OSError: TLS CA bundle`). Fix por sesión:
   `Remove-Item Env:CURL_CA_BUNDLE`
2. **`PROJ_LIB`/`GDAL_DATA`/`PROJ_DATA`** apuntan a PostgreSQL. Rompen rasterio
   (`Cannot find proj.db`). `terra_cognita/__init__.py` ya los quita al importar.
3. **RAM de la máquina es 7.7 GB total**. Docker-WSL configurado a 5 GB (en
   `%USERPROFILE%\.wslconfig`). NO correr Qwen 3:4b con Docker arriba (500):
   usar `gemma31b` (config.yaml) o apagar Docker para demo con Ollama robusto.
4. **DataHub**: no detener `kafka-broker` (GMS no arranca sin él).
   `datahub-actions` SÍ se puede detener (ahorra RAM).
5. Python 3.11 es el bueno: `C:\Users\user\AppData\Local\Programs\Python\Python311\`.

## Módulos y piezas clave

- `terra_cognita/agent/orquestador.py` — cerebro: interpretar (Ollama) → contexto
  (MCP) → ejecutar (geo) → cerrar_ciclo (write-back + alerta)
- `terra_cognita/datahub_mcp/cliente.py` — HTTP al servidor MCP (URL_MCP=http://localhost:8000/mcp),
  auto-arranque del servidor si no existe (espera hasta 90 s)
- `terra_cognita/datahub_write/catalogar.py` — MCE con `DatasetSnapshotClass` (el
  MCP nuevo `emit_mcp` falla con avro; NO usar → ya probado)
- `terra_cognita/geo/*` — sinteticos.py (raster sintético), gee.py (Sentinel-2 real, 1 flag),
  analisis.py (estadísticas + umbrales), datos.py (multi-fuente)
- `terra_cognita/alertas/telegram_bot.py` — envío Telegram (reutilizado del
  sistema de deforestación anterior)
- `config/config.yaml` — modelo, umbrales, tokens (hojas vacías = no configurado)

## Siguientes pasos (por orden prioridad)

1. 🔴 Arreglar `ciclo_completo.py` (bug silencioso)
2. 🟡 Subir la GEE real a Puerto en config → `fuente_default: "gee"` y probar 1 línea
   (necesita `earthengine authenticate` una vez; si falla, seguir conGEE
   sintético: sin auth reportar error claro)
3. 🟡 Telegram: pedir al usuario token BotFather + chat_id y probar envío real
4. 🟡 Dashboard Streamlit (`dashboard/app.py`) — instalar streamlit en venv,
   renderizar raster en mapa (folium/plotly) + chat
5. 🟢 Repositorio GitHub público (Apache 2.0 ya en LICENSE) + primer push
6. 🟢 Video demo (≤3 min) guion en `docs/` — los jurados ven SOLO ese video

## Pitch que vende (para el video)

> "Modelo local pequeño + DataHub como memoria = agente que NO alucina.
> Preguntas en español → búsqueda real en el grafo (MCP), análisis de riesgo
> geoes-espacial, resultado escrito DE VUELTA a DataHub con linaje para que
> otros agentes lo hereden, y alerta por Telegram si hay riesgo."