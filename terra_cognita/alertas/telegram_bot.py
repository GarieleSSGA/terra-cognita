"""Cliente Telegram reutilizado de la infra base (envío de alertas y
reportes). Solo dependencias estándar: requests."""
import time

import requests

API = "https://api.telegram.org/bot{token}/"
TIMEOUT = 30
REINTENTOS = 3
ESPERA = 5


def _llamar(token, metodo, **kwargs):
    url = API.format(token=token) + metodo
    for intento in range(REINTENTOS):
        try:
            r = requests.post(url, timeout=TIMEOUT, **kwargs)
            if r.status_code == 200 and r.json().get("ok"):
                return r.json().get("result")
            ultimo = r.json().get("description", f"HTTP {r.status_code}")
        except requests.RequestException as exc:
            ultimo = str(exc)
        if intento < REINTENTOS - 1:
            time.sleep(ESPERA * (intento + 1))
    raise RuntimeError(f"Telegram {metodo} fallo: {ultimo}")


def enviar_mensaje(token, chat_id, texto, silencioso=False):
    return _llamar(token, "sendMessage", data={
        "chat_id": chat_id, "text": texto,
        "disable_notification": silencioso})


def enviar_foto(token, chat_id, ruta_png, caption="", silencioso=False):
    with open(ruta_png, "rb") as f:
        return _llamar(token, "sendPhoto",
                       data={"chat_id": chat_id, "caption": caption,
                             "disable_notification": silencioso},
                       files={"photo": f})


def enviar_documento(token, chat_id, ruta, caption="", silencioso=False):
    with open(ruta, "rb") as f:
        return _llamar(token, "sendDocument",
                       data={"chat_id": chat_id, "caption": caption,
                             "disable_notification": silencioso},
                       files={"document": f})