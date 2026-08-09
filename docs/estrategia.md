# DataHub Hackathon - Strategy Terra Cognita

## Objetivo
Ganar la categoría "Agents that do real work" (o Abierto) del DataHub
Community Hackathon.

## Checklist de requisitos
- [x] DataHub corriendo en Docker (localhost:9002)
- [ ] Repositorio público GitHub con licencia Apache 2.0
- [ ] Usar MCP Server de DataHub (obligatorio: al menos 1 de las 4)
- [ ] Video demo <= 3 min (en inglés o subtitulado)
- [ ] README con instalación y prueba
- [ ] Carpeta examples/ con outputs del agente
- [ ] Diagrama de arquitectura (docs/)

## Puntaje (todo pesa 20%)
| Criterio | Cómo suma Terra Cognita |
|---|---|
| Uso de DataHub | discovery MCP + write-back de resultados (contribuye al grafo) |
| Ejecución técnica | pipeline que funciona end-to-end con datos sintéticos |
| Originalidad | agente geoespacial dirigido por IA local + DataHub como memoria |
| Utilidad real | planificadores urbanos: análisis de riesgo en minutos, no días |
| Presentación | video punch, README impecable, examples con outputs reales |

## Demo ganadora (segmento para el video)
1. "¿Cuál es el NDVI promedio de la zona X?" (5 s, en vivo)
2. Agente usa DataHub MCP para descubrir el dataset correcto (mostrar)
3. Análisis se ejecuta (sintético) → mapa con colores + valor
4. Write-back visible en DataHub UI: nuevo dataset + linaje
5. Si riesgo: alerta llega a Telegram (muestra el celular)

## Prioridades (en orden)
1. Núcleo: agente + MCP + análisis sintético (lo que da el 80% del puntaje)
2. Write-back a DataHub
3. GEE real (1 línea)
4. Telegram
5. Dashboard
6. Video + README + examples

## Riesgos
- Alcance grande: NO construir todo primero. Demo mínima funcional ANTES de pulir.
- Video en inglés: grabar con guion breve, subtítulos si es necesario.
- Originalidad: el repo debe nacer en el período del hackathon.

## Palabras prohibidas en presentación
decir que el proyecto "ya estaba hecho" o que es una continuación directa
del sistema de deforestación anterior. Terra Cognita es nuevo: integra GEE +
DataHub MCP + IA local + write-back en una sola plataforma.