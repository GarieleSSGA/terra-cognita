"""Generador de cÃ³digo Google Earth Engine (JavaScript para el Code Editor).

El agente decide el anÃ¡lisis (NDVI, lluvia, humedad, NDWI, LST, EVI, serie
temporal...) y aquÃ­ se produce un script GEE AD-HOC para esa consulta:
parÃ¡metros (bbox, fechas, dÃ­as, escala) interpolados en plantillas fijas
pero distintas entre sÃ­. Cada consulta genera un cÃ³digo diferente.

Uso desde el orquestador:  resultado["codigo_gee"] = generar_codigo_gee(plan)
"""
from datetime import date, timedelta

# Bbox por defecto: zona PEQUEÑA (~2x2 km en Lima) para descargas rapidas
# y dentro de la cuota gratuita de GEE. Se amplia/con plaza con plan["bbox"].
LIMA = {"lon_oeste": -77.060, "lat_sur": -12.070,
        "lon_este": -77.040, "lat_norte": -12.050}

# variable de salida de cada plantilla (para el bloque de descarga)
VARIABLE_SALIDA = {"ndvi": "ndvi", "lluvia": "total", "humedad": "smap",
                   "ndwi": "ndwi", "lst": "mod", "evi": "evi", "serie": "ndvi"}


def _bbox_objeto(plan: dict) -> dict:
    b = plan.get("bbox") or {}
    return {**LIMA, **b}


def _fechas(plan: dict) -> tuple[str, str]:
    dias = plan.get("dias")
    hoy = date.today()
    if dias and int(dias) > 1:
        return (hoy - timedelta(days=int(dias))).isoformat(), hoy.isoformat()
    return (hoy - timedelta(days=15)).isoformat(), hoy.isoformat()


