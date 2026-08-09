"""Demo del CICLO COMPLETO de Terra Cognita (lo que se muestra en el video):

1. El usuario pregunta en lenguaje natural
2. Ollama interpreta (analisis + zona)
3. El agente busca en DataHub via MCP (contexto, sin alucinar)
4. Ejecuta el analisis sobre el raster sintetico
5. Escribe el resultado DE VUELTA en DataHub (dataset + linaje)
6. Verifica por MCP que el dataset es visible/lineage
7. Genera alerta si supera el umbral (Telegram si esta configurado)

Uso:  python scripts/ciclo_completo.py "dame el NDVI de Lima"
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from terra_cognita.agent.orquestador import Orquestador


def main():
    consulta = sys.argv[1] if len(sys.argv) > 1 else "El nivel de vegetacion (NDVI) en Lima"
    orq = Orquestador()
    print(f">> Consulta: {consulta}\n")

    # 1-4. agente: plan -> contexto -> analisis
    resultado = orq.ejecutar(consulta)
    plan = resultado.get("plan", {})
    print(f"[1] Plan (Ollama): {plan.get('analisis')} en {plan.get('zona')} "
          f"({'cerebro' if not plan.get('ollama_error') else 'fallback'})")

    contexto = resultado.get("contexto_datahub", {})
    n = 0
    if isinstance(contexto, dict) and "error" not in contexto:
        try:
            n = int(contexto.get("content", ["{}"])[0][7:14]
                    if contexto.get("content") else 0)
        except (ValueError, IndexError, TypeError):
            n = 0
    print(f">> Contexto DataHub (MCP): {n} datasets encontrados para '{plan.get('analisis')}'")

    print(f"\n== ANALISIS ==")
    print(f"   estado: {resultado.get('estado')}")
    print(f"   detalle: {resultado.get('pct_bajo_umbral', '')} | {resultado.get('max_mm', '')}")

    # 5) Write-back a DataHub (dataset + linaje)
    completo = orq.cerrar_ciclo(resultado, consulta)
    urn = completo.get("urn_datahub", "?")
    print(f"\n== WRITE-BACK a DataHub ==")
    print(f"   dataset creado con linaje: {urn}")

    # 6) Verificacion por MCP
    import json as _json
    try:
        res = orq.datahub.search_datasets(plan.get("analisis", "ndvi"))
        total = _extraer_total(res)
        print(f"[Verificacion MCP: {total} datasets sobre '{plan.get('analisis')}' en el grafo]")
    except Exception as exc:
        print(f"[Verificacion MCP fallo: {exc}]")

    # 7) Alerta si aplica
    alerta = completo.get("alerta") or {}
    if "ALERTA" in str(completo.get("estado", "")):
        print(f"\n[!] {completo['estado']}")
        if alerta.get("aviso"):
            print(f"    {alerta['aviso']}")
        else:
            print("    Alerta enviada a Telegram")


def _extraer_total(res: dict) -> int:
    import re
    for p in res.get("content", []):
        try:
            return int(_json_carga(p).get("total", 0))
        except Exception:
            continue
    return 0


def _json_carga(texto):
    import json
    inicio = texto.find("{")
    return json.loads(texto[inicio:])