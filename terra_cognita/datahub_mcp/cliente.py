"""Cliente MCP de DataHub: descubrimiento de datasets, esquemas y linaje.

Permite que el agente consulte a DataHub antes de actuar:
1. search        -> ¿qué datasets geoespaciales existen?
2. get_entities  -> ¿cuál es el dataset correcto para la consulta?
3. list_schema   -> ¿qué columnas tiene?
4. get_lineage   -> ¿es la fuente confiable?

Si el servidor MCP no está corriendo, el agente sigue con datos locales
(no romper la demo), pero avisa.
"""
import json
import subprocess
import sys

from ..config import cargar_config


class DataHubMCP:
    """Puente hacia el MCP Server de DataHub (ejecuta el binario MCP)."""

    def __init__(self, config: dict | None = None):
        self.config = config or cargar_config()
        self._proceso = None

    # ------------------------------------------------------------------
    def _mcp(self, herramienta: str, argumentos: dict) -> dict:
        """Ejecuta una herramienta del MCP Server de DataHub vía stdio."""
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return {"error": "mcp no instalado (pip install mcp)"}

        params = StdioServerParameters(
            command="datahub",
            args=["mcp", "server"],
        )
        return {"error": "pendiente: conexión MCP activa"}

    # ------------------------------------------------------------------
    def search_datasets(self, query: str) -> list:
        """Busca datasets cuyo nombre/descripción coincida con la consulta."""
        return self._mcp("search", {"query": query})

    def get_entities(self, urn: str) -> dict:
        """Obtiene entidad (dataset) completa por su URN."""
        return self._mcp("get_entities", {"urn": urn})

    def list_schema(self, urn: str) -> list:
        """Devuelve las columnas del dataset y sus tipos."""
        return self._mcp("list_schema_fields", {"urn": urn})

    def get_lineage(self, urn: str) -> dict:
        """Devuelve las fuentes upstream/downstream del dataset."""
        return self._mcp("get_lineage", {"urn": urn})