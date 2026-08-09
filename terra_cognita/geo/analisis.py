"""Estadísticas y análisis sobre rasters (NDVI, lluvia) para las alertas."""
import json
from pathlib import Path

import numpy as np
import rasterio


def estadisticas_raster(ruta_tif: str) -> dict:
    """Media, desvío, min/max y píxeles bajos del raster."""
    with rasterio.open(ruta_tif) as src:
        arr = src.read(1)
        arr = arr[~np.isnan(arr)]
        if arr.size == 0:
            return {"error": "raster vacío"}
        return {
            "media": float(np.mean(arr)), "desvio": float(np.std(arr)),
            "min": float(np.min(arr)), "max": float(np.max(arr)),
            "pixeles": int(arr.size),
        }


def evaluar_ndvi(ruta_tif: str, umbral: float = 0.3) -> dict:
    """Clasifica vegetación: pct de área sobre/bajo el umbral."""
    with rasterio.open(ruta_tif) as src:
        arr = src.read(1)
    arr = arr[~np.isnan(arr)]
    total = arr.size
    bajo = float(np.mean(arr < umbral) * 100) if total else 0.0
    return {
        "pct_bajo_umbral": round(bajo, 1),
        "estado": "ALERTA: vegetación baja" if bajo >= 50 else "OK",
    }


def evaluar_lluvia(ruta_tif: str, umbral_mm: float = 50) -> dict:
    """Riesgo de inundación según precipitación sobre el umbral."""
    with rasterio.open(ruta_tif) as src:
        arr = src.read(1)
    arr = arr[~np.isnan(arr)]
    max_mm = float(np.max(arr)) if arr.size else 0.0
    return {
        "max_mm": round(max_mm, 1),
        "media_mm": round(float(np.mean(arr)), 1) if arr.size else 0.0,
        "estado": "ALERTA: lluvia intensa" if max_mm >= umbral_mm else "OK",
    }


def valor_en_punto(ruta_tif: str, lat: float, lon: float) -> dict:
    """Devuelve el valor del raster en la coordenada dada."""
    with rasterio.open(ruta_tif) as src:
        fila, col = src.index(lon, lat)
        valor = src.read(1)[fila, col]
        return {"lat": lat, "lon": lon, "valor": float(valor)}


def resumen_a_json(ruta_tif: str, tipo: str = "ndvi") -> dict:
    """Resumen completo (para el write-back a DataHub."""
    est = estadisticas_raster(ruta_tif)
    with rasterio.open(ruta_tif) as src:
        est["crs"] = str(src.crs)
        est["shape"] = (src.height, src.width)
        bounds = src.bounds
        est["bounds"] = [bounds.left, bounds.bottom, bounds.right, bounds.top]
    est[tipo] = (evaluar_lluvia(ruta_tif) if tipo == "lluvia"
                 else evaluar_ndvi(ruta_tif))
    return est