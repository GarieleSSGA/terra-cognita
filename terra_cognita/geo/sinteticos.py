"""Generación de rasters sintéticos para demos rápidas y pruebas offline.

Misma interfaz de salida que la fuente GEE real: un GeoTIFF con banda(s).
El agente no distingue de dónde viene el dato -> demo reproducible sin auth.
"""
import numpy as np
import rasterio
from pathlib import Path
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


def generar_humedad_sintetica(ruta_salida: str, ancho: int = 120, alto: int = 120,
                              lon_oeste: float = -77.20, lat_sur: float = -12.20,
                              lon_este: float = -76.90, lat_norte: float = -11.90,
                              semilla: int = 11) -> str:
    """Raster de humedad del suelo (% 0-100): pastizales secos al N, humedos al S."""
    rng = np.random.default_rng(semilla)
    base = rng.normal(45.0, 12.0, (alto, ancho))
    base = np.clip(base, 2.0, 90.0)
    base[: int(alto * 0.25), :] = np.clip(
        base[: int(alto * 0.25), :], 2.0, 28.0)      # zona seca al norte
    yy, xx = np.ogrid[:alto, :ancho]
    c = (ancho * 0.5, alto * 0.85)
    rio = 55.0 * np.exp(-(((xx - c[0]) / (ancho / 14)) ** 2)
                        - (((yy - c[1]) / (alto / 10)) ** 2))
    base = np.clip(base + rio, 0.0, 100.0)
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


def generar_serie_ndvi(directorio_salida: str, nombre_base: str, dias: int = 7,
                       fechas: list[str] | None = None,
                       ancho: int = 120, alto: int = 120,
                       lon_oeste: float = -77.20, lat_sur: float = -12.20,
                       lon_este: float = -76.90, lat_norte: float = -11.90,
                       semilla: int = 42) -> list[str]:
    """Serie temporal NDVI: un GeoTIFF por fecha en el directorio.

    Evolución artificial: cada día el foco de degradación del noreste
    crece y la media global baja ligeramente (tendencia realista, no
    aleatoria por fecha). Devuelve las rutas ordenadas por fecha.
    """
    from datetime import date, timedelta

    if fechas is None:
        hoy = date.today()
        fechas = [(hoy - timedelta(days=dias - 1 - i)).isoformat()
                  for i in range(dias)]

    rng = np.random.default_rng(semilla)
    base = rng.uniform(0.15, 0.85, (alto, ancho))
    base[: int(alto * 0.2), :] = np.clip(base[: int(alto * 0.2), :], 0.05, 0.25)

    yy, xx = np.ogrid[:alto, :ancho]
    eje = np.sqrt(((xx - ancho * 0.85) / (ancho / 6)) ** 2
                  + ((yy - alto * 0.35) / (alto / 6)) ** 2)

    rutas = []
    for i, fecha in enumerate(fechas):
        progreso = (i + 1) / max(len(fechas), 1)   # 0..1 a lo largo de la serie
        arr = base.copy()
        radio = (ancho / 6) * (0.9 + 0.8 * progreso)
        degradacion = np.clip(
            np.linspace(0.5, 0.05, alto)[
                np.minimum(np.clip(eje / max(radio, 1e-9), 0, 0.99) * (alto - 1), alto - 1).astype(int)],
            0.02, 0.5)
        arr[eje < radio * 1.15] = np.minimum(
            arr[eje < radio * 1.15], degradacion[eje < radio * 1.15])
        arr = arr - 0.03 * progreso                       # declive global
        arr = np.clip(arr, 0.0, 1.0)                      # NDVI en [0,1]

        ruta = (Path(directorio_salida) /
                f"{nombre_base}_{fecha}.tif").resolve()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        transform = from_bounds(lon_oeste, lat_sur, lon_este, lat_norte,
                                ancho, alto)
        with rasterio.open(
            ruta, "w", driver="GTiff",
            height=alto, width=ancho, count=1, dtype="float32",
            crs="EPSG:4326", transform=transform,
        ) as dst:
            dst.write(arr.astype("float32"), 1)
        rutas.append(str(ruta))
    return rutas