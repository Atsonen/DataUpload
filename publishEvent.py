import json
from typing import Any, Dict, Sequence

import paho.mqtt.client as mqtt
import requests

from payload_logger import log_payload

HOST = "https://script.google.com"
# Valitse tähän se oikea oman Apps Script -julkaisusi ID:
SCRIPT_ID = "AKfycbyjEthTZuGTR_fUB1KQ1X0mZiE_RSh5m5pn-CAE6IcsrORtlzJBDqEPte2JEDkV7-c_"
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"

MQTT_BROKER = "192.168.1.51"
MQTT_PORT = 1883
MQTT_TOPIC = "Sensors/EventLogger"


def _pick_int(values: Sequence[Any], index: int) -> int:
    """Return an integer from ``values`` at ``index`` when possible."""

    if index >= len(values):
        return 0

    value = values[index]
    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    if not text:
        return 0
    # Poista ympäriltä mahdolliset aaltosulut/klammerit, jotta esim.
    # "{4}" ja "4}" tulkitaan oikein numeroksi.
    text = text.strip("{}[]()")
    if not text:
        return 0
    try:
        return int(text, 10)
    except ValueError:
        return 0


def _build_status_fields(values: Sequence[Any]) -> Dict[str, int]:
    """Create a summary payload for the MQTT acknowledgement message."""

    return {
        "Done": _pick_int(values, 9),
        "Spare1": _pick_int(values, 1),
        "Spare2": _pick_int(values, 2),
        "Status": _pick_int(values, 3),
    }


def _publish_acknowledgement(message: Dict[str, int]) -> None:
    """Publish an acknowledgement packet to the MQTT broker."""

    client = mqtt.Client()
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        payload = json.dumps(message, ensure_ascii=False)
        info = client.publish(MQTT_TOPIC, payload, qos=1, retain=False)
        info.wait_for_publish()
        log_payload(
            "publishEvent",
            f"Published success ack to {MQTT_TOPIC}: {payload}",
            context="mqtt_ack",
        )
    except Exception as exc:  # pylint: disable=broad-except
        log_payload(
            "publishEvent",
            f"Failed to publish success ack to {MQTT_TOPIC}: {exc}",
            context="mqtt_ack",
        )
    finally:
        client.loop_stop()
        client.disconnect()

def send_data(sheet_name: str,
              *values: Any,
              timeout: int = 30) -> None:
    """Lähettää tapahtuman Google Apps Scriptille.

    Käyttöesimerkkejä:
      1) CSV-muotoinen arvoketju:
         send_data("EventLogger", 1000, 2000, 3000)  # -> "1000,2000,3000"
      2) Valmis dict:
         send_data("EventLogger", {"type": "ALARM", "code": 123})

    Params:
      sheet_name: Google Sheet -välilehti
      *values: arvot, jotka yhdistetään lähetettäväksi
      timeout: HTTP timeout sekunteina
    """

    if not values:
        value_string = ""
    elif len(values) == 1 and isinstance(values[0], dict):
        value_string = json.dumps(values[0], ensure_ascii=False)
    else:
        value_string = ",".join(str(v) for v in values)

    payload = {
        "sheet_name": sheet_name,
        "values": value_string,
    }

    status_fields = _build_status_fields(values)

    log_payload(
        "publishEvent",
        {"payload": payload, "status_fields": status_fields},
        context="send_data",
    )

    headers = {"Content-Type": "application/json"}

    try:
        print(f"Connecting to {URL}...")
        response = requests.post(URL, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            print(payload)
            print("Event data published successfully.")
            print("Response:", response.text)
            log_payload("publishEvent", f"Success: {response.text}")
            _publish_acknowledgement(status_fields)
        else:
            print(f"Failed to publish event data. Status Code: {response.status_code}")
            print("Response:", response.text)
            log_payload(
                "publishEvent",
                f"Failure {response.status_code}: {response.text}",
            )
    except requests.exceptions.RequestException as exc:
        print(f"Connection failed: {exc}")
        log_payload("publishEvent", f"Connection failed: {exc}")