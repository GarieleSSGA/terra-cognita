# BITÁCORA — errores encontrados, qué evitar, qué falta

Registro incremental de la sesión 2026-08-09 (últimos 2 h pre-entrega hackathon).

## 🔴 Errores encontrados (y ya corregidos)

| # | Error | Causa | Fix | Cómo evitarlo en el futuro |
|---|---|---|---|---|
| 1 | `ciclo_completo.py` "sin salida" | prints sin `flush` + proceso de 3-4.5 min (Ollama con RAM justa) → al matar por timeout el buffer se perdía | `flush=True` / `line_buffering` en scripts; timeouts Ollama 90 s y MCP 45 s | toda demo con `-u` o line_buffering; nunca asumir "cuelga" sin faulthandler |
| 2 | write-back crasheaba (`OperationalError` GMS) | `asegurar_raster_fuente` estaba FUERA del try/except | movido dentro → fallback local con URN | cualquier IO externo va dentro del fallback local |
| 3 | **config cargaba vacía (token/umbrales ignorados)** | `RUTA_CONFIG = parents[2]` apuntaba a `DEJANDO EL PASADO\config\` (no existe). Todo corría con defaults que coincidían por casualidad | `parents[1]` (raíz del repo) | verificar `cargar_config()` en cada sesión: `print(len(token))` |
| 4 | Telegram "Not Found" | consecuencia del #3 (token vacío) | el #3 lo arregló | — |
| 5 | `ok, msg = enviar_mensaje(...)` ValueError | la función devuelve dict, no tupla | desempacar como dict | leer la firma antes de desempacar |
| 6 | `KeyError: 'min'` en generador GEE | `.format()` chocaba con llaves GEE `{min:...}` | reemplazo por tokens `__ZONA__` etc. | no usar `.format()` con texto que contenga llaves |
| 7 | `Start-Process` partía args con espacios (`sys.argv[1]="dame"`) | PowerShell 5.1 no cita argumentos | usar `& python.exe ...` directo | nunca lanzar demos con Start-Process si llevan argumentos con espacios |
| 8 | pip warning `~ebsockets` | instalación interrumpida previa | borrar dir temporal | limpiar con `Remove-Item -Recurse` |
| 9 | `[DataHub] aviso al catalogar serie: 'charmap' codec can't encode '\u241e'` después del write-back | `demo_temporal.py` asignaba `urn = orq.cerrar_ciclo(...)` pero `cerrar_ciclo` devuelve el **dict resultado** (con el contexto MCP largo, chars raros) → el `print` de cp1252 moría. El write-back SÍ había funcionado | `["urn_datahub"]` al desempacar | leer la firma: `cerrar_ciclo` → dict; `resultado["urn_datahub"]` es el URN |

## ⚠️ Errores conocidos SIN corregir (limitaciones)

- **RAM 7.65 GB**: Docker arriba = ~0.3 GB libres → Ollama hace timeout y los
  imports pesados van lento. Es la máquina, no el código.
- Docker daemon da 500 de vez en cuando → reiniciar Docker Desktop
  (`Start-Service com.docker.service` si quedó Stopped).
- `getDownloadURL` de GEE aún NO probado end-to-end (falta ejecutar 1 escena).
- Dashboard aún no arrancado de punta a punta (falta verificar streamlit).

## 🚫 Qué evitar (trampas del entorno)

1. `CURL_CA_BUNDLE` roto → `Remove-Item Env:CURL_CA_BUNDLE` al inicio de CADA sesión.
2. PROJ_LIB/GDAL_DATA heredados de PostgreSQL → los limpia `terra_cognita/__init__.py` (no quitarlos).
3. No tocar `config_monitoreo.json` del proyecto deforestación (regla AGENTS.md); leer sí.
4. Python 3.14 del sistema NO sirve; usar siempre `.venv\Scripts\python.exe` (3.11).
5. Ollama y Docker NO coexisten en esta RAM: elegir uno (o usar `llm_api`).
6. Subir secretos: config.yaml (tokens) está en .gitignore → commitear config.example.yaml.

## ✅ Lo que ya funciona (verificado hoy)

- **Intérprete opencode como "cerebro"** (RAM cero local): `opencode run --pure`
  devuelve el plan JSON en ~20 s (via: opencode). Cadena completa:
  opencode -> Ollama -> llm_api -> heurística. Resolver del exe:
  `%APPDATA%\npm\node_modules\opencode-ai\bin\opencode.exe` (CreateProcess no
  resuelve los shims .cmd/.ps1). Config: sección `opencode` en config.yaml.
- Telegram real: bot @ERRADICADORBOT → chat 7245893327 (message_id 32).
- Generador de código GEE (7 plantillas distintas: ndvi/lluvia/humedad/ndwi/lst/evi/serie).
- Raster sintético de humedad + evaluación.
- Config real cargada (token, proyecto GEE, umbrales).
- DataHub+MCP+GMS (pendiente re-verificar tras reinicio de Docker).
- **Serie temporal en DataHub (VERIFICADO end-to-end)**: `demo_temporal.py`
  cataloga 1 dataset por fecha + resumen `analisis_<zona>_tendencia` con
  lineage múltiple. Evidencia GMS: 5 datasets tendencia + rasters por día
  (search "lima" total=22). Último URN: `analisis_lima_tendencia_03d678`.

## ❓ Falta (pendiente de esta sesión o del usuario)

1. Test end-to-end del dashboard (streamlit run).
2. GEE real: `ee.Initialize` + descarga síncrona 1 escena.
4. examples/ + README.md.
5. git init + push (lo sube el usuario).
6. Video (lo graba el usuario).
7. Mejoras pendientes: geocodificar "tal lugar", dashboard con historial de
   consultas, serie GEE real por fechas, `llm_api` con clave (falta dinero/clave).
