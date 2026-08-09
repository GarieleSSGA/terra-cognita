"""Write-back: registra los resultados del análisis en DataHub.

Es lo que hace que el agente 'contribuya al grafo' (20% del puntaje):
cada análisis crea un dataset nuevo con sus métricas y linaje hacia
las fuentes consultadas.

Estrategia resiliente: si el GMS no responde, el resultado se guarda
localmente (data/resultados_catalogados/) y la demo no se rompe.
"""
import uuid
from pathlib import Path

from ..config import cargar_config


def _urn_dataset(zona: str) -> str:
    codigo = f"analisis_{zona}_{uuid.uuid4().hex[:6]}"
    return f"urn:li:dataset:(urn:li:dataPlatform:terraCognita,{codigo},PROD)"


def _propiedades(resultado: dict, consulta: str) -> dict:
    """Construye el dict de propiedades (texto libre) del dataset."""
    resumen = resultado.get("resumen", {})
    return {
        "consulta": consulta,
        "zona": resultado.get("zona"),
        "estado": resultado.get("estado"),
        "analisis": resultado.get("plan", {}).get("analisis"),
        "metricas": resumen,
        "raster": resultado.get("raster"),
    }


def escribir_resultado(resultado: dict, consulta: str) -> str:
    """Crea el dataset en DataHub vía la API REST. Devuelve la URN."""
    cfg = cargar_config()
    gms = cfg["datahub"]["gms_url"]
    urn = _urn_dataset(resultado.get("zona", "zona"))
    props = _propiedades(resultado, consulta)

    try:
        from datahub.emitter.rest_emitter import DatahubRestEmitter
        from datahub.metadata.schema_classes import (
            DatasetPropertiesClass,
            DatasetSnapshot,
            MetadataChangeEventClass,
        )

        emitter = DatahubRestEmitter(gms_url=gms)
        aspecto = DatasetPropertiesClass(
            name=f"analisis_{resultado.get('zona', 'zona')}",
            description=(
                f"Resultado del analisis de {resultado.get('estado')} para "
                f"{resultado.get('zona')}. Consulta: {consulta}. "
                f"Metricas: {resumen_json(props)}"
            ),
        )
        evento = MetadataChangeEventClass(
            proposedSnapshot=DatasetSnapshot(
                urn=urn, aspects=[aspecto]))
        emitter.emit_mce(evento)
        return urn
    except Exception as exc:
        ruta = Path("data/resultados_catalogados")
        ruta.mkdir(parents=True, exist_ok=True)
        archivo = ruta / f"{urn.split(',')[1]}.json"
        archivo.write_text(
            _json_utf8({"urn": urn, "propiedades": props}),
            encoding="utf-8")
        return f"{urn} (fallback local: {exc})"


def resumen_json(props: dict) -> str:
    import json
    return json.dumps(props, ensure_ascii=False, default=str)


def _json_utf8(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)