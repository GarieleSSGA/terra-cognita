"""Prueba de conexión MCP -> DataHub: lista herramientas y ejecuta una búsqueda."""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

COMANDO = str(ROOT / ".venv" / "Scripts" / "mcp-server-datahub.exe")


async def probar():
    env = {
        **os.environ,
        "PROJ_LIB": "",
        "GDAL_DATA": "",
        "DATAHUB_GMS_HOST": "localhost",
        "DATAHUB_GMS_PORT": "8080",
        "DATAHUB_GMS_PROTOCOL": "http",
    }
    params = StdioServerParameters(
        command=COMANDO,
        args=[],
        env=env,
    )
    async with stdio_client(params) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()
            herramientas = await sesion.list_tools()
            print(f"== {len(herramientas.tools)} herramientas MCP disponibles ==")
            nombres = sorted(t.name for t in herramientas.tools)
            for n in nombres:
                print(f"  - {n}")

            print("\n== Prueba: buscar 'dataset' ==")
            try:
                res = await sesion.call_tool("search", {"query": "dataset"})
                for item in res.content:
                    print(item.text[:500] if hasattr(item, "text") else item)
            except Exception as exc:
                print(f"ERROR buscar: {exc}")

            print("\n== Prueba: get_me (usuario autenticado) ==")
            try:
                res = await sesion.call_tool("get_me", {})
                for item in res.content:
                    print(item.text[:300] if hasattr(item, "text") else item)
            except Exception as exc:
                print(f"ERROR get_me: {exc}")


if __name__ == "__main__":
    asyncio.run(probar())