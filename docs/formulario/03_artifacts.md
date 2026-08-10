# Artifacts — respuesta para el formulario (EN)

> Pregunta: *"If your Project generates artifacts (code files, queries,
> reports, transformations), link to examples in your repo (e.g., an
> examples/ folder) so judges can evaluate quality without running the
> code."*

## Respuesta para pegar (inglés)

Yes — every artifact the agent generates is stored in the repo's
`examples/` folder, produced by **real runs** (not mockups):

- **Query + agent plan (LLM interpretation):**
  https://github.com/GarieleSSGA/terra-cognita/blob/main/examples/prompts/consulta_y_plan.txt
- **Auto-generated Google Earth Engine code** (NDVI, small bbox +
  `getDownloadURL`):
  https://github.com/GarieleSSGA/terra-cognita/blob/main/examples/salidas/codigo_gee_ndvi.js
- **Trend report** (7-day NDVI series: 37.7% → 40.8% area below
  threshold, delta +3.1 pp, WATCH conclusion):
  https://github.com/GarieleSSGA/terra-cognita/blob/main/examples/salidas/informe_tendencia.txt
- **Dataset catalogued back into DataHub** (JSON with URN + lineage):
  https://github.com/GarieleSSGA/terra-cognita/blob/main/examples/salidas/catalogado_datahub.json
- **Examples overview:**
  https://github.com/GarieleSSGA/terra-cognita/tree/main/examples

Raw GitHub links (no login needed? GitHub renders fine): should the judge
prefer raw text:

- https://raw.githubusercontent.com/GarieleSSGA/terra-cognita/main/examples/salidas/informe_tendencia.txt
- https://raw.githubusercontent.com/GarieleSSGA/terra-cognita/main/examples/salidas/codigo_gee_ndvi.js
- https://raw.githubusercontent.com/GarieleSSGA/terra-cognita/main/examples/prompts/consulta_y_plan.txt
- https://raw.githubusercontent.com/GarieleSSGA/terra-cognita/main/examples/salidas/catalogado_datahub.json

## Notas

- `examples/` es la carpeta exigida por DataHub para el hackathon: contiene
  salidas **reales** del agente, no ejemplos escritos a mano.
- El informe coincide con la demo interactiva y con la ejecución viva
  (dashboard + DataHub UI), así que el jurado puede cruzar las tres vistas.
- Si el formulario incluye un campo distinto para links, pega la lista
  directamente sin el texto explicativo.