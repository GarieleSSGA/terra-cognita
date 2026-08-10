"""Configuración central de Terra Cognita.

Carga config/config.yaml y permite override con variables de entorno
(TELEGRAM_TOKEN, CHAT_ID, FUENTE_DATOS, etc.).
"""
import os
from pathlib import Path

import yaml

RUTA_CONFIG = Path(__file__).resolve().parents[1] / "config" / "config.yaml"


def cargar_config() -> dict:
    if RUTA_CONFIG.exists():
        with open(RUTA_CONFIG, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = {}

    def _env(clave, ruta, defecto=""):
        return os.environ.get(clave, ruta or defecto)

    cfg.setdefault("datahub", {})
    cfg["datahub"].setdefault("frontend_url", "http://localhost:9002")
    cfg["datahub"].setdefault("gms_url", "http://localhost:8080")

    cfg.setdefault("ollama", {})
    cfg["ollama"].setdefault("model", _env("OLLAMA_MODEL", cfg["ollama"].get("model"), "qwen3:4b"))
    cfg["ollama"].setdefault("base_url", "http://localhost:11434")
    cfg["ollama"].setdefault("timeout_s", 90)

    cfg.setdefault("llm_api", {})
    cfg["llm_api"]["base_url"] = _env("LLM_API_BASE", cfg["llm_api"].get("base_url"))
    cfg["llm_api"]["model"] = _env("LLM_API_MODEL", cfg["llm_api"].get("model"), "deepseek-chat")
    cfg["llm_api"]["api_key"] = _env("LLM_API_KEY", cfg["llm_api"].get("api_key"))
    cfg["llm_api"].setdefault("timeout_s", 60)

    cfg.setdefault("gee", {})
    cfg["gee"].setdefault("fuente_default", "sintetico")

    cfg.setdefault("alertas", {})
    cfg["alertas"]["telegram_token"] = _env("TELEGRAM_TOKEN", cfg["alertas"].get("telegram_token"))
    cfg["alertas"]["chat_id"] = _env("CHAT_ID", cfg["alertas"].get("chat_id"))
    cfg["alertas"].setdefault("umbral_ndvi", 0.3)
    cfg["alertas"].setdefault("umbral_lluvia_mm", 50)
    cfg["alertas"].setdefault("umbral_humedad", 30)

    cfg.setdefault("dashboard", {})
    cfg["dashboard"].setdefault("host", "localhost")
    cfg["dashboard"].setdefault("puerto", 8501)
    return cfg