"""Cliente MCP de DataHub (modo HTTP, servidor persistente).

Arquitectura:
- `mcp-server-datahub` corre UNA VEZ en modo HTTP (servidor persistente).
- El agente hace llamadas HTTP (~1-3 s) en vez de levantar el proceso
  por cada consulta (37 s con stdio).

Herramientas disponibles (DataHub OSS):
- search                    -> descubre datasets por lenguaje natural
- get_entities              -> entidad completa por URN
- list_schema_fields        -> columnas de un dataset
- get_lineage               -> origen/confianza de los datos
- get_lineage_paths_between -> caminos de linaje entre dos URNs

Si el servidor no responde, se intenta arrancar una vez. Si no hay DataHub
levantado, el agente continúa con datos locales (la demo no se rompe).
"""
import asyncio
import os
import subprocess
import time
from pathlib import Path

import requests
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from ..config import cargar_config

PUERTO_MCP = 8000
URL_MCP = f"http://localhost:{PUERTO_MCP}/mcp"
HEALTH = f"http://localhost:{PUERTO_MCP}/health"


def _binario_mcp() -> str:
    venv_scripts = Path(__file__).resolve().parents[2] / ".venv" / "Scripts"
    for cand in (venv_scripts / "mcp-server-datahub.exe",
                 venv_scripts / "mcp-server-datahub"):
        if cand.exists():
            return str(cand)
    return "mcp-server-datahub"


def _servidor_vivo() -> bool:
    try:
        return requests.get(HEALTH, timeout=3).status_code == 200
    except requests.RequestException:
        return False


def _levantar_servidor(config: dict) -> None:
    """Arranca el servidor MCP en modo HTTP con las credenciales de DataHub."""
    env = dict(os.environ)
    for var in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
        env.pop(var, None)
    gms = config["datahub"]["gms_url"]
    protocolo, resto = gms.split("://", 1)
    host, _, puerto = resto.rpartition(":")
    env["DATAHUB_GMS_PROTOCOL"] = protocolo
    env["DATAHUB_GMS_HOST"] = host
    env["DATAHUB_GMS_PORT"] = puerto or "8080"
    if config["datahub"].get("token"):
        env["DATAHUB_GMS_TOKEN"] = config["datahub"]["token"]
    DEVNULL = open(os.devnull, "w")
    subprocess.Popen(
        [_binario_mcp(), "--transport", "http"],
        env=env, stdout=DEVNULL, stderr=DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def _esperar_servidor(tope_s: float = 90) -> bool:
    """Espera hasta que el servidor MCP responda."""
    fin = time.time() + tope_s
    while time.time() < fin:
        if _servidor_vivo():
            return True
        time.sleep(2)
    return False


class DataHubMCP:
    """Puente HTTP hacia el MCP Server de DataHub."""

    def __init__(self, config: dict | None = None):
        self.config = config or cargar_config()
        self.disponible = None

    # ------------------------------------------------------------------
    def _llamar(self, nombre_tool: str, argumentos: dict) -> dict:
        async def _correr():
            async with streamablehttp_client(URL_MCP) as (lectura, escritura, _):
                async with ClientSession(lectura, escritura) as sesion:
                    await sesion.initialize()
                    res = await sesion.call_tool(nombre_tool, argumentos)
                    return _contenido_plano(res)

        try:
            return asyncio.run(_correr())
        except Exception as exc:
            return {"error": f"MCP DataHub: {exc}"}

    # ------------------------------------------------------------------
    def _garantizar_servidor(self) -> bool:
        """Devuelve True si el servidor MCP está operativo (levanta si falta)."""
        if self.disponible is not None:
            return self.disponible
        if not _servidor_vivo():
            _levantar_servidor(self.config)
        self.disponible = _esperar_servidor()
        return self.disponible

    # ------------------------------------------------------------------
    def search_datasets(self, query: str) -> dict:
        if not self._garantizar_servidor():
            return {"aviso": "MCP server no disponible (¿DataHub apagado?)"}
        return self._llamar("search", {"query": query})

    def get_entities(self, urn: str) -> dict:
        if not self._garantizar_servidor():
            return {"aviso": "MCP server no disponible"}
        return self._llamar("get_entities", {"urn": urn})

    def listar_schema(self, urn: str) -> dict:
        if not self._garantizar_servidor():
            return {"aviso": "MCP server no disponible"}
        return self._llamar("list_schema_fields", {"urn": urn})

    def get_lineage(self, urn: str) -> dict:
        if not self._garantizar_servidor():
            return {"aviso": "MCP server no disponible"}
        return self._llamar("get_lineage", {"urn": urn})


def _contenido_plano(resultado) -> dict:
    """Convierte la respuesta MCP en un dict simple."""
    piezas = []
    for item in getattr(resultado, "content", []) or []:
        texto = getattr(item, "text", None)
        if texto:
            piezas.append(texto)
        elif hasattr(item, "structuredContent") and item.structuredContent:
            piezas.append(item.structuredContent)
    return {"content": piezas}