import requests

# Vakioarvot
HOST = "https://script.google.com"
SCRIPT_ID = "AKfycbyMvbyVtql9r3sGCPpy96RIc9fCt1Ja4w-OK2nx9W9wkd0zEEl_LaORH8Sz2N-cx8x2"
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"


def _format_values(values):
    """Palauta Apps Scriptin odottama pilkuin eroteltu merkkijono."""
    return ",".join(str(value) for value in values)


def send_data(sheet_name, *values):
    """Lähetä tapahtumadata Google Apps Scriptille JSON-muodossa."""
    if not sheet_name:
        raise ValueError("sheet_name on annettava")

    if len(values) < 7:
        raise ValueError("EventLogger vaatii vähintään 7 arvoa")

    payload = {
        "sheet_name": sheet_name,
        "values": _format_values(values),
    }

    headers = {"Content-Type": "application/json"}

    try:
        print(f"Connecting to {URL}...")
        response = requests.post(URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            print("Data published successfully.")
            print("Response:", response.text)
        else:
            print(f"Failed to publish data. Status Code: {response.status_code}")
            print("Response:", response.text)

    except requests.exceptions.RequestException as err:
        print(f"Connection failed: {err}")
