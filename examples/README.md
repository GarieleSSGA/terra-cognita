# Artefactos generados por el agente (salidas reales)

Cada archivo proviene de una **corrida real** del agente (consulta
`"dame la vegetacion de Lima de los ultimos 7 dias"`) contra DataHub
+ rasters sintéticos. Los números son idénticos a los de la demo
interactiva y al grafo de DataHub en vivo.

## Contenido

| Archivo | Qué es |
|---|---|
| `prompts/consulta_y_plan.txt` | Consulta en lenguaje natural + plan JSON que generó el LLM |
| `salidas/reporte_telegram.txt` | Texto exacto del informe enviado al bot de Telegram |
| `salidas/tabla_tendencia.csv` | Serie de 7 días: % área bajo umbral y NDVI medio por día |
| `salidas/resumen_tendencia.json` | Resumen estructurado + URN del dataset catalogado en DataHub |
| `salidas/catalogado_datahub.json` | Ejemplo de un dataset puntual (snapshot) catalogado con su URN |
| `salidas/codigo_gee_ndvi.js` | Código JavaScript auto-generado para Google Earth Engine (NDVI, bbox pequeño + getDownloadURL) |
| `rasters/*.tif` | Dos rasters de muestra de la serie (primer y último día, GeoTIFF NDVI) |

## Evidencia

- 7 días: área bajo umbral **37.7 % → 40.8 %** (delta **+3.1 pp**)
- NDVI medio: **0.344 → 0.332**
- Estado: **OBSERVACIÓN** (deterioro leve)
- En DataHub UI (:9002): buscar `tendencia` → el dataset
  `analisis_Lima_tendencia_*` apunta (lineage) a sus 7 rasters fuente.