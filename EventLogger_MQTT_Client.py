import json
from typing import Any, Dict, List, Union

import paho.mqtt.client as mqtt
import publishEvent

MQTT_BROKER = "192.168.1.51"
MQTT_PORT = 1883
MQTT_TOPIC = "EventLogger/#"


ParsedEvent = Union[Dict[str, Any], List[str], str]


def parse_event_payload(payload: str) -> ParsedEvent:
    """Parse incoming payload for event logging."""
    payload = payload.strip()
    if not payload:
        return {}

    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"events": data}
    if data is not None:
        return {"value": data}

    # Fallback: try key-value pairs separated by ';' or ','
    separators = [';', ',']
    segments: List[str] = [payload]
    for separator in separators:
        if separator in payload:
            segments = [segment.strip() for segment in payload.split(separator) if segment.strip()]
            break

    event_data: Dict[str, Any] = {}
    for segment in segments:
        if '=' in segment:
            key, value = segment.split('=', 1)
            event_data[key.strip()] = value.strip()

    if event_data:
        return event_data

    if len(segments) > 1:
        return segments

    return payload


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
            return

        print(f"Payload: {payload}")
        print("=============================")

        topic_parts = msg.topic.split('/')
        device_name = topic_parts[1] if len(topic_parts) >= 2 and topic_parts[1] else "EventLogger"
        if len(topic_parts) >= 3 and topic_parts[2]:
            event_identifier = topic_parts[2]
        else:
            event_identifier = None

        event_data = parse_event_payload(payload)

        if isinstance(event_data, dict):
            if event_identifier and "event" not in event_data:
                event_data["event"] = event_identifier
            publishEvent.send_data(device_name, event_data)
            return

        if isinstance(event_data, (list, tuple)):
            values: List[str] = [str(value) for value in event_data]
        elif event_data is None:
            values = []
        else:
            values = [str(event_data)]

        if event_identifier:
            values.insert(0, event_identifier)

        publishEvent.send_data(device_name, *values)
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
