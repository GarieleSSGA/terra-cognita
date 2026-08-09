"""Generación de rasters sintéticos para demos rápidas y pruebas offline.

Misma interfaz de salida que la fuente GEE real: un GeoTIFF con banda(s).
El agente no distingue de dónde viene el dato -> demo reproducible sin auth.
"""
import numpy as np
import rasterio
from rasterio.transform import from_bounds


def generar_ndvi_sintetico(ruta_salida: str,
                           ancho: int = 120,
                           alto: int = 120,
                           lon_oeste: float = -77.20,
                           lat_sur: float = -12.20,
                           lon_este: float = -76.90,
                           lat_norte: float = -11.90,
                           semilla: int = 42) -> str:
    """Genera un raster NDVI sintético: zonas urbanas (bajo), vegetación (alto),
    y un foco de degradación (bajo) en el noreste."""
    rng = np.random.default_rng(semilla)
    base = rng.uniform(0.15, 0.85, (alto, ancho))

    base[: int(alto * 0.2), :] = np.clip(base[: int(alto * 0.2), :], 0.05, 0.25)
    base[int(alto * 0.75):, int(ancho * 0.7):] = 0.05

    yy, xx = np.ogrid[:alto, :ancho]
    foco_c = (ancho * 0.85, alto * 0.35)
    dist = np.sqrt(((xx - foco_c[0]) / (ancho / 6)) ** 2 + ((yy - foco_c[1]) / (alto / 6)) ** 2)
    base[dist < 1] = np.linspace(0.55, 0.05, alto)[
        np.minimum(((dist[dist < 1] / 1.0) * (alto - 1)).astype(int), alto - 1)]

    transform = from_bounds(lon_oeste, lat_sur, lon_este, lat_norte, ancho, alto)
    with rasterio.open(
        ruta_salida, "w", driver="GTiff",
        height=alto, width=ancho, count=1, dtype="float32",
        crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(base.astype("float32"), 1)
    return ruta_salida


def generar_lluvia_sintetica(ruta_salida: str, dias: int = 1,
                             ancho: int = 120, alto: int = 120,
                             lon_oeste: float = -77.20, lat_sur: float = -12.20,
                             lon_este: float = -76.90, lat_norte: float = -11.90,
                             semilla: int = 7) -> str:
    """Raster de precipitación diaria (mm) con un núcleo de lluvia intensa."""
    rng = np.random.default_rng(semilla)
    base = rng.gamma(2.0, 5.0, (alto, ancho))
    yy, xx = np.ogrid[:alto, :ancho]
    c = (ancho * 0.4, alto * 0.5)
    base += 80.0 * np.exp(-(((xx - c[0]) / (ancho / 10)) ** 2) - (((yy - c[1]) / (alto / 10)) ** 2))
    transform = from_bounds(lon_oeste, lat_sur, lon_este, lat_norte, ancho, alto)
    with rasterio.open(
        ruta_salida, "w", driver="GTiff",
        height=alto, width=ancho, count=1, dtype="float32",
        crs="EPSG:4326", transform=transform,
    ) as dst:
        dst.write(base.astype("float32"), 1)
    return ruta_salida