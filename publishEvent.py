import requests
import json

# Vakioarvot
HOST = "https://script.google.com"
SCRIPT_ID = "AKfycbyMvbyVtql9r3sGCPpy96RIc9fCt1Ja4w-OK2nx9W9wkd0zEEl_LaORH8Sz2N-cx8x2"  # Korvaa omalla Google Script ID:lläsi
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"

def send_data(device_name, *values):
    """
    Lähettää datasetin HTTPS POST -pyynnöllä Google Apps Scriptille.
    """
    # Muodosta pilkulla eroteltu arvoketju
    value_string = ",".join(str(value) for value in values)

    # Muodosta oikea JSON-rakenne
    payload = {
        "sheet_name": "EventLogger",
        "values": value_string,
    }

    headers = {"Content-Type": "application/json"}

    try:
        print(f"Connecting to {URL}...")
        response = requests.post(URL, headers=headers, json=payload, timeout=30)

        # Tarkista vastaus
        if response.status_code == 200:
            print("Data published successfully.")
            print("Response:", response.text)
        else:
            print(f"Failed to publish data. Status Code: {response.status_code}")
            print("Response:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {e}")

# Esimerkki kutsu
# send_data("DataUpload2", 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000)
