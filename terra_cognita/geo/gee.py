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

    Síncrono y sin Google Drive: calcula el promedio de la ventana y baja los
    bytes con `getDownloadURL` (escala 500 m para que el tile quede pequeno).
    Requiere credenciales GEE: `earthengine authenticate` una sola vez.
    Si GEE no está disponible, lanza un mensaje claro (el flujo usa
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

    url = ndvi.getDownloadURL({
        "scale": 500, "region": region,
        "format": "GEO_TIFF", "crs": "EPSG:4326"})
    import requests
    respuesta = requests.get(url, timeout=300)
    respuesta.raise_for_status()

    ruta = Path(ruta_salida)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(respuesta.content)
    return f"NDVI GEE descargado ({len(respuesta.content)} bytes) -> {ruta}"