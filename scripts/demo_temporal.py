"""Demo del modo TENDENCIA (agente espacial-temporal) de Terra Cognita.

Responde consultas como:
  "dame la vegetacion de Lima de los ultimos 7 dias"
  "como esta evolucionando la sequia en Lima esta semana"

Flujo: interpreta (Ollama | llm_api | heuristica) -> serie sintetica de 1
raster por dia (o GEE real si config.fuente_default=gee) -> analisis de
tendencia (pct bajo umbral dia a dia, delta, direccion) -> informe

La salida es texto plano listo para copiar en un reporte o pegar en la UI.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from terra_cognita.agent.orquestador import Orquestador


def barra(pct: float, ancho: int = 30) -> str:
    n = max(0, min(ancho, int(round(pct / 100 * ancho))))
    return "#" * n + "." * (ancho - n)


def main():
    consulta = sys.argv[1] if len(sys.argv) > 1 else (
        "dame la vegetacion de Lima de los ultimos 7 dias")
    orq = Orquestador()
    print(f">> Consulta: {consulta}\n", flush=True)

    resultado = orq.ejecutar(consulta)
    plan = resultado.get("plan", {})
    via = ("cerebro local" if not plan.get("ollama_error")
           else "heuristica" if "Ollama" in str(plan.get("ollama_error"))
           else plan.get("via", "heuristica"))
    print(f"[Plan] {plan.get('analisis')} en {plan.get('zona')} | "
          f"dias={plan.get('dias')} | via: {via}", flush=True)

    contexto = resultado.get("contexto_datahub", {})
    if isinstance(contexto, dict) and contexto.get("error"):
        print(f"[DataHub] aviso: {contexto['error'][:100]}", flush=True)
    else:
        print("[DataHub] contexto MCP consultado (sin alucinar)", flush=True)

    serie = resultado.get("serie", [])
    ten = resultado.get("tendencia")
    print("\n== INFORME DE TENDENCIA (NDVI) ==", flush=True)

    if not serie:
        print(f" (analisis puntual) {resultado}", flush=True)
        return

    print(f" Zona   : {resultado.get('zona')}", flush=True)
    print(f" Periodo: {serie[0]['fecha']} -> {serie[-1]['fecha']} "
          f"({resultado.get('dias')} dias)", flush=True)
    print(f" Umbral de alerta: {orq.config['alertas']['umbral_ndvi']} "
          "(NDVI bajo este valor = vegetacion estresada/degradada)", flush=True)
    print("", flush=True)
    print(f" {'Fecha':<12}{'area baja':>10}{'NDVI medio':>12}   {('bajo umbral ' + str(orq.config['alertas']['umbral_ndvi'])):<30}", flush=True)
    for p in serie:
        print(f" {p['fecha']:<12}{str(p['pct_bajo'])+'%':>10}"
              f"{p['media_ndvi']:>12.3f}   {barra(p['pct_bajo'])}", flush=True)
    print("", flush=True)
    print(f" Cambio total: area bajo umbral {resultado.get('pct_bajo_inicial')}%"
          f" -> {resultado.get('pct_bajo_final')}% "
          f"(delta {resultado.get('delta_pct'):+.1f}pp); "
          f"NDVI medio {resultado.get('delta_media_ndvi'):+.3f}", flush=True)
    print(f" Conclusion  : vegetacion {resultado.get('tendencia')}. "
          f"{resultado.get('estado')}", flush=True)
    print(f" Resumen     : {resultado.get('resumen')}", flush=True)

    if "ALERTA" in str(resultado.get("estado", "")):
        print("\n[!] Se activaria alerta temprana (Telegram si esta configurado)", flush=True)

    try:
        urn = orq.cerrar_ciclo(resultado, consulta)["urn_datahub"]
        print(f"\n[DataHub] serie catalogada con linaje multiple: {urn}", flush=True)
    except Exception as exc:
        import traceback
        print(f"\n[DataHub] aviso al catalogar serie: {exc}", flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    main()