PLANTILLAS = {
    "ndvi": """// TERRA COGNITA :: Vegetacion (NDVI) â€” Sentinel-2
// Generado automaticamente para: __ZONA__
// Analisis: NDVI __DIAS__ dias, escala __ESCALA__m
var zona = ee.Geometry.Rectangle(__COORDS__);
var fechas = ee.DateRange('__FINI__', '__FFIN__');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(zona).filterDate(fechas)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));
var ndvi = s2.median().normalizedDifference(['B8', 'B4']).rename('ndvi');
var paleta = ['#8B0000','#FFD700','#228B22'];   // seco -> vegetado
Map.centerObject(zona, 11);
Map.addLayer(ndvi.clip(zona), {min: -0.2, max: 0.8, palette: paleta}, 'NDVI __ZONA__');
Export.image.toDrive({image: ndvi.clip(zona), description: 'TC_ndvi___ZONA__',
  folder: 'terra_cognita', scale: __ESCALA__, region: zona, maxPixels: 1e9});
print('Media NDVI:', ndvi.clip(zona).reduceRegion(
  ee.Reducer.mean(), zona, __ESCALA__).get('ndvi'));
""",

    "lluvia": """// TERRA COGNITA :: Precipitacion (CHIRPS diario)
// Generado automaticamente para: __ZONA__
var zona = ee.Geometry.Rectangle(__COORDS__);
var fechas = ee.DateRange('__FINI__', '__FFIN__');
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .filterBounds(zona).filterDate(fechas);
var total = chirps.sum().multiply(1).rename('precip_mm');
Map.centerObject(zona, 11);
Map.addLayer(total.clip(zona), {min: 0, max: 200,
  palette: ['#FFFFFF','#BDFFF', '#0066FF', '#000099']}, 'Lluvia __ZONA__');
Export.image.toDrive({image: total.clip(zona), description: 'TC_lluvia___ZONA__',
  folder: 'terra_cognita', scale: __ESCALA__, region: zona, maxPixels: 1e9});
print('Acumulado (mm):', total.clip(zona).reduceRegion(
  ee.Reducer.sum(), zona, __ESCALA__).get('precip_mm'));
""",

    "humedad": """// TERRA COGNITA :: Humedad del suelo (SMAP L4 o ERA5 diario)
// Generado automaticamente para: __ZONA__
var zona = ee.Geometry.Rectangle(__COORDS__);
var fechas = ee.DateRange('__FINI__', '__FFIN__');
var smap = ee.ImageCollection('NASA_SMAP/SPL4SMGP/006')
  .filterBounds(zona).filterDate(fechas)
  .select('sm_surface_0_10cm').mean().multiply(100).rename('humedad_pct');
Map.centerObject(zona, 11);
Map.addLayer(smap.clip(zona), {min: 0, max: 60,
  palette: ['#FFE4B5','#FFFF00','#228B22','#0000FF']}, 'Humedad __ZONA__');
Export.image.toDrive({image: smap.clip(zona), description: 'TC_humedad___ZONA__',
  folder: 'terra_cognita', scale: __ESCALA__, region: zona, maxPixels: 1e9});
print('Humedad media (%):', smap.clip(zona).reduceRegion(
  ee.Reducer.mean(), zona, __ESCALA__).get('humedad_pct'));
""",

    "ndwi": """// TERRA COGNITA :: Agua (NDWI) â€” Sentinel-2
// Generado automaticamente para: __ZONA__
var zona = ee.Geometry.Rectangle(__COORDS__);
var fechas = ee.DateRange('__FINI__', '__FFIN__');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(zona).filterDate(fechas)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));
var ndwi = s2.median().normalizedDifference(['B3', 'B8']).rename('ndwi');
Map.centerObject(zona, 11);
Map.addLayer(ndwi.clip(zona), {min: -0.4, max: 0.6,
  palette: ['#8B4513','#FFFFFF','#0000FF']}, 'NDWI __ZONA__');
Export.image.toDrive({image: ndwi.clip(zona), description: 'TC_ndwi___ZONA__',
  folder: 'terra_cognita', scale: __ESCALA__, region: zona, maxPixels: 1e9});
print('Agua media:', ndwi.clip(zona).reduceRegion(
  ee.Reducer.mean(), zona, __ESCALA__).get('ndwi'));
""",

    "lst": """// TERRA COGNITA :: Temperatura superficial (LST) â€” MODIS
// Generado automaticamente para: __ZONA__
var zona = ee.Geometry.Rectangle(__COORDS__);
var fechas = ee.DateRange('__FINI__', '__FFIN__');
var mod = ee.ImageCollection('MODIS/061/MOD11A1')
  .filterBounds(zona).filterDate(fechas)
  .select('LST_Day_1km').mean().multiply(0.02).subtract(273.15).rename('lst_c');
Map.centerObject(zona, 11);
Map.addLayer(mod.clip(zona), {min: 0, max: 45,
  palette: ['#0000FF','#00FF00','#FFFF00','#FF0000']}, 'LST __ZONA__');
Export.image.toDrive({image: mod.clip(zona), description: 'TC_lst___ZONA__',
  folder: 'terra_cognita', scale: __ESCALA__, region: zona, maxPixels: 1e9});
print('LST media (C):', mod.clip(zona).reduceRegion(
  ee.Reducer.mean(), zona, __ESCALA__).get('lst_c'));
""",

    "evi": """// TERRA COGNITA :: Ãndice EVI (vegetacion robusta) â€” Sentinel-2
// Generado automaticamente para: __ZONA__
var zona = ee.Geometry.Rectangle(__COORDS__);
var fechas = ee.DateRange('__FINI__', '__FFIN__');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(zona).filterDate(fechas)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)).median();
var evi = s2.expression(
  '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
  {'NIR': s2.select('B8'), 'RED': s2.select('B4'), 'BLUE': s2.select('B2')}
).rename('evi');
Map.centerObject(zona, 11);
Map.addLayer(evi.clip(zona), {min: -0.2, max: 1.0,
  palette: ['#8B0000','#FFD700','#228B22']}, 'EVI __ZONA__');
Export.image.toDrive({image: evi.clip(zona), description: 'TC_evi___ZONA__',
  folder: 'terra_cognita', scale: __ESCALA__, region: zona, maxPixels: 1e9});
print('EVI medio:', evi.clip(zona).reduceRegion(
  ee.Reducer.mean(), zona, __ESCALA__).get('evi'));
""",

    "serie": """// TERRA COGNITA :: Serie temporal NDVI (evolucion) â€” Sentinel-2
// Generado automaticamente para: __ZONA__
var zona = ee.Geometry.Rectangle(__COORDS__);
var fechas = ee.DateRange('__FINI__', '__FFIN__');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(zona).filterDate(fechas)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));
var ndvi = s2.map(function(img) {
  return img.normalizedDifference(['B8', 'B4']).rename('ndvi')
    .copyProperties(img, ['system:time_start']);
});
var serie = ndvi.map(function(img) {
  var m = img.reduceRegion(ee.Reducer.mean(), zona, __ESCALA__);
  return ee.Feature(null, {'fecha': img.date().format(), 'ndvi': m.get('ndvi')});
}).filter(ee.Filter.notNull(['ndvi']));
// Grafico de la serie
var chart = ui.Chart.feature.byFeature(serie, 'fecha', 'ndvi')
  .setOptions({title: 'NDVI __ZONA__ â€” ultimos __DIAS__ dias', vAxis: {min: 0, max: 1}});
print(chart);
Export.table.toDrive({collection: serie, description: 'TC_serie___ZONA__',
  folder: 'terra_cognita', fileFormat: 'CSV'});
""",
}

