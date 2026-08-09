# Terra Cognita

Agente local de inteligencia espacial que entiende consultas en lenguaje natural,
descubre datasets geoespaciales usando DataHub (MCP Server), ejecuta análisis
(NDVI, riesgo, humedad) sobre rasters **sintéticos** (demo rápida) o **Sentinel-2
real vía Google Earth Engine** (un cambio de línea), escribe sus resultados de
vuelta al grafo de DataHub y cierra el ciclo enviando alertas + reportes por
Telegram.

**Problema que resuelve:** el análisis de riesgo espacial para planificadores
urbanos toma días (datos fragmentados, GIS complejo, sin contexto). Terra Cognita
lo reduce a minutos: pregunta en español → respuesta con mapa, valores y alertas.

**Hackathon:** DataHub Community Hackathon — Categoría: "Agents that do real work".

## Arquitectura (resumen)

```
Usuario → [Ollama: agente local] → [DataHub MCP: contexto/descubrimiento]
                                   → [mcp-geo: análisis espacial]
                                   → [GEE / rasters sintéticos: datos]
                                   → [write-back a DataHub: dataset + linaje]
                                   → [Telegram: alertas] → [Dashboard: mapa + chat]
```

## Requisitos

- Docker Desktop (DataHub corriendo en `http://localhost:9002`)
- Ollama con un modelo local (ej. `qwen3:4b`)
- Python 3.11+

## Instalación

```bash
pip install -r requirements.txt
python -m terra_cognita.agent.orchestrator --demo
```

## Estructura

```
terra_cognita/
├── agent/          # Orquestador: Ollama + herramientas
├── datahub_mcp/    # Cliente MCP de DataHub (search, schema, lineage)
├── geo/            # Rasters sintéticos, GEE (Sentinel-2), índices
├── alertas/        # Reportes + bot de Telegram
├── datahub_write/  # Write-back de resultados al grafo
├── dashboard/      # Frontend visual (mapa + chat)
├── config/         # Configuración central
├── scripts/        # Utilidades: generar sintéticos, demo rápida
├── examples/       # Outputs del agente (carpeta exigida por DataHub)
└── docs/           # Arquitectura y diagrama
```

## Licencia

Apache License 2.0