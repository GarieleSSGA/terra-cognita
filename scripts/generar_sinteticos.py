"""Genera los rasters sinteticos de la demo en data/sinteticos/."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from terra_cognita.geo.sinteticos import (
    generar_ndvi_sintetico, generar_lluvia_sintetica)

SALIDAS = ROOT / "data" / "sinteticos"


def main():
    SALIDAS.mkdir(parents=True, exist_ok=True)
    ndvi = generar_ndvi_sintetico(str(SALIDAS / "ndvi_lima_demo.tif"))
    lluvia = generar_lluvia_sintetica(str(SALIDAS / "lluvia_lima_demo.tif"))
    print(f"NDVI  -> {ndvi}")
    print(f"Lluvia-> {lluvia}")
    print("Demo lista. Ejecuta ahora: python scripts/demo_rapida.py")


if __name__ == "__main__":
    main()