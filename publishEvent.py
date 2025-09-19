import json
import requests
import paho.mqtt.publish as mqtt_publish
from typing import Any

from payload_logger import log_payload

HOST = "https://script.google.com"
# Valitse tähän se oikea oman Apps Script -julkaisusi ID:
SCRIPT_ID = "AKfycbwzZCJKv3pyLBs3dSVUgYUYwQPKIS5atRKHsvxcFNSNJTDVg51MisQtZW0EGYmvTfzp6g"
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"

MQTT_BROKER = "192.168.1.51"
MQTT_PORT = 1883
MQTT_SUCCESS_TOPIC = "Sensors/EventLogger"
SUCCESS_PAYLOAD = {
    "Done": 10,
    "Spare1": 1,
    "Spare2": 2,
    "Status": 3,
}

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

    log_payload("publishEvent", payload)

    headers = {"Content-Type": "application/json"}

    try:
        print(f"Connecting to {URL}...")
        response = requests.post(URL, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            print(payload)
            print("Event data published successfully.")
            print("Response:", response.text)
            log_payload("publishEvent", f"Success: {response.text}")
            try:
                mqtt_payload = json.dumps(SUCCESS_PAYLOAD, ensure_ascii=False)
                mqtt_publish.single(
                    MQTT_SUCCESS_TOPIC,
                    payload=mqtt_payload,
                    hostname=MQTT_BROKER,
                    port=MQTT_PORT,
                    retain=False,
                )
                log_payload(
                    "publishEvent",
                    f"Published success ack to {MQTT_SUCCESS_TOPIC}: {mqtt_payload}",
                )
            except Exception as exc:
                print(f"Failed to publish success ack to MQTT: {exc}")
                log_payload(
                    "publishEvent",
                    f"Failed to publish success ack: {exc}",
                )
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
