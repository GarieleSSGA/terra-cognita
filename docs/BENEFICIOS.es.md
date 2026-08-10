# 🌎 BENEFICIOS de Terra Cognita

Sistema agéntico geoespacial: consulta en lenguaje natural → análisis
espacial con IA → memoria con linaje (DataHub) → alertas (Telegram).
Pensado para los criterios del hackathon: innovación, impacto social,
integración real y demostración en vivo.

## 1. IA capaz con CUALQUIER presupuesto de RAM

- **Cadena de intérpretes en cascada**: `opencode (IA potente) → Ollama
  (modelo local privado) → API LLM → heurística`. El sistema NUNCA se
  cuelga: si el intérprete tarda, el siguiente toma el control y la demo
  termina siempre.
- En una máquina con 8 GB de RAM (como la de la demo, con Docker arriba
  consumiendo casi todo), el agente SIGUE siendo inteligente: usa opencode
  (~0 RAM local) — la demostración de que "puedes tener un geo-agente
  potente sin una GPU".
- En una máquina potente (p. ej. core i7 con 16+ GB), se activa `Ollama` y
  todo el razonamiento es 100 % local y privado.

## 2. Un agente que NO alucina (memoria real con DataHub)

- Antes de responder, el agente **consulta DataHub vía MCP**: qué datasets
  existen, qué columnas tienen y de dónde vienen (linaje).
- El razonamiento arranca del **grafo real**, no de "lo que cree el modelo".
- Cada análisis **se escribe de vuelta a DataHub con linaje**: un dataset
  por fecha + resumen con `upstreamLineage`. Los números del reporte se
  pueden rastrear hasta su raster fuente — auditoría completa.

## 3. De la consulta al dato real (Google Earth Engine)

- El agente **genera código JavaScript de GEE ad-hoc** para cada consulta:
  diferente por análisis (NDVI, lluvia CHIRPS, humedad SMAP, NDWI, LST
  MODIS, EVI), zona y fechas.
- Zona pequeña (~2 km) por defecto: descargas rápidas y dentro de la cuota
  gratuita. Con `getDownloadURL` el código descarga el raster y el pipeline
  lo procesa igual (sintéticos y reales usan el mismo análisis).

## 4. Alerta temprana con decisión del agente

- El agente **razona el resultado** y decide qué avisar: ALERTA (riesgo),
  OBSERVACIÓN o OK — y opcionalmente reporta cada consulta a Telegram
  (`reporte_siempre: true`).
- No es un botón fijo: es la misma IA que entendió la consulta la que
  decide el mensaje, cerrando el círculo acción → aviso.

## 5. Visualización completa

- **Dashboard Streamlit**: mapa NDVI con leyenda + chat + tendencia por día
  (tabla y conclusión) + estado del stack en vivo + DataHub UI enlazada.
- **`scripts/flujo_paso_a_paso.py`**: muestra las 8 etapas internas con
  prints reales — perfecto para explicar la arquitectura al jurado.

## 6. Reproducibilidad y robustez

- Datos sintéticos de demostración → demo reproducible sin depender de
  APIs externas que fallan o demoran; el código para datos reales (GEE)
  cambia en una línea (`fuente_default: gee`).
- Fallbacks en cascada: MCP caído → continúa con contexto local;
  write-back fallido → respaldo local sin romper el flujo.
- Bitácora de errores del entorno (`docs/BITACORA.md`) que documenta cada
  trampa y su arreglo.

## Mapa (hipótesis de impacto)

| Problema | Terra Cognita |
|----------|---------------|
| Monitoreo lento y manual | Consulta en lenguaje natural, respuesta en minutos |
| Ojo no experto en teledetección | El agente traduce a índices y umbrales |
| Resultados sin trazabilidad | Todo queda en DataHub con linaje |
| Alertas genéricas | Mensaje razonado por el agente según la severidad |
| Costo de infraestructura | IA local / opencode en máquinas comunes |