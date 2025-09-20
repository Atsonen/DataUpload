import requests
from typing import Sequence, Dict

from payload_logger import log_payload


def _build_status_fields(values: Sequence[int]) -> Dict[str, int]:
    """Create a summary of key status fields from the payload values.

    The caller sends the data as a positional sequence, so we pick the
    interesting indices and fall back to ``0`` when the dataset is shorter
    than expected.  The "Done" field now reflects the 10th value from the
    payload (``values[9]``) instead of the previous fixed value.
    """

    normalized = list(values)

    def pick(index: int) -> int:
        return int(normalized[index]) if index < len(normalized) else 0

    return {
        "Done": pick(9),
        "Spare1": pick(1),
        "Spare2": pick(2),
        "Status": pick(3),
    }

# Vakioarvot
HOST = "https://script.google.com"
SCRIPT_ID = "AKfycbwnmiItP_1NRe0ER6dogBr29-qXEC97CUkgAK6nly3gn8IjlFxAE9FwUxA2ss0JaruFjA"  # Korvaa omalla Google Script ID:lläsi
URL = f"{HOST}/macros/s/{SCRIPT_ID}/exec"

def send_data(device_name, *values):
    """
    Lähettää datasetin HTTPS POST -pyynnöllä Google Apps Scriptille.
    """
    # Muodosta pilkulla eroteltu arvoketju
    value_string = ",".join(str(value) for value in values)

    # Muodosta oikea JSON-rakenne
    payload = {
        "sheet_name": device_name,
        "values": value_string,
        "command": "insert_row"
    }

    status_fields = _build_status_fields(values)
    log_payload("publishData", {"payload": payload, "status_fields": status_fields})

    headers = {"Content-Type": "application/json"}

    try:
        print(f"Connecting to {URL}...")
        response = requests.post(URL, headers=headers, json=payload, timeout=30)

        # Tarkista vastaus
        if response.status_code == 200:
            print("Data published successfully.")
            print("Response:", response.text)
            log_payload("publishData", f"Success: {response.text}")
        else:
            print(f"Failed to publish data. Status Code: {response.status_code}")
            print("Response:", response.text)
            log_payload(
                "publishData",
                f"Failure {response.status_code}: {response.text}",
            )

    except requests.exceptions.RequestException as e:
        print(f"Connection failed: {e}")
        log_payload("publishData", f"Connection failed: {e}")

# Esimerkki kutsu
# send_data("DataUpload2", 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000)
