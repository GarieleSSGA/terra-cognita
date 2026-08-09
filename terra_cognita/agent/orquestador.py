"""Orquestador: el 'cerebro' de Terra Cognita.

Flujo:
1. Ollama interpreta la consulta en lenguaje natural (intención, zona, análisis).
2. El agente pregunta a DataHub (MCP) si ya hay datasets del tema (contexto).
3. Ejecuta el análisis sobre la fuente configurada (sintético o GEE).
4. Escribe el resultado de vuelta a DataHub.
5. Si hay riesgo -> alerta por Telegram.
"""
import json

from ..config import cargar_config
from ..datahub_mcp.cliente import DataHubMCP
from ..datahub_write.catalogar import escribir_resultado
from ..geo.analisis import evaluar_ndvi, evaluar_lluvia, resumen_a_json
from ..geo.datos import FuenteData


class Orquestador:
    def __init__(self, config: dict | None = None):
        self.config = config or cargar_config()
        self.datahub = DataHubMCP(self.config)
        self.fuente = FuenteData(
            fuente=self.config["gee"]["fuente_default"],
            proyecto_gee=self.config["gee"].get("project_id", ""),
        )

    # ------------------------------------------------------------------
    def interpretar(self, consulta: str) -> dict:
        """Pide a Ollama extraer: análisis, zona, y datos necesarios."""
        try:
            import ollama
            cliente = ollama.Client(host=self.config["ollama"]["base_url"])
            respuesta = cliente.chat(
                model=self.config["ollama"]["model"],
                messages=[{
                    "role": "system",
                    "content": (
                        "Eres el planificador de Terra Cognita. Devuelve SOLO JSON: "
                        '{"analisis": "ndvi"|"lluvia"|"estadisticas", "zona": "<nombre>", '
                        '"datos_necesarios": ["<dataset o indice>"]}. '
                        "Si la consulta menciona vegetacion, sequia o NDVI -> ndvi. "
                        "Lluvia, inundacion o precipitacion -> lluvia."
                    ),
                }, {
                    "role": "user",
                    "content": consulta,
                }],
            )
            texto = respuesta["message"]["content"]
            inicio, fin = texto.find("{"), texto.rfind("}")
            return json.loads(texto[inicio:fin + 1])
        except Exception as exc:
            return self._interpretar_fallback(consulta, str(exc))

    def _interpretar_fallback(self, consulta: str, error: str) -> dict:
        """Si Ollama no responde, la demo sigue con heurística simple."""
        consulta = consulta.lower()
        if any(p in consulta for p in ("lluvia", "inundacion", "precipitacion", "humedad")):
            analisis = "lluvia"
        else:
            analisis = "ndvi"
        return {"analisis": analisis, "zona": "lima",
                "datos_necesarios": [analisis], "ollama_error": error}

    # ------------------------------------------------------------------
    def buscar_contexto_datahub(self, tema: str) -> dict:
        """Consulta a DataHub qué sabe del tema (contexto = no alucinar).

        Devuelve los datasets encontrados o, si el MCP no está disponible,
        un aviso claro — el flujo continúa con datos locales.
        """
        return self.datahub.search_datasets(tema)

    # ------------------------------------------------------------------
    def ejecutar(self, consulta: str) -> dict:
        plan = self.interpretar(consulta)
        contexto = self.buscar_contexto_datahub(plan.get("analisis", ""))
        zona = plan.get("zona", "zona_generica")

        if plan.get("analisis") == "lluvia":
            ruta = self.fuente.lluvia(zona)
            resultado = evaluar_lluvia(ruta, self.config["alertas"]["umbral_lluvia_mm"])
        else:
            ruta = self.fuente.ndvi(zona)
            resultado = evaluar_ndvi(ruta, self.config["alertas"]["umbral_ndvi"])

        resultado["raster"] = ruta
        resultado["resumen"] = resumen_a_json(ruta, tipo=plan.get("analisis", "ndvi"))
        resultado["zona"] = zona
        resultado["plan"] = plan
        resultado["contexto_datahub"] = contexto

        return resultado

    # ------------------------------------------------------------------
    def cerrar_ciclo(self, resultado: dict, consulta: str) -> dict:
        """Escribe el resultado en DataHub y genera alerta si aplica."""
        urn = escribir_resultado(resultado, consulta)
        resultado["urn_datahub"] = urn

        alerta = None
        if "ALERTA" in str(resultado.get("estado", "")):
            alerta = self._alertar(resultado)
        resultado["alerta"] = alerta
        return resultado

    def _alertar(self, resultado: dict) -> dict:
        from ..alertas.telegram_bot import enviar_mensaje
        cfg = self.config["alertas"]
        if not cfg.get("telegram_token") or not cfg.get("chat_id"):
            return {"aviso": "TELEGRAM_TOKEN/CHAT_ID no configurados; alerta solo en log."}
        texto = (f"[Terra Cognita] {resultado['estado']}\n"
                 f"Zona: {resultado.get('zona')}\n{resultado}")
        return enviar_mensaje(cfg["telegram_token"], cfg["chat_id"], texto)