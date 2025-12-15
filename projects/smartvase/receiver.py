import paho.mqtt.client as mqtt
from datetime import datetime

BROKER = "broker.hivemq.com"  # match your ESP32
PORT = 1883
TOPIC = "murad/vase/#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker!")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print("❌ Failed to connect, return code =", rc)

def on_message(client, userdata, msg):
    t = datetime.now().strftime("%H:%M:%S")
    topic = msg.topic
    payload = msg.payload.decode()
    if "events" in topic:
        print(f"\033[93m[{t}] 💥 TAP -> {payload}\033[0m")
    else:
        print(f"\033[92m[{t}] 🌿 Moisture -> {payload}\033[0m")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to broker {BROKER}:{PORT} ...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
