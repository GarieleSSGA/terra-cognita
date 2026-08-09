"""Terra Cognita - agente local de inteligencia espacial.

En Windows, las variables PROJ_LIB/GDAL_DATA heredadas de instalaciones
como PostgreSQL rompen rasterio (no encuentran proj.db). Las quitamos
al importar el paquete, antes de que rasterio se inicialice.
"""
import os

for _var_proj in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    os.environ.pop(_var_proj, None)

__version__ = "0.1.0"