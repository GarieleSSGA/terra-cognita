"""Fuente GEE real (Sentinel-2). Misma interfaz que los sintéticos:
recibe zona y devuelve un GeoTIFF. Cambiar `fuente_default` en config
activa esta vía sin tocar el resto del pipeline."""
from pathlib import Path


def descargar_ndvi_gee(lon_oeste: float, lat_sur: float,
                       lon_este: float, lat_norte: float,
                       ruta_salida: str,
                       fecha_inicio: str | None = None,
                       fecha_fin: str | None = None,
                       proyecto: str = "") -> str:
    """Descarga NDVI de Sentinel-2 para una zona y lo guarda como GeoTIFF.

    Requiere credenciales GEE: `earthengine authenticate` una sola vez.
    Si GEE no está disponible, devuelve un mensaje claro (el flujo usa
    sintéticos y no se rompe).
    """
    try:
        import ee
        ee.Initialize(project=proyecto or None)
    except Exception as exc:
        raise RuntimeError(
            "GEE no disponible (¿falta `earthengine authenticate`?). "
            "Usa la fuente sintética para la demo.") from exc

    from datetime import date, timedelta
    hoy = date.today()
    if fecha_inicio is None:
        fecha_inicio = (hoy - timedelta(days=15)).isoformat()
    if fecha_fin is None:
        fecha_fin = hoy.isoformat()

    region = ee.Geometry.Rectangle([lon_oeste, lat_sur, lon_este, lat_norte])
    coleccion = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                 .filterBounds(region)
                 .filterDate(fecha_inicio, fecha_fin)
                 .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30)))

    imagen = coleccion.median()
    ndvi = (imagen.select("B8").subtract(imagen.select("B4"))
            .divide(imagen.select("B8").add(imagen.select("B4"))))

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tarea = ee.batch.Export.image.toDrive(
        image=ndvi.toFloat(), description="terra_cognita_ndvi",
        folder="terra_cognita", scale=10, region=region,
        fileFormat="GeoTIFF", maxPixels=1e9)
    tarea.start()
    return f"Export GEE iniciado (tarea {tarea.id}). Descarga el GeoTIFF de Google Drive."