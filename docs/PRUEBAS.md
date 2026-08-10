# 🧪 GUION DE PRUEBAS para la demo — Terra Cognita

Pruebas ordenadas (de lo más simple a lo más vistoso) con pasos exactos y
resultado esperado. Todo desde la raíz del repo, con Docker arriba y el MCP
server corriendo.

**Siempre primero:** `Remove-Item Env:CURL_CA_BUNDLE`

## 0. Estado del sistema

```powershell
# 5 contenedores sanos:
docker ps
# agentes responden:
(Invoke-WebRequest http://localhost:8000/health -UseBasicParsing).StatusCode   # 200 MCP
(Invoke-WebRequest http://localhost:9002 -UseBasicParsing).StatusCode          # 200 DataHub UI
```

**Esperado:** 200 / 200 y 5 contenedores `Up`.

## 1. Análisis puntual (snapshot)

```powershell
.venv\Scripts\python.exe scripts\demo_rapida.py "cual es el NDVI de Lima"
```

**Esperado:** plan `via: opencode`, % bajo umbral, estado OK u OBSERVACION,
y al final un URN catalogado en DataHub.

## 2. Tendencia de 7 días (la estrella)

```powershell
.venv\Scripts\python.exe scripts\demo_temporal.py "dame la vegetacion de Lima de los ultimos 7 dias"
```

**Esperado:** tabla de 7 fechas (área bajo umbral 37.7→40.8 %, NDVI medio en
declive), delta +3.1 pp, "OBSERVACION: deterioro leve", serie catalogada con
linaje múltiple y **mensaje en tu Telegram** (informe formateado con tabla).

## 3. Otra tendencia: 15 días (más deterioro)

```powershell
.venv\Scripts\python.exe scripts\demo_temporal.py "como esta evolucionando la sequia en Lima los ultimos 15 dias"
```

**Esperado:** serie de 15 rasters, delta mayor, misma estructura.

## 4. Otro índice: lluvia (alerta)

```powershell
.venv\Scripts\python.exe scripts\demo_rapida.py "cuanta lluvia caera en Iquitos"
```

**Esperado:** plan `lluvia`, valor máx mm; si supera el umbral (50 mm) →
**ALERTA por Telegram** (🚨). Es la prueba que dispara alerta real.

## 5. Humedad de suelo

```powershell
.venv\Scripts\python.exe scripts\demo_rapida.py "como esta la humedad del suelo en Lima"
```

**Esperado:** plan `humedad`, % de área seca, estado OK/ALERTA.

## 6. Dashboards + mapas (visual, para el video)

```powershell
.venv\Scripts\python.exe -m streamlit run dashboard\app.py   # http://localhost:8501
```

1. Ejecuta "dame la vegetacion de Lima de los ultimos 7 dias".
2. **Esperado:** métricas (análisis/zona/intérprete `opencode`), estado
   OBSERVACION, tabla de tendencia, **2 gráficos** (área bajo umbral y NDVI),
   **selectbox de día** (cambia el mapa), mapa folium con leyenda verde/amarillo/rojo,

## 7. Flujo narrado (para GRABAR el video)

```powershell
.venv\Scripts\python.exe scripts\flujo_paso_a_paso.py --presentacion "dame la vegetacion de Lima de los ultimos 7 dias"
```

**Esperado:** 8 etapas con pausa de 6 s y guion 🎙 junto a cada una:
consulta → interpretación → contexto MCP → rasters → cálculo → código GEE →
write-back → reporte Telegram. Explícale al cámara cada pantalla mientras corre.

## 8. Ver el grafo de DataHub (figura clave del pitch)

1. Abre **http://localhost:9002** → login `datahub` / `datahub`.
2. Busca `tendencia` → abre un `analisis_*_tendencia_*`.
3. Pestaña **Lineage** → el resumen apunta a sus 7 rasters diarios.
4. Busca `lima` → total 29+ (memoria acumulada del agente).

**Esperado:** grafo visible con upstreams; eso demuestra que el agente
"escribe memoria con linaje" (criterio del hackathon).

## 9. Robustez (vender en el pitch)

| Prueba | Cómo | Resultado esperado |
|---|---|---|
| Sin MCP server | Mata el proceso :8000, corre demo | La demo sigue: contexto con aviso, resto OK |
| Sin Ollama/API | No tener ollama ni clave | Via: opencode o heurística; nunca se cuelga |
| Write-back caído | Para el GMS, corre demo | Fallback local en `data/resultados_catalogados/` |

## 10. Telegram (reportes)

1. Consulta con tendencia → llega informe formateado (tabla día a día).
2. Consulta de lluvia con valor alto → alerta 🚨.
3. O manual: `scripts` + botón "Enviar mensaje de prueba" en el dashboard.

**Esperado:** mensajes con texto legible (sin JSON ni código crudo).

---

**Consejo para el video:** graba en orden 6 → 7 → 8 → 4: dashboard en acción,
flujo narrado (arquitectura), grafo de DataHub (memoria con linaje) y alerta
Telegram (cierre del ciclo).