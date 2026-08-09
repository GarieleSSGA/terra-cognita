# Arquitectura de Terra Cognita

```
┌────────────────────────────┐
│        USUARIO             │
│  "dame el NDVI de SJL"     │
└──────────────┬─────────────┘
               ▼
┌────────────────────────────┐
│  AGENTE LOCAL (Ollama)     │  Razona la intención, arma el plan,
│  qwen3:4b (privado)        │  decide qué herramientas invocar
└──────┬──────────────┬──────┘
       ▼              ▼
┌────────────────┐  ┌────────────────────┐
│ DATAHUB MCP    │  │  CAPA DE ACCIÓN    │
│ search         │  │  geo: índices,     │
│ get_entities   │  │  umbrales, riesgo  │
│ list_schema    │  │  NDVI, lluvia      │
│ get_lineage    │  └────────┬───────────┘
└──────┬─────────┘           ▼
       │           ┌────────────────────┐
       │           │ DATOS              │
       └──────────▶│ sintéticos (demo)  │
                   │ GEE Sentinel-2     │
                   │ (1 línea de cambio)│
                   └────────┬───────────┘
                            ▼
              ┌─────────────────────────┐
              │ WRITE-BACK → DATAHUB    │  ← contribuye al grafo (20% puntaje)
              │ dataset del análisis    │
              │ + linaje a fuentes      │
              └────────┬────────────────┘
                       ▼
              ┌─────────────────────────┐
              │ TELEGRAM (alerta +      │
              │ reporte con mapa)       │
              └────────┬────────────────┘
                       ▼
              ┌─────────────────────────┐
              │ DASHBOARD (Streamlit)   │
              │ mapa + chat + valores   │
              └─────────────────────────┘
```

## Flujo de una consulta

1. Usuario pregunta en lenguaje natural.
2. Ollama interpreta (¿qué dato? ¿dónde? ¿qué análisis?).
3. El agente consulta DataHub vía MCP: encuentra el dataset correcto,
   aprende su esquema y verifica linaje (evita alucinaciones).
4. La capa geo ejecuta el análisis sobre raster sintético (demo) o
   Sentinel-2 real (GEE). Mismo código, un flag.
5. El resultado se escribe de vuelta en DataHub como dataset nuevo
   con linaje hacia sus fuentes.
6. Se genera alerta/reporte por Telegram si supera umbrales.
7. El dashboard muestra mapa + valores + chat de la sesión.

## Decisiones de diseño

| Decisión | Por qué |
|---|---|
| Datos sintéticos primero | Demo reproducible en segundos, sin auth GEE, offline en el video |
| GEE conectable con 1 línea | Se demuestra integración real (la API se usa sí o sí) |
| Write-back a DataHub | "Contribuir al grafo" = 20% del puntaje |
| Ollama local | Privacidad + demo convincente: IA local orquestando |
| Telegram | Cierre del ciclo acción: de pregunta a alerta |