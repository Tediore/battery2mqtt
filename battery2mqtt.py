import os
import json
from time import sleep
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_QOS = int(os.getenv('MQTT_QOS', 1))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'server')
INTERVAL = int(os.getenv('INTERVAL', 60))
MONITORED_CONDITIONS = os.environ.get('MONITORED_CONDITIONS','alarm,capacity,capacity_level,present,status,voltage_now')

client = mqtt.Client("battery2mqtt")
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

monitored_conditions = MONITORED_CONDITIONS.split(',')

path = "/sys/class/power_supply"

dirs = os.listdir(path)

payload = {}

while True:
    for dir in dirs:
        for name in monitored_conditions:
            try:
                with open(path + '/' + dir + '/' + name, 'r') as file:
                    if name in ['alarm', 'capacity', 'present']:
                        payload[name] = int(file.read().replace('\n',''))
                    elif 'voltage' in name:
                        payload[name] = round(float(file.read().replace('\n','')) / 1000000,2)
                    else:
                        payload[name] = file.read().replace('\n','')
            except:
                payload[name] = "condition not found"

    client.connect(MQTT_HOST)
    client.publish("battery2mqtt/" + MQTT_TOPIC + '/' + dir, json.dumps(payload), qos=MQTT_QOS, retain=False)

    sleep(INTERVAL)
