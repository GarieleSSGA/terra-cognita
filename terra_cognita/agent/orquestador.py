"""Orquestador: el 'cerebro' de Terra Cognita.

Flujo:
1. Ollama interpreta la consulta en lenguaje natural (intención, zona, análisis).
2. El agente pregunta a DataHub (MCP) si ya hay datasets del tema (contexto).
3. Ejecuta el análisis sobre la fuente configurada (sintético o GEE).
4. Escribe el resultado de vuelta a DataHub.
5. Si hay riesgo -> alerta por Telegram.

Modos de análisis:
- snapshot: un solo raster (ndvi/lluvia/estadisticas) de la fecha actual.
- tendencia: si la consulta pide "ultimos N dias"/"evolucion", genera la serie
  temporal (N rasters) y mide el cambio (ver geo/analisis.py::evaluar_tendencia).

Nota de robustez: la llamada a Ollama tiene timeout (config `ollama.timeout_s`);
si el modelo tarda mas (RAM justa + Docker), se usa la heuristica local y la
demo nunca se queda "colgada" en silencio.
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturoTimeout

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
        """Cadena de interpretación: Ollama local -> LLM API (respaldo) -> heurística.

        - Ollama se intenta primero (modelo local, privado).
        - Si no responde o tarda (RAM justa con Docker), se prueba la API
          LLM configurada en `llm_api` (OpenAI-compatible; p.ej. DeepSeek).
        - Si tampoco, heurística local: la demo NUNCA se cuelga.
        """
        plan = self._interpretar_ollama(consulta)
        if "ollama_error" not in plan:
            return plan

        plan_api = self._interpretar_llm_api(consulta)
        if plan_api is not None:
            return plan_api

        return self._interpretar_fallback(consulta, plan.get("ollama_error", ""))

    # ------------------------------------------------------------------
    def _interpretar_ollama(self, consulta: str) -> dict:
        try:
            import ollama
            cliente = ollama.Client(host=self.config["ollama"]["base_url"])
            timeout = float(self.config["ollama"].get("timeout_s", 90))

            def _llamar():
                return cliente.chat(
                    model=self.config["ollama"]["model"],
                    messages=self._mensajes_planificador(consulta),
                )

            with ThreadPoolExecutor(max_workers=1) as pool:
                respuesta = pool.submit(_llamar).result(timeout=timeout)
            texto = respuesta["message"]["content"]
            inicio, fin = texto.find("{"), texto.rfind("}")
            return json.loads(texto[inicio:fin + 1])
        except FuturoTimeout:
            return self._interpretar_fallback(
                consulta, f"Ollama excedio {timeout:.0f}s de timeout (RAM justa?)")
        except Exception as exc:
            return self._interpretar_fallback(consulta, str(exc))

    # ------------------------------------------------------------------
    def _interpretar_llm_api(self, consulta: str) -> dict | None:
        """Prueba la API LLM de respaldo (OpenAI-compatible) si está configurada."""
        llm = self.config.get("llm_api") or {}
        base_url = (llm.get("base_url") or "").strip()
        api_key = (llm.get("api_key") or "").strip()
        if not base_url or not api_key:
            return None

        import requests
        url = base_url.rstrip("/") + "/chat/completions"
        cuerpo = {
            "model": llm.get("model", "deepseek-chat"),
            "messages": self._mensajes_planificador(consulta),
            "temperature": 0.1,
            "max_tokens": 200,
        }
        try:
            r = requests.post(
                url, json=cuerpo,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=float(llm.get("timeout_s", 60)))
            r.raise_for_status()
            texto = r.json()["choices"][0]["message"]["content"]
            inicio, fin = texto.find("{"), texto.rfind("}")
            plan = json.loads(texto[inicio:fin + 1])
            plan["via"] = "llm_api"
            return plan
        except Exception as exc:
            return None

    @staticmethod
    def _mensajes_planificador(consulta: str) -> list:
        return [{
            "role": "system",
            "content": (
                "Eres el planificador de Terra Cognita. Devuelve SOLO JSON: "
                '{"analisis": "ndvi"|"lluvia"|"humedad"|"ndwi"|"lst"|"evi"|'
                '"estadisticas", "zona": "<nombre>", '
                '"dias": <numero o null>, "datos_necesarios": ["<dataset o indice>"]}. '
                "Reglas: vegetacion/sequia/NDVI -> ndvi; lluvia/inundacion/"
                "precipitacion -> lluvia; humedad de suelo -> humedad; "
                "agua/cuerpos de agua/riego -> ndwi; temperatura/calor/isoterma "
                "-> lst; vigor vegetal -> evi. Si piden 'ultimos N dias', "
                "'evolucion', 'tendencia' -> rellena 'dias' con N (default 7). "
                "Si es puntual -> 'dias': null."
            ),
        }, {
            "role": "user",
            "content": consulta,
        }]

    def _interpretar_fallback(self, consulta: str, error: str) -> dict:
        """Si Ollama no responde, la demo sigue con heurística simple."""
        consulta = consulta.lower()
        if any(p in consulta for p in ("humedad", "suelo", "seco", "riego")):
            analisis = "humedad"
        elif any(p in consulta for p in ("agua", "inundacion", "riachuelo", "lago", "rio ")):
            analisis = "ndwi"
        elif any(p in consulta for p in ("temperatura", "calor", "isoterma", "ict")):
            analisis = "lst"
        elif any(p in consulta for p in ("lluvia", "inundacion", "precipitacion", "humedad")):
            analisis = "lluvia"
        else:
            analisis = "ndvi"
        dias = None
        m = re.search(r"ultimos?[^\d]{0,12}(\d{1,2})\s*dias?", consulta)
        if m:
            dias = min(int(m.group(1)), 30)
        elif any(p in consulta for p in ("evolucion", "tendencia", "serie", "ultimas")):
            dias = 7
        return {"analisis": analisis, "zona": "lima",
                "datos_necesarios": [analisis], "dias": dias,
                "ollama_error": error}

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
        dias = plan.get("dias")

        if plan.get("analisis") == "lluvia":
            ruta = self.fuente.lluvia(zona)
            resultado = evaluar_lluvia(ruta, self.config["alertas"]["umbral_lluvia_mm"])
            resultado["raster"] = ruta
            resultado["resumen"] = resumen_a_json(ruta, tipo="lluvia")
        elif plan.get("analisis") in ("humedad", "humedad_suelo"):
            from ..geo.analisis import evaluar_humedad
            ruta = self.fuente.humedad(zona)
            resultado = evaluar_humedad(ruta, self.config["alertas"].get("umbral_humedad", 30))
            resultado["raster"] = ruta
            resultado["resumen"] = resumen_a_json(ruta, tipo="humedad")
        elif dias and int(dias) > 1:
            from ..geo.analisis import evaluar_tendencia
            from ..geo.sinteticos import generar_serie_ndvi
            n = min(int(dias), 30)
            rutas = generar_serie_ndvi("data/series", f"ndvi_{zona}", n)
            resultado = evaluar_tendencia(rutas, self.config["alertas"]["umbral_ndvi"])
            resultado["raster"] = rutas[-1] if rutas else ""
            resultado["serie_rasters"] = rutas
            resultado["tipo_analisis"] = "tendencia"
        else:
            ruta = self.fuente.ndvi(zona)
            resultado = evaluar_ndvi(ruta, self.config["alertas"]["umbral_ndvi"])
            resultado["resumen"] = resumen_a_json(ruta, tipo="ndvi")
            resultado["tipo_analisis"] = "snapshot"

        resultado["zona"] = zona
        resultado["plan"] = plan
        resultado["contexto_datahub"] = contexto
        resultado["codigo_gee"] = self._generar_codigo_gee(plan)

        return resultado

    def _generar_codigo_gee(self, plan: dict) -> str:
        """Genera el script GEE ad-hoc para el plan (si el analisis lo soporta)."""
        try:
            from ..geo.gee_codegen import generar_codigo_gee
            return generar_codigo_gee(plan)
        except Exception as exc:
            return f"// No se pudo generar codigo GEE: {exc}"

    # ------------------------------------------------------------------
    def cerrar_ciclo(self, resultado: dict, consulta: str) -> dict:
        """Escribe el resultado en DataHub y genera alerta si aplica.

        - Analisis puntual -> dataset con linaje al raster fuente.
        - Tendencia -> serie de datasets por fecha + resumen con linaje múltiple
          (DataHub guarda la memoria temporal del agente).
        """
        if resultado.get("tipo_analisis") == "tendencia":
            from ..datahub_write.catalogar import escribir_serie
            urn = escribir_serie(resultado, consulta)
        else:
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