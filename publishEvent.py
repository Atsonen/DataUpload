import json
import requests

HOST = "https://script.google.com"
SCRIPT_ID = "AKfycbwE9irQKciLv7vXbJRCyT9v5xXyQMYiqvaBr_3R7jfNsJg37hvKaSyco1EbP4BUu9Zn"
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"


def send_data(device_name: str, event_data):
    if not isinstance(event_data, dict):
        event_payload = {"raw_payload": str(event_data)}
    else:
        event_payload = event_data

    payload = {
        "sheet_name": device_name,
        "values": json.dumps(event_payload, ensure_ascii=False),
        
    }

    headers = {"Content-Type": "application/json"}

    try:
        print(f"Connecting to {URL}...")
        response = requests.post(URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            print("Event data published successfully.")
            print("Response:", response.text)
        else:
            print(f"Failed to publish event data. Status Code: {response.status_code}")
            print("Response:", response.text)
    except requests.exceptions.RequestException as exc:
        print(f"Connection failed: {exc}")