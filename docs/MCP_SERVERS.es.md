# MCP Servers externos: georreferenciación + catálogo en DataHub

Terra Cognita ya usa el MCP server oficial de DataHub (`mcp-server-datahub`,
HTTP persistente, ver `terra_cognita/datahub_mcp/cliente.py`). Este documento
lista servidores MCP **externos** que amplían el grafo de conocimiento y la
capacidad geoespacial del agente, con su plan de integración.

## Por qué sumar MCPs al grafo

El pitch de Terra Cognita es "pregunta en español → búsqueda real en DataHub
(MCP) → análisis → resultado DE VUELTA a DataHub con linaje". Añadir otros
dominios de datos por MCP enriquece lo que el agente puede *descubrir* y
*heredar*: cada herramienta externa pasa a ser un nodo más del patrón
"información verificable en vez de alucinada".

## Servidores evaluados (jul-ago 2026)

| Servidor | Qué aporta | Herramientas clave | Coste de integrar |
|---|---|---|---|
| [gis-mcp](https://github.com/mahdin75/gis-mcp) (PyPI `gis-mcp`) | GIS real: raster, vectores, estadística espacial (92 tools) | `compute_ndvi`, `raster_band_statistics`, `zonal_statistics`, `compute_s2_ndvi`, `download_satellite_imagery`, `morans_i`, `create_web_map` | pip install; Python ≥3.10; transporte HTTP/SSE y stdio |
| [earth-engine-mcp](https://github.com/Dhenenjay/earth-engine-mcp-new) | Imágenes satelitales vía Google Earth Engine | `search_catalog`, `get_band_names`, `filter_collection`, NDVI en GEE, export a GCS | Requiere cuenta GEE + JSON de service account |
| [geosight-mcp](https://github.com/armaasinghn/geosight-mcp) | Análisis de imagen satelital == al nuestro | `search_imagery`, `calculate_ndvi`, `calculate_ndwi`, `detect_land_cover`, informes PDF/HTML con mapas | Python 3.11+, requiere claves Sentinel Hub |
| JAXA Satellite MCP | Datos de observación JAXA | precipitación, LST, NDVI, elevación, humedad de suelo | Clave de API JAXA |
| [satellite-mcp](https://glama.ai/mcp/servers/badchars/satellite-mcp) | Índices espectrales | `spectral_ndvi` y otros índices por banda | Ligero (solo calcula índices) |

Recomendación de prioridad:
1. **gis-mcp** — encaja con la pila actual (rasterio/geopandas ya presentes),
   da estadística espacial seria (Moran's I → autocorrelación espacial para el
   análisis de riesgo) y sirve en modo HTTP igual que mcp-server-datahub.
2. **earth-engine-mcp** — es el puente natural a la tarea 2 del ESTADO
   (fuente real GEE en vez de sintética).
3. geosight-mcp — cuando haya claves Sentinel Hub (demo de "cambio de uso de
   suelo": deforestación, que es el caso de uso que originó este proyecto).

## Plan de integración (2 niveles)

### Nivel 1 — Puente ligero (stdio cliente, sin servidor persistente)

Patrón ya probado en `scripts/probar_mcp.py` (cliente stdio):
levantar el servidor externo bajo demanda, llamar la herramienta concreta y
devolver el JSON. El agente guarda el resumen y lo escribe en DataHub.

```python
# scripts/geo_mcp_extra.py (borrador de la pieza que falta)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMANDO = str(ROOT / ".venv" / "Scripts" / "gis-mcp.exe")   # tras pip install

async def ndvi_desde_gis_mcp(raster: str, rojo: int = 3, nir: int = 4):
    params = StdioServerParameters(command=COMANDO, args=[], env={})
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as sesion:
            await sesion.initialize()
            res = await sesion.call_tool("compute_ndvi", {
                "source": raster, "red_band_index": rojo,
                "nir_band_index": nir, "destination": str(raster) + ".ndvi.tif",
            })
            return {"content": [i.text for i in res.content]}
```

### Nivel 2 — Servidor HTTP persistente (como hace mcp-server-datahub)

Cada servidor externo con transporte HTTP se arranca una vez
(`gis-mcp serve --http` o equivalente) y el agente lo llama por URL reutilizando
`DataHubMCP._llamar` (basta parametrizar la URL de `cliente.py`).

### Catálogo en DataHub (cierre del ciclo)

Todo lo que devuelva un MCP externo y merezca heredarse se cataloga con la
misma pieza que el write-back actual (`terra_cognita/datahub_write/catalogar.py`):
crear `DatasetSnapshotClass` (plataforma `terraCognita`) + `upstreamLineage`
hacia el dataset fuente del raster. Así el grafo muestra
"resultado_geo_mcp ← raster_Lima_sintetico" y otros agentes lo reutilizan.

## Config pendiente (config/config.yaml)

```yaml
mcp_extra:
  gis_mcp:
    comando: ".venv/Scripts/gis-mcp.exe"   # o "python -m gis_mcp"
    transporte: "stdio"                    # stdio | http
    url_http: ""                           # si transporte: http
  earth_engine:
    credenciales_gee: ""                   # JSON service account (tarea 2)
    proyecto: "mi-proyecto-gee"
```

No está implementado todavía: es la hoja de ruta para la próxima sesión
(instalar `gis-mcp` en el venv y dejar el puente de Nivel 1 funcionando).