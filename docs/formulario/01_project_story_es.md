# Historia del Proyecto — Terra Cognita

> **Sobre el proyecto:** nuestra inspiración, lo que aprendimos, cómo lo
> construimos y los retos que enfrentamos.

---

## Qué nos inspiró

Vivimos en un país donde mirar la tierra importa: la sequía avanza sobre
los espacios verdes costeros, las zonas urbanas se expanden sobre lomas
frágiles, y un aviso tardío puede significar días de riesgo innecesario.

El problema no son los datos. Sentinel-2, CHIRPS, SMAP y MODIS publican
información diaria y gratuita sobre vegetación, lluvia, suelo y
temperatura. El problema es el *acceso*: leer esas capas requiere
conocimiento de SIG, herramientas fragmentadas y días de trabajo manual
— por eso la mayoría de decisiones se toman **sin** evidencia espacial.

Imaginamos otro usuario: un alcalde, un pequeño agricultor, un
periodista. Alguien que pregunta, en español simple:

> "¿Cómo está evolucionando la sequía en Lima esta semana?"

…y obtiene en aproximadamente un minuto: un mapa, la tendencia, el
linaje de cada número y una alerta en Telegram si algo anda mal.

Eso es Terra Cognita: **un agente que usa la memoria de su propio grafo
de datos, para no alucinar nunca.**

## Lo que aprendimos

El proyecto nos empujó por cuatro mundos muy distintos:

1. **Agentes como software, no chatbots.** El patrón de orquestación —
   interpretar → consultar contexto → actuar → escribir de vuelta →
   notificar — convirtió al LLM en un pequeño *motor de flujos*. El
   modelo planea, el código ejecuta, y el modelo razona sobre
   resultados reales.
2. **DataHub como memoria del agente.** La lección más sorprendente fue
   que un catálogo de datos también es una *herramienta cognitiva*:
   preguntarle al servidor MCP *"¿qué datasets existen de NDVI?"* antes
   de actuar elimina la alucinación por construcción — el agente razona
   sobre entidades reales (datasets, esquemas, linaje), no sobre lo que
   cree saber.
3. **Earth Engine está más cerca de lo que parece.** Con un bounding box
   pequeño (~2 km) la cuota gratuita alcanza de sobra, y la generación
   de código hace que el propio agente escriba el script de descarga por
   consulta: NDVI, lluvia, humedad, agua, LST y EVI comparten un motor
   de plantillas y un mismo pipeline.
4. **Una demo nunca debe colgarse.** En un portátil de 8 GB, correr TRES
   sistemas a la vez (Docker+DataHub, el agente y el dashboard) deja
   menos de ~0.3 GB de RAM libre. Terminamos construyendo una cascada de
   intérpretes (opencode → Ollama → API LLM → heurística) para que la
   demo siempre termine, pase lo que pase debajo.

## Cómo lo construimos

El pipeline es un ciclo cerrado, con cada etapa con un rol deliberado:

```text
Usuario (lenguaje natural)
   │
   ▼
AGENTE — cascada: opencode → Ollama (local) → API LLM → heurística
   │  plan = {analisis, zona, dias}  (JSON desde el LLM)
   ├──► DataHub vía servidor MCP (HTTP :8000): search/schema/lineage
   ├──► rasters (sintéticos para la demo, o GEE real: un cambio de línea)
   ├──► cálculo: % bajo umbral, medias, delta, tendencia, estado
   ├──► código GEE auto-generado (bbox pequeño + getDownloadURL)
   ├──► datahub_write: 1 dataset por fecha + upstreamLineage
   └──► Telegram (alerta razonada por el agente) + dashboard/mapa/chat
```

La matemática es simple pero significativa. Para vegetación seguimos el
índice clásico de diferencia normalizada:

$$
NDVI = \frac{NIR - RED}{NIR + RED}
$$

y la fracción de área degradada en el día $t$:

$$
P_t = \frac{1}{N_t}\sum_{i=1}^{N_t} \mathbf{1}\big[NDVI_i < \tau\big] \cdot 100
$$

El informe de tendencia compara el primer y el último día de la serie:

