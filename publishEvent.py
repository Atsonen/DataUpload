import json
import requests
from typing import Any, Dict, Optional

HOST = "https://script.google.com"
# Valitse tähän se oikea oman Apps Script -julkaisusi ID:
SCRIPT_ID = "AKfycbwzZCJKv3pyLBs3dSVUgYUYwQPKIS5atRKHsvxcFNSNJTDVg51MisQtZW0EGYmvTfzp6g"
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"

def send_data(device_name: str,
              data: Optional[Any] = None,
              *values: Any,
              sheet_name: str = "EventLogger",
              timeout: int = 30) -> None:
    """
    Lähettää tapahtuman Google Apps Scriptille.

    Käyttö:
      1) Dict-eventti:
         send_data("MyDevice", {"type": "ALARM", "code": 123, "msg": "Overheat"})
      2) Raaka-arvo:
         send_data("MyDevice", "some raw text")
      3) Numerolista/CSV:
         send_data("MyDevice", 1000, 2000, 3000)  # -> "1000,2000,3000"
         # tai
         send_data("MyDevice", 1000, 2000)  # data+*values -> "1000,2000"

    Params:
      device_name: laitteen tai datalähteen nimi
      data: dict/str/num tai None
      *values: lisäarvot CSV-käyttöön
      sheet_name: Google Sheet -välilehti (oletus "EventLogger")
      timeout: HTTP timeout sekunteina
    """

    # Muodosta event-payload useilla tavoilla, mutta yhtenäiseen muotoon
    if isinstance(data, dict):
        event_payload: Dict[str, Any] = data
    elif values:  # data + values tulkitaan CSV:ksi
        items = ((data,) + values) if data is not None else values
        csv_str = ",".join(str(v) for v in items)
        event_payload = {"csv": csv_str}
    else:
        # yksittäinen raakateksti/numero tai tyhjä
        event_payload = {"raw_payload": "" if data is None else str(data)}

    # Leimaa mukaan laitteen nimi; GAS-päässä voi käyttää tätä sarakkeessa
    event = {"device": device_name, **event_payload}

    payload = {
        "sheet_name": sheet_name,
        "command": "insert_event",
        # Viedään arvot JSON-muodossa yhteen kenttään; GAS parsii sen
        "values": json.dumps(event, ensure_ascii=False)
    }

    headers = {"Content-Type": "application/json"}

    try:
        print(f"Connecting to {URL}...")
        response = requests.post(URL, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            print("Event data published successfully.")
            print("Response:", response.text)
        else:
            print(f"Failed to publish event data. Status Code: {response.status_code}")
            print("Response:", response.text)
    except requests.exceptions.RequestException as exc:
        print(f"Connection failed: {exc}")
