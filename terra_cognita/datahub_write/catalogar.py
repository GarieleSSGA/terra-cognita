"""Write-back: registra los resultados del análisis en DataHub.

Cierra el ciclo del agente: cada análisis crea en el grafo un dataset con:
- datasetProperties  -> quién (agente), qué, cuándo, métricas del análisis
- upstreamLineage    -> de qué dataset fuente se alimentó (linaje)

Estrategia resiliente: si el GMS no responde, el resultado se guarda
localmente (data/resultados_catalogados/) y la demo no se rompe.
"""
import uuid
from pathlib import Path

from ..config import cargar_config

PLATAFORMA = "terraCognita"


def _urn_dataset(nombre: str) -> str:
    return f"urn:li:dataset:(urn:li:dataPlatform:{PLATAFORMA},{nombre},PROD)"


def _emitter():
    from datahub.emitter.rest_emitter import DatahubRestEmitter
    cfg = cargar_config()
    return DatahubRestEmitter(gms_server=cfg["datahub"]["gms_url"])


def _emit_mce(urn: str, aspectos: list) -> None:
    from datahub.metadata.schema_classes import (
        DatasetSnapshotClass, MetadataChangeEventClass)
    snapshot = DatasetSnapshotClass(urn=urn, aspects=aspectos)
    _emitter().emit_mce(MetadataChangeEventClass(proposedSnapshot=snapshot))


def _props(resultado: dict, consulta: str) -> dict:
    """Propiedades: consulta, zona, estado, análisis, métricas, raster."""
    return {
        "consulta": consulta,
        "zona": resultado.get("zona"),
        "estado": resultado.get("estado"),
        "analisis": resultado.get("plan", {}).get("analisis"),
        "metricas": resultado.get("resumen", {}),
        "raster": resultado.get("raster"),
    }


def asegurar_raster_fuente(zona: str, ruta_raster: str) -> str:
    """Crea (si no existe) el dataset fuente: el raster analizado."""
    from datahub.metadata.schema_classes import DatasetPropertiesClass
    urn = _urn_dataset(f"raster_{zona}_sintetico")
    aspecto = DatasetPropertiesClass(
        name=f"raster_{zona}",
        qualifiedName=urn,
        description=(
            f"Raster fuente del analisis en {zona} ({ruta_raster}). "
            "Generado por Terra Cognita para la demo rapida."
        ),
    )
    _emit_mce(urn, [aspecto])
    return urn


def escribir_resultado(resultado: dict, consulta: str) -> str:
    """Crea el dataset del análisis + linaje hacia el raster fuente."""
    from datahub.metadata.schema_classes import (
        DatasetPropertiesClass, UpstreamClass, UpstreamLineageClass)

    props = _props(resultado, consulta)
    zona = resultado.get("zona", "zona")
    urn = _urn_dataset(f"analisis_{zona}_{uuid.uuid4().hex[:6]}")

    try:
        urn_fuente = asegurar_raster_fuente(zona, str(resultado.get("raster", "")))
        aspecto_props = DatasetPropertiesClass(
            name=f"analisis_{zona}",
            qualifiedName=urn,
            description=(
                f"Resultado del analisis {resultado.get('estado')} para "
                f"{zona}. Consulta: {consulta}. "
                f"Metricas: {resumen_json(props)}"
            ),
        )
        aspecto_lineage = UpstreamLineageClass(
            upstreams=[UpstreamClass(dataset=urn_fuente, type="TRANSFORMED")],
        )
        _emit_mce(urn, [aspecto_props, aspecto_lineage])
        return urn
    except Exception as exc:
        ruta = Path("data/resultados_catalogados")
        ruta.mkdir(parents=True, exist_ok=True)
        archivo = ruta / f"{urn.split(',')[1]}.json"
        archivo.write_text(
            _json_utf8({"urn": urn, "propiedades": props}),
            encoding="utf-8")
        return f"{urn} (fallback local: {exc})"


def escribir_serie(resultado: dict, consulta: str) -> str:
    """Cataloga una serie temporal: un dataset por fecha + resumen con linaje.

    Cada raster de la serie (`serie_rasters`) se registra como dataset
    `raster_<zona>_<fecha>` y el dataset resumen `analisis_<zona>_tendencia`
    apunta (upstreamLineage) a todos ellos: el grafo muestra la memoria
    temporal completa y otros agentes la pueden heredar.
    """
    from datahub.metadata.schema_classes import (
        DatasetPropertiesClass, UpstreamClass, UpstreamLineageClass)

    serie = resultado.get("serie", [])
    rutas = resultado.get("serie_rasters", [])
    zona = resultado.get("zona", "zona")
    analisis = resultado.get("plan", {}).get("analisis", "ndvi")

    urn_resumen = _urn_dataset(f"analisis_{zona}_tendencia_{uuid.uuid4().hex[:6]}")
    upstreams = []

    try:
        for item, ruta in zip(serie, rutas):
            fecha = item.get("fecha", "?")
            urn_dia = _urn_dataset(f"raster_{zona}_{fecha}")
            _emit_mce(urn_dia, [DatasetPropertiesClass(
                name=f"raster_{zona}_{fecha}",
                qualifiedName=urn_dia,
                description=(
                    f"Raster {analisis} de {zona} del {fecha}. "
                    f"pct_bajo={item.get('pct_bajo')}%, "
                    f"media={item.get('media_ndvi')}. Fuente: {ruta}"
                ),
            )])
            upstreams.append(UpstreamClass(dataset=urn_dia, type="TRANSFORMED"))

        desc = (f"Serie temporal {analisis} de {zona} "
                f"({resultado.get('dias')} dias, "
                f"{serie[0]['fecha']} -> {serie[-1]['fecha']}): "
                f"{resultado.get('resumen', '')}")
        _emit_mce(urn_resumen, [
            DatasetPropertiesClass(
                name=f"analisis_{zona}_tendencia",
                qualifiedName=urn_resumen,
                description=desc,
            ),
            UpstreamLineageClass(upstreams=upstreams),
        ])
        return urn_resumen
    except Exception as exc:
        ruta = Path("data/resultados_catalogados")
        ruta.mkdir(parents=True, exist_ok=True)
        archivo = ruta / f"{urn_resumen.split(',')[1]}.json"
        archivo.write_text(
            _json_utf8({"urn": urn_resumen, "tipo": "serie",
                        "propiedades": _props(resultado, consulta)}),
            encoding="utf-8")
        return f"{urn_resumen} (fallback local: {exc})"


def resumen_json(props: dict) -> str:
    import json
    return json.dumps(props, ensure_ascii=False, default=str)


def _json_utf8(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)