ANALISIS_VALIDOS = tuple(PLANTILLAS.keys())


def mapear_analisis(analisis: str) -> str:
    """Normaliza un analisis del plan a una plantilla GEE (default ndvi)."""
    a = (analisis or "").lower()
    if a in ("lluvia", "precipitacion", "inundacion"):
        return "lluvia"
    if a in ("humedad", "humedad_suelo", "suelo"):
        return "humedad"
    if a in ("ndwi", "agua", "inundacion_agua"):
        return "ndwi"
    if a in ("lst", "temperatura", "temperatura_superficial", "calor"):
        return "lst"
    if a in ("evi",):
        return "evi"
    if a in ("serie", "tendencia", "evolucion"):
        return "serie"
    return "ndvi"


def _bloque_descarga(analisis: str, zona: str, escala: int, var: str) -> str:
    """Cierra el script con la descarga automatica del raster (zona pequena).

    getDownloadURL devuelve un enlace GEOTIFF que se descarga directo del
    Code Editor; Export.image.toDrive guarda el archivo en Drive. Con la
    zona pequena (~2 km) la tarea termina en segundos y cabe en la cuota.
    """
    if analisis == "serie":
        return (
            "// ===== DESCARGA AUTOMATICA (serie) =====\n"
            "// serie.csv ya sale via Export.table.toDrive (arriba).\n"
            "// Para raster por dia, repite con ndvi.filterDate(fecha) en un loop.\n")
    return (
        f"// ===== DESCARGA AUTOMATICA ({zona}, bbox pequeno ~2 km) =====\n"
        f"// 1) Enlace directo GEOTIFF (requiere cuenta autenticada):\n"
        f"print({var}.clip(zona).getDownloadURL({{scale: {escala}, "
        f"region: zona, format: 'GEO_TIFF'}}));\n"
        f"// 2) Guardar en Google Drive (tarea asincrona en la pestana Tasks):\n"
        f"// Export.image.toDrive({{image: {var}.clip(zona), "
        f"description: 'TC_{analisis}_{zona}', folder: 'terra_cognita', "
        f"scale: {escala}, region: zona, maxPixels: 1e9}});\n")


def generar_codigo_gee(plan: dict, escala: int = 250) -> str:
    """Devuelve el script JavaScript de Earth Engine para el plan.

    Diferente para cada analisis/zona/fechas: el agente 'escribe codigo'
    segun lo que pida el usuario (requisito de la hackaton). Cierra con la
    descarga automatica del raster (zona pequena por defecto).
    """
    analisis = mapear_analisis(plan.get("analisis", "ndvi"))
    zona = plan.get("zona", "zona").replace(" ", "_")
    b = _bbox_objeto(plan)
    f_inicio, f_fin = _fechas(plan)
    coords = [b["lon_oeste"], b["lat_sur"], b["lon_este"], b["lat_norte"]]
    plantilla = PLANTILLAS[analisis]
    codigo = (plantilla
              .replace("__ZONA__", zona)
              .replace("__COORDS__", str(coords))
              .replace("__FINI__", f_inicio)
              .replace("__FFIN__", f_fin)
              .replace("__ESCALA__", str(escala))
              .replace("__DIAS__", str(plan.get("dias") or 15)))
    return codigo + _bloque_descarga(
        analisis, zona, escala, VARIABLE_SALIDA[analisis])


def probar_generador():
    """Auto-test: genera un script para cada plantilla (sin GEE real)."""
    import json
    planes = [
        {"analisis": "ndvi", "zona": "lima"},
        {"analisis": "lluvia", "zona": "ucayali"},
        {"analisis": "humedad", "zona": "lima"},
        {"analisis": "ndwi", "zona": "iquitos"},
        {"analisis": "lst", "zona": "arequipa"},
        {"analisis": "evi", "zona": "cusco"},
        {"analisis": "ndvi", "zona": "lima", "dias": 7},
    ]
    for p in planes:
        print("=" * 20, p["analisis"], p["zona"], p.get("dias", "-"))
        print(generar_codigo_gee(p)[:220], "...\n")
    return True


if __name__ == "__main__":
    probar_generador()