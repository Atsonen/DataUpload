import json
import requests

HOST = "https://script.google.com"
SCRIPT_ID = "AKfycbwzZCJKv3pyLBs3dSVUgYUYwQPKIS5atRKHsvxcFNSNJTDVg51MisQtZW0EGYmvTfzp6g"
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"


def send_data(device_name: str, event_data):
    if not isinstance(event_data, dict):
        event_payload = {"raw_payload": str(event_data)}
    else:
        event_payload = event_data

    payload = {
        "sheet_name": device_name,
        "values": json.dumps(event_payload, ensure_ascii=False),
        "command": "insert_event",
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
