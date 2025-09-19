import paho.mqtt.client as mqtt
import publishData
import publishEvent

# Määrittele MQTT-palvelimen tiedot
MQTT_BROKER = "192.168.1.51"  # MQTT-välittäjän IP-osoite
MQTT_PORT = 1883              # MQTT-oletusportti
MQTT_TOPICS = [
    ("Datalogger/#", 0),
    ("EventLogger/#", 0),
]

DATA_SHEET_NAME = "DataUpload2"
EVENT_DEFAULT_SHEET = "EventLogger"


def parse_payload(payload):
    """Palauttaa viestistä poimitut arvot kokonaislukuina."""
    start = payload.find('{')
    end = payload.rfind('}')

    if start != -1 and end != -1 and end > start:
        payload_content = payload[start + 1:end]
    else:
        payload_content = payload

    values = []
    for value in payload_content.split(','):
        stripped = value.strip()
        if not stripped:
            values.append(99)
            continue

        try:
            values.append(int(stripped))
        except ValueError as exc:
            raise ValueError(
                f"Sanoman arvo '{stripped}' ei ole kokonaisluku."
            ) from exc

    return values

# Kun yhdistätään palvelimeen
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Yhdistetty onnistuneesti MQTT-välittäjään.")
        for topic, qos in MQTT_TOPICS:
            client.subscribe(topic, qos=qos)
            print(f"Tilattu aihe: {topic} QoS {qos}")
    else:
        print(f"Yhdistäminen epäonnistui. Palautekoodi: {rc}")

# Kun uusi sanoma vastaanotetaan
def on_message(client, userdata, msg):
    try:
        print("------- Sanoman tiedot -------")
        print(f"Aihe: {msg.topic}")
        try:
            payload = msg.payload.decode('utf-8')
        except UnicodeDecodeError as ude:
            print(f"Virhe dekoodattaessa payloadia: {ude}")
            return

        print(f"Payload: {payload}")
        print("-----------------------------")

        topic_parts = [part for part in msg.topic.split('/') if part]
        if not topic_parts:
            print(f"Virheellinen aihe: {msg.topic}")
            return

        base_topic = topic_parts[0]

        try:
            int_values = parse_payload(payload)
        except ValueError as err:
            print(f"Virhe: {err}")
            return

        dataset_size = len(int_values)
        if dataset_size == 0 or dataset_size > 40:
            print(f"Virhe: Datasetin koko ({dataset_size}) ei ole hyväksyttävä: {payload}")
            return

        if base_topic == "Datalogger":
            publishData.send_data(DATA_SHEET_NAME, *int_values)
        elif base_topic == "EventLogger":
            sheet_name = topic_parts[1] if len(topic_parts) > 1 else EVENT_DEFAULT_SHEET
            publishEvent.send_data(sheet_name, *int_values)
        else:
            print(f"Tuntematon aihe: {msg.topic}")
    except Exception as e:
        print(f"Virhe käsiteltäessä sanomaa: {e}")

# Luo MQTT-asiakas
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    # Yhdistä MQTT-välittäjään
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print(f"Yhdistään välittäjään: {MQTT_BROKER}:{MQTT_PORT}")

    # Käynnistä asiakas ja pysy käynnissä
    client.loop_forever()
except KeyboardInterrupt:
    print("Ohjelma keskeytetty.")
except Exception as e:
    print(f"Virhe: {e}")
