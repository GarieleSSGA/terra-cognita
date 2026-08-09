"""Capa unificada de datos geoespaciales.

Elige la fuente según config: 'sintetico' (demo rápida, sin auth) o 'gee'
(Sentinel-2 real vía Google Earth Engine). La demo no se rompe si GEE
no está disponible: la fuente sintética es el modo por defecto.
"""
from pathlib import Path

from .sinteticos import generar_ndvi_sintetico, generar_lluvia_sintetica

OL = -77.20  # lon oeste bbox (Lima)
SL = -12.20  # lat sur
EL = -76.90  # lon este
NL = -11.90  # lat norte


class FuenteData:
    """Interfaz: mis APIs => un GeoTIFF listo para analizar."""

    def __init__(self, fuente: str = "sintetico", ruta_base: Path | None = None,
                 proyecto_gee: str = ""):
        self.fuente = fuente
        self.ruta_base = ruta_base or Path("data")
        self.proyecto_gee = proyecto_gee

    def ndvi(self, zona: str) -> str:
        ruta = self.ruta_base / f"ndvi_{zona}.tif"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if self.fuente == "sintetico":
            return generar_ndvi_sintetico(str(ruta))
        from .gee import descargar_ndvi_gee
        return descargar_ndvi_gee(OL, SL, EL, NL, str(ruta),
                                  proyecto=self.proyecto_gee)

    def lluvia(self, zona: str) -> str:
        ruta = self.ruta_base / f"lluvia_{zona}.tif"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        return generar_lluvia_sintetica(
            str(ruta),
            lon_oeste=OL, lat_sur=SL, lon_este=EL, lat_norte=NL)