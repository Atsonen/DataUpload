import paho.mqtt.client as mqtt
import publishData

# Määrittele MQTT-palvelimen tiedot
MQTT_BROKER = "192.168.1.51"  # MQTT-välittäjän IP-osoite
MQTT_PORT = 1883              # MQTT-oletusportti
MQTT_TOPIC = "Datalogger/"    # Seurattava aihe

# Kun yhdistätään palvelimeen
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Yhdistetty onnistuneesti MQTT-välittäjään.")
        client.subscribe(MQTT_TOPIC)
        print(f"Tilattu aihe: {MQTT_TOPIC}")
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

        topic_parts = msg.topic.split('/')  # Jaa aihe osiin
        if len(topic_parts) >= 2:  # Varmistetaan, että aiheessa on riittävästi osia
            device_name = topic_parts[1]  # Laitteen nimi toisena osana

            # Poista aaltosulut ja jaa arvot pilkun perusteella
            payload_cleaned = payload.strip('{}')
            values = payload_cleaned.split(',')

            # Korvataan puuttuvat arvot oletusarvolla 99
            try:
                int_values = [
                    int(value.strip()) if value.strip() else 99
                    for value in values
                ]
            except ValueError as ve:
                print(f"Virhe: Sanoman arvot eivät ole kokonaislukuja. Virhe: {ve}")
                return

            # Tarkistetaan, että riittävästi arvoja käsitellään
            dataset_size = len(int_values)
            if dataset_size > 0 and dataset_size <= 40:  # Varmista, että datasetti mahtuu määritettyyn alueeseen
                publishData.send_data(
                    "DataUpload2", *int_values
                )
            else:
                print(f"Virhe: Datasetin koko ({dataset_size}) ei ole hyväksyttävä: {payload}")
        else:
            print(f"Virheellinen aihe: {msg.topic}")
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
