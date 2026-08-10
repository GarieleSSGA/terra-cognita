# Artefactos generados por el agente (salidas reales)

Cada archivo proviene de una **corrida real** del agente (consulta
`"dame la vegetacion de Lima de los ultimos 7 dias"`) contra DataHub
+ rasters sintéticos. Los números son idénticos a los de la demo
interactiva y al grafo de DataHub en vivo.

## Contenido

### Consulta y plan
- `prompts/consulta_y_plan.txt` — consulta en lenguaje natural + plan JSON generado por el LLM.

### Reportes y datos (salidas)
| Archivo | Qué es |
|---|---|
| `salidas/reporte_telegram.txt` | Texto exacto del informe enviado al bot de Telegram |
| `salidas/tabla_tendencia.csv` | Serie de 7 días: % área bajo umbral y NDVI medio por día |
| `salidas/resumen_tendencia.json` | Resumen estructurado + URN del dataset catalogado en DataHub |
| `salidas/catalogado_datahub.json` | Dataset puntual (snapshot) catalogado con su URN |
| `salidas/catalogado_snapshot_lima.json` | Otro snapshot real guardado por el fallback local |
| `salidas/codigo_gee_ndvi.js` | Código JavaScript auto-generado para Google Earth Engine (NDVI, bbox pequeño + `getDownloadURL`) |
| `salidas/tendencia_ndvi_lima.png` | Gráfico de tendencia generado a partir de los datos de la corrida |
| `salidas/informe_tendencia.txt` | Salida legible de la consola (demo temporal) |

### Visualizaciones
- `mapas/ndvi_lima_2026-08-04_heatmap.png` — raster renderizado (día 1 de la serie)
- `mapas/ndvi_lima_2026-08-10_heatmap.png` — raster renderizado (día 7: más área degradada)

### Rasters crudos (la serie completa, para reproducir/pescar)
- `rasters/ndvi_lima_2026-08-03.tif` … `rasters/ndvi_lima_2026-08-10.tif` — los 8 GeoTIFF NDVI de la semana (EPSG:4326, 120×120).

## Evidencia

- 7 días: área bajo umbral **37.7 % → 40.8 %** (delta **+3.1 pp**)
- NDVI medio: **0.344 → 0.332**
- Estado: **OBSERVACIÓN** (deterioro leve)
- En DataHub UI (:9002): buscar `tendencia` → el dataset
  `analisis_Lima_tendencia_*` apunta (lineage) a sus 7 rasters fuente.
- El gráfico PNG y los heatmaps fueron renderizados desde los propios
  rasters de `ras ters/` sin edición manual.