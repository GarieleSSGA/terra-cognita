"""FLUJO INTERNO paso a paso: demuestra TODAS las etapas del sistema.

Para "ver" internamente Terra Cognita en vivo (demo/video):

    python scripts/flujo_paso_a_paso.py "dame la vegetacion de Lima de los ultimos 7 dias"

Cada etapa imprime su detalle real: interpretacion, contexto DataHub (MCP),
generacion de rasters, analisis, codigo GEE, write-back con linaje y reporte.
"""
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from terra_cognita.agent.orquestador import Orquestador

PRESENTACION = "--presentacion" in sys.argv
PAUSA = 6 if PRESENTACION else 0


def etapa(titulo: str, guion: str = "") -> None:
    print("\n" + "=" * 72, flush=True)
    print(f"  ETAPA: {titulo}", flush=True)
    print("=" * 72, flush=True)
    if PRESENTACION:
        if guion:
            print(f"  🎙 [NARRA] {guion}", flush=True)
        print(f"  (pausa de {PAUSA}s para explicar...)", flush=True)
        time.sleep(PAUSA)


def main():
    consulta = sys.argv[1] if len(sys.argv) > 1 else (
        "dame la vegetacion de Lima de los ultimos 7 dias")
    orq = Orquestador()

    etapa("1/8 CONSULTA del usuario",
          "\"El usuario no sabe de GIS: pregunta en espanol y el sistema hace el resto.\"")
    print(f"  >> \"{consulta}\"", flush=True)
    print("  (texto libre en español, sin tecnicismos)", flush=True)

    etapa("2/8 INTERPRETACION (agente decide el plan)",
          "\"Aqui el cerebro del sistema (hoy opencode, en produccion un modelo local con Ollama): entiende la intencion y arma el plan en JSON: que indice buscar, en que zona y cuantos dias.\"")
    plan = orq.interpretar(consulta)
    via = plan.get("via", "cerebro local")
    print(f"  Via: {via}", flush=True)
    print(f"  Plan JSON: {plan}", flush=True)
    print("  El agente entendio: analisis + zona + dias. "
          "Ahora sabe QUE buscar.", flush=True)

    etapa("3/8 CONTEXTO en DataHub via MCP (sin alucinar)",
          "\"Antes de actuar, el agente pregunta a su memoria (DataHub via MCP): que datasets hay del tema, qué columnas, de dónde vienen. Asi NO inventa: razona sobre datos reales.\"")
    contexto = orq.buscar_contexto_datahub(plan.get("analisis", ""))
    piezas = contexto.get("content", [])
    if piezas:
        print(f"  DataHub encontro {len(piezas)} resultados del tema:", flush=True)
        for p in piezas[:2]:
            print(f"    - {str(p)[:300]}", flush=True)
    else:
        print(f"  {contexto.get('error') or contexto.get('aviso') or piezas}", flush=True)
    print("  El agente consulta la 'memoria' del sistema antes de actuar.", flush=True)

    zona = plan.get("zona", "zona_generica")
    dias = plan.get("dias")
    ruta = ""

    etapa("4/8 GENERACION/MAPEADO de datos (sinteticos o GEE real)",
          "\"Por defecto usamos rasters sinteticos para que la demo sea rapida y reproducible; con una linea se cambia a datos reales de Sentinel-2 descargados por GEE.\"")
    if dias and int(dias) > 1:
        from terra_cognita.geo.sinteticos import generar_serie_ndvi
        n = min(int(dias), 30)
        rutas = generar_serie_ndvi("data/series", f"ndvi_{zona}", n)
        print(f"  Serie de {len(rutas)} rasters generados:", flush=True)
        for r in rutas:
            print(f"    - {r}", flush=True)
        ruta = rutas[-1] if rutas else ""
    else:
        ruta = orq.fuente.ndvi(zona)
        print(f"  Raster puntual: {ruta}", flush=True)
    print("  (en produccion la misma linea bajaria rasters reales "
          "de Sentinel-2 via GEE)", flush=True)

    etapa("5/8 CALCULO AUTOMATICO del analisis geoespacial",
          "\"El mismo pipeline calcula: porcentaje de area degradada, NDVI medio por dia, el cambio total y si eso es alerta, observacion o normal.\"")
    from terra_cognita.geo.analisis import evaluar_tendencia, evaluar_ndvi
    from terra_cognita.config import cargar_config
    cfg = cargar_config()
    umbral = cfg["alertas"]["umbral_ndvi"]
    if dias and int(dias) > 1:
        res = evaluar_tendencia(rutas, umbral)
        res["tipo_analisis"] = "tendencia"
        res["serie_rasters"] = rutas
        serie_txt = "\n".join(
            f"    - {p['fecha']}: {p['pct_bajo']}% bajo umbral, "
            f"NDVI medio {p['media_ndvi']}" for p in res["serie"])
        print(f"  Tendencia ({res['dias']} dias):", flush=True)
        print(serie_txt, flush=True)
    else:
        res = evaluar_ndvi(ruta, umbral)
        res["tipo_analisis"] = "snapshot"
    print(f"  Estado: {res['estado']}", flush=True)
    print("  El sistema calcula % de area degradada, medias y delta.", flush=True)

    etapa("6/8 CODIGO GOOGLE EARTH ENGINE auto-generado",
          "\"El agente tambien ES PROGRAMA: escribe el codigo JavaScript de Earth Engine adecuado a esta consulta, con zona pequena y descarga automatica.\"")
    codigo = orq._generar_codigo_gee(plan)
    print("  El agente 'escribe' el script JS ad-hoc de GEE:", flush=True)
    for linea in codigo.splitlines()[:14]:
        print(f"    {linea}", flush=True)
    print(f"    ... ({len(codigo.splitlines())} lineas totales)", flush=True)
    print("  Al descomentar/ejecutar en el Code Editor descarga el raster", flush=True)
    print("  (zona pequena ~2 km) y el pipeline lo procesa igual.", flush=True)

    etapa("7/8 WRITE-BACK a DataHub (linaje: otros agentes heredan)",
          "\"El resultado NO se pierde: se escribe de vuelta en el grafo de DataHub, un dataset por dia, y el resumen apunta a todos con linaje. Otro agente puede heredar este analisis.\"")
    res["zona"] = zona
    res["plan"] = plan
    res["contexto_datahub"] = contexto
    resultado = orq.cerrar_ciclo(res, consulta)
    print(f"  URN catalogado: {resultado.get('urn_datahub')}", flush=True)
    print("  Cada raster de la serie quedo como dataset + el resumen apunta", flush=True)
    print("  (upstreamLineage) a todos: el grafo guarda la memoria temporal.", flush=True)

    etapa("8/8 REPORTE FINAL (dashboard + Telegram)",
          "\"Y el circulo se cierra: el usuario lo ve en el mapa del dashboard, y el agente se comunica por Telegram con un informe claro.\"")
    print(f"  Resumen: {resultado.get('resumen')}", flush=True)
    alerta = resultado.get("alerta")
    if isinstance(alerta, dict) and alerta.get("message_id"):
        print(f"  Telegram: enviado (message_id {alerta['message_id']})", flush=True)
    elif isinstance(alerta, dict) and alerta.get("aviso"):
        print(f"  Telegram: {alerta['aviso']}", flush=True)
    else:
        print("  Telegram: no aplica (sin alerta)", flush=True)

    print("\n" + "=" * 72, flush=True)
    print("  FLUJO COMPLETO: consulta -> IA -> DataHub(MCP) -> raster ->", flush=True)
    print("  analisis -> codigo GEE -> write-back -> reporte Telegram", flush=True)
    print("=" * 72, flush=True)


if __name__ == "__main__":
    main()