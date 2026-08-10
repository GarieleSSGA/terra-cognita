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


def evaluar_humedad(ruta_tif: str, umbral_seca: float = 30) -> dict:
    """Humedad de suelo: % del área seca (< umbral) y media general."""
    with rasterio.open(ruta_tif) as src:
        arr = src.read(1)
    arr = arr[~np.isnan(arr)]
    total = arr.size
    seca = float(np.mean(arr < umbral_seca) * 100) if total else 0.0
    return {
        "pct_area_seca": round(seca, 1),
        "humedad_media_pct": round(float(np.mean(arr)), 1) if total else 0.0,
        "estado": "ALERTA: suelo seco" if seca >= 50 else "OK",
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


# ------------------------------------------------------------------ temporal
def evaluar_tendencia(archivos: list[str], umbral: float = 0.3) -> dict:
    """Serie temporal: % de área bajo umbral día a día + dirección del cambio.

    - `archivos`: rutas GeoTIFF ordenadas por fecha (ver generar_serie_ndvi).
    - Devuelve las fechas (del nombre del archivo), el % bajo umbral de cada
      día, la media de NDVI, el delta total y el estado de alerta.
    """
    serie = []
    for ruta in archivos:
        nombre = Path(ruta).stem
        fecha = nombre.split("_")[-1] if "_" in nombre else "?"
        with rasterio.open(ruta) as src:
            arr = src.read(1)
        arr = arr[~np.isnan(arr)]
        if arr.size == 0:
            continue
        pct = float(np.mean(arr < umbral) * 100)
        serie.append({"fecha": fecha, "pct_bajo": round(pct, 1),
                      "media_ndvi": round(float(np.mean(arr)), 3)})

    if not serie:
        return {"error": "serie vacía"}

    primero, ultimo = serie[0], serie[-1]
    delta_pct = round(ultimo["pct_bajo"] - primero["pct_bajo"], 1)
    delta_media = round(ultimo["media_ndvi"] - primero["media_ndvi"], 3)
    pico_alarma = max(p["pct_bajo"] for p in serie)

    if pico_alarma >= 50:
        estado = "ALERTA: vegetación baja"
    elif delta_pct > 5:
        estado = "ALERTA: degradación en aumento"
    elif delta_pct > 0:
        estado = "OBSERVACION: deterioro leve"
    else:
        estado = "OK"

    tendencia = ("en declive" if delta_media < -0.02
                 else "estable" if abs(delta_media) <= 0.02
                 else "en mejora")
    return {
        "dias": len(serie),
        "serie": serie,
        "primera_fecha": primero["fecha"],
        "ultima_fecha": ultimo["fecha"],
        "pct_bajo_inicial": primero["pct_bajo"],
        "pct_bajo_final": ultimo["pct_bajo"],
        "delta_pct": delta_pct,
        "delta_media_ndvi": delta_media,
        "tendencia": tendencia,
        "estado": estado,
        "resumen": (
            f"Ultimos {len(serie)} dias: area bajo umbral paso de "
            f"{primero['pct_bajo']}% a {ultimo['pct_bajo']}% "
            f"(delta {delta_pct:+.1f}pp); NDVI medio {delta_media:+.3f} "
            f"-> vegetacion {tendencia}. Estado: {estado}."
        ),
    }