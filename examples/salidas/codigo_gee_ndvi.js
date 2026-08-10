// TERRA COGNITA :: Vegetacion (NDVI) â€” Sentinel-2
// Generado automaticamente para: Lima
// Analisis: NDVI 7 dias, escala 250m
var zona = ee.Geometry.Rectangle([-77.06, -12.07, -77.04, -12.05]);
var fechas = ee.DateRange('2026-08-03', '2026-08-10');
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(zona).filterDate(fechas)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30));
var ndvi = s2.median().normalizedDifference(['B8', 'B4']).rename('ndvi');
var paleta = ['#8B0000','#FFD700','#228B22'];   // seco -> vegetado
Map.centerObject(zona, 11);
Map.addLayer(ndvi.clip(zona), {min: -0.2, max: 0.8, palette: paleta}, 'NDVI Lima');
Export.image.toDrive({image: ndvi.clip(zona), description: 'TC_ndvi_Lima',
  folder: 'terra_cognita', scale: 250, region: zona, maxPixels: 1e9});
print('Media NDVI:', ndvi.clip(zona).reduceRegion(
  ee.Reducer.mean(), zona, 250).get('ndvi'));
// ===== DESCARGA AUTOMATICA (Lima, bbox pequeno ~2 km) =====
// 1) Enlace directo GEOTIFF (requiere cuenta autenticada):
print(ndvi.clip(zona).getDownloadURL({scale: 250, region: zona, format: 'GEO_TIFF'}));
// 2) Guardar en Google Drive (tarea asincrona en la pestana Tasks):
// Export.image.toDrive({image: ndvi.clip(zona), description: 'TC_ndvi_Lima', folder: 'terra_cognita', scale: 250, region: zona, maxPixels: 1e9});
