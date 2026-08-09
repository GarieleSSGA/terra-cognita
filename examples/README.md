# Ejemplos de Terra Cognita

Carpeta exigida por el hackathon: outputs reales del agente, listos
para que los jueces vean qué produce sin tener que ejecutar nada.

## Contenido

- `salidas/`  -> JSON de resultados de analisis (autogenerado por el agente)
- `prompts/`  -> consultas usadas en el video/demo, con su respuesta esperada

## Consultas de demo (copiar-pegar)

1. "Identifica las zonas con baja vegetacion (NDVI) en Lima"
2. "Dame el riesgo de inundacion por lluvia en el Callao"
3. "¿Que dataset tengo en DataHub sobre cobertura vegetal?"

## Cómo generar ejemplos

```bash
python scripts/demo_rapida.py "Identifica las zonas con baja vegetacion en Lima"
```

Los outputs se guardan en `data/` y los mejores pasan a `examples/salidas/`
para el repositorio.