$$
\Delta = P_{t_0} - P_{t_{N}} \qquad\text{(puntos porcentuales)}
$$

con reglas de alerta:

$$
\text{estado} =
\begin{cases}
\text{ALERTA} & P_{\max} \geq 50 \\
\text{ALERTA} & \Delta > +5 \\
\text{OBSERVACIÓN} & \Delta > 0 \\
\text{OK} & \text{en otro caso}
\end{cases}
$$

El mismo motor de plantillas impulsa lluvia (CHIRPS), humedad de suelo
(SMAP), agua (NDWI), temperatura (LST-MODIS) y vegetación robusta (EVI).

Para la demo usamos rasters sintéticos, de modo que el flujo sea
reproducible en cualquier sala, y la ruta de datos reales (GEE) está a
una línea de configuración:

```python
gee:
  fuente_default: "sintetico"   # → "gee" descarga Sentinel-2 de verdad
```

## Retos que enfrentamos (y cómo los resolvimos)

| Reto | Qué pasó realmente | Solución |
|---|---|---|
| La demo "se colgaba" en silencio | prints sin `flush` + proceso de 4 minutos → salida perdida al matarlo | `flush=True` en todo + timeouts explícitos (Ollama 90 s, MCP 45 s) |
| Write-back crasheaba | `asegurar_raster_fuente` estaba fuera del try/except | movido dentro → respaldo local con URN |
| Config cargada vacía | `parents[2]` apuntaba fuera del repo → tokens ignorados | ruta corregida a `parents[1]`; verificar `len(token)` en cada sesión |
| `CURL_CA_BUNDLE` roto en Windows | peticiones TLS fallaban al azar | `Remove-Item Env:CURL_CA_BUNDLE` al inicio de cada sesión |
| Plantilla GEE crasheaba | `.format()` chocaba con las llaves `{min: ...}` de Earth Engine | placeholders por token (`__ZONA__`, `__ESCALA__`, …) |
| El mapa no renderizaba | el folium moderno movió `Colormap` a `branca`; `ImageOverlay` a `raster_layers`; luego `cmap(arr)` falló con arrays 2-D | `branca.LinearColormap` (leyenda) + rasterización RGB manual |
| HTML crudo en la interfaz | Streamlit requería `st.html` para los estilos que queríamos | todo el estilo movido a `st.html` |
| Telegram enviaba dicts feos de Python | limitación: el reporte era el `repr` del resultado | informe formateado: tabla por día, delta, conclusión, URN de DataHub |
| Secretos en git | `config.yaml` con el token del bot estaba trackeado | `git rm --cached` + `config.example.yaml` en el repo |
| Emoji corrompido por consola | cp1252 de la CLI dañaba caracteres multibyte | reportes enviados desde la ruta de código (UTF-8), no desde consola |

El hardware también enseñó disciplina: con ~0.3 GB libres de RAM, los
imports van lentos, Ollama hace timeout y los procesos compiten por
memoria. El diseño de intérpretes en cascada nació de una restricción
real: **la demo debe terminar**, y terminar con heurística vale más que
la teoría sin salida.

## El resultado

- Un repositorio público con licencia Apache-2.0, documentación completa
  y salidas reales del agente (informe, JSON catalogado, código GEE
  generado).
- Un dashboard (mapa por día + gráficos de tendencia + estado del stack
  en vivo).
- Un script de ejecución narrado — 8 etapas visibles para explicar la
  arquitectura mientras corre.
- Un agente que escribe sus resultados **de vuelta al grafo con
  linaje**, de modo que cualquier otro agente pueda heredarlos: 29+
  datasets, 5 de tendencia, cada uno trazable hasta sus rasters fuente.

Terra Cognita demuestra que una máquina *modesta* puede correr un
*geo-agente potente*: el cerebro es intercambiable (cualquier proveedor,
cualquier modelo local), pero la memoria — DataHub y su linaje — es lo
que le da confianza.

---

*Formato: Markdown con soporte de LaTeX. Terra Cognita — DataHub
Community Hackathon, categoría "Agents that do real work".*