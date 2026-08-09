"""Demo rapida de Terra Cognita (sin DataHub ni Telegram, todo local):
- pregunta al agente -> interpreta con Ollama (o heuristica si no hay olla)
- analiza el NDVI sintetico de Lima
- imprime el resumen + decide si habria alerta

Uso:  python scripts/demo_rapida.py "cual es el NDVI de Lima"
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from terra_cognita.agent.orquestador import Orquestador


def main():
    consulta = sys.argv[1] if len(sys.argv) > 1 else (
        "¿Cual es el nivel de vegetacion (NDVI) en Lima?")
    orq = Orquestador()
    print(f">> Consulta: {consulta}\n")

    resultado = orq.ejecutar(consulta)

    print("== PLAN (Ollama) ==")
    plan = resultado.get("plan", {})
    print(f"  analisis : {plan.get('analisis')}")
    print(f"  zona     : {plan.get('zona')}")
    print(f"  fallback : {'sin Ollama: ' + plan.get('ollama_error', '') if plan.get('ollama_error') else 'no'}")

    print("\n== CONTEXTO DataHub ==")
    for item in resultado.get("contexto_datahub", []):
        print(f"  {item}")

    print("\n== RESULTADO ==")
    for k, v in resultado.items():
        if k not in ("plan", "contexto_datahub", "resumen"):
            print(f"  {k}: {v}")
    print(f"  umbral  : {resultado.get('resumen', {}).get('ndvi')}")

    if "ALERTA" in str(resultado.get("estado", "")):
        print("\n[!] Se generaria alerta temprana (configura Telegram para enviarla)")


if __name__ == "__main__":
    main()