import json
import re
from typing import Any, Dict, Iterable, List, Optional

import paho.mqtt.client as mqtt
import publishEvent
from payload_logger import log_payload

MQTT_BROKER = "192.168.1.51"
MQTT_PORT = 1883
MQTT_TOPIC = "EventLogger/#"


EXPECTED_VALUE_COUNT = 7

FIELD_ALIASES = {
    "rssi": ("rssi", "signal", "signal_strength"),
    "priority": ("priority", "prio", "severity"),
    "device": ("device", "device_id", "device_ip", "ip"),
    "event_code": ("event_code", "code", "event", "eventid"),
    "event_word": ("event_word", "word"),
    "event_value": ("event_value", "value", "eventvalue"),
    "extra": ("extra", "extra_value", "addition", "payload"),
}


def _coerce_to_int(value: Any, field_name: str) -> int:
    if value is None:
        return 0
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
        log_payload(
            "EventLogger_MQTT_Client",
            f"Ei-numeerinen arvo '{value}' kentässä {field_name}, käytetään 0",
            context="value_conversion",
        )
        return 0


def _values_from_dict(data: Dict[str, Any], event_identifier: Optional[str]) -> List[int]:
    values: List[int] = []
    for field, aliases in FIELD_ALIASES.items():
        selected = next((data.get(alias) for alias in aliases if alias in data), None)
        if field == "event_code" and selected is None and event_identifier is not None:
            selected = event_identifier
        values.append(_coerce_to_int(selected, field))
    return values


def _ensure_length(values: Iterable[int]) -> List[int]:
    normalized = list(values)
    if len(normalized) < EXPECTED_VALUE_COUNT:
        normalized.extend([0] * (EXPECTED_VALUE_COUNT - len(normalized)))
    return normalized


def parse_event_payload(payload: str, event_identifier: Optional[str] = None) -> List[int]:
    """Parse incoming payload into the numeric format expected by the Apps Script."""

    payload = payload.strip()
    if not payload:
        raise ValueError("Tyhjä payload")

    data: Any
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, dict):
        return _ensure_length(_values_from_dict(data, event_identifier))

    if isinstance(data, list):
        return _ensure_length(_coerce_to_int(value, f"list[{index}]") for index, value in enumerate(data))

    separators = ",;\t"
    if any(sep in payload for sep in separators):
        parts = [part.strip() for part in re.split(r"[,;\t]", payload) if part.strip()]
    else:
        parts = [payload]

    values = [_coerce_to_int(value, f"segment[{index}]") for index, value in enumerate(parts)]

    if event_identifier and len(values) < EXPECTED_VALUE_COUNT:
        event_code = _coerce_to_int(event_identifier, "event_identifier")
        while len(values) < 4:
            values.append(0)
        values[3] = event_code

    return _ensure_length(values)


# MQTT callbacks

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("EventLogger MQTT client connected successfully.")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect. Return code: {rc}")


def on_message(client, userdata, msg):
    try:
        print("======= Event Message =======")
        print(f"Topic: {msg.topic}")
        try:
            payload = msg.payload.decode("utf-8")
        except UnicodeDecodeError as ude:
            print(f"Failed to decode payload: {ude}")
            log_payload("EventLogger_MQTT_Client", f"Decode failed: {ude}", context=msg.topic)
            return

        print(f"Payload: {payload}")
        print("=============================")
        log_payload("EventLogger_MQTT_Client", payload, context=msg.topic)

        topic_parts = msg.topic.split('/')
        device_name = topic_parts[1] if len(topic_parts) >= 2 and topic_parts[1] else "EventLogger"
        if len(topic_parts) >= 3 and topic_parts[2]:
            event_identifier = topic_parts[2]
        else:
            event_identifier = None

        try:
            event_values = parse_event_payload(payload, event_identifier)
        except ValueError as exc:
            print(f"Error parsing event payload: {exc}")
            log_payload("EventLogger_MQTT_Client", f"Parsing error: {exc}", context=msg.topic)
            return

        publishEvent.send_data(device_name, *event_values)
        log_payload(
            "EventLogger_MQTT_Client",
            f"Forwarded values: {event_values}",
            context=device_name,
        )
    except Exception as exc:
        print(f"Error handling event message: {exc}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print(f"Connecting to broker: {MQTT_BROKER}:{MQTT_PORT}")
    client.loop_forever()
except KeyboardInterrupt:
    print("EventLogger MQTT client interrupted.")
except Exception as exc:
    print(f"MQTT client error: {exc}")
