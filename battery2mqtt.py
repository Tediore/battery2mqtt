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
BATTERY_HEALTH = os.getenv('BATTERY_HEALTH', 1)
TIME_REMAINING = os.getenv('TIME_REMAINING', 1)

client = mqtt.Client("battery2mqtt")
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

monitored_conditions = MONITORED_CONDITIONS.split(',')

path = "/sys/class/power_supply/"

dirs = os.listdir(path)

payload = {}
health_calc = {}
time_remaining = {}

while True:
    for dir in dirs:
        for name in monitored_conditions:
            try:
                with open(path + dir + '/' + name, 'r') as file:
                    if name in ['alarm', 'capacity', 'cycle_count', 'online', 'present']:
                        payload[name] = int(file.read().replace('\n',''))
                    elif name.startswith('voltage') or name.startswith('energy') or name.startswith('power'):
                        payload[name] = round(float(file.read().replace('\n','')) / 1000000,2)
                    else:
                        payload[name] = file.read().replace('\n','')
            except:
                payload[name] = "condition not found"

        if BATTERY_HEALTH == '1':
            try:
                for name in ['energy_full_design', 'energy_full']:
                    with open(path + dir + '/' + name, 'r') as file:
                        health_calc[name] = int(file.read().replace('\n',''))
                payload['battery_health'] = round((health_calc['energy_full'] / health_calc['energy_full_design']) * 100,2)
            except:
                pass
        
        if TIME_REMAINING == '1':
            try:
                for name in ['energy_now', 'power_now']:
                    with open(path + dir + '/' + name, 'r') as file:
                        time_remaining[name] = int(file.read().replace('\n',''))
                payload['time_remaining'] = round((time_remaining['energy_now'] / time_remaining['power_now']),2)
            except:
                pass

    client.connect(MQTT_HOST)
    client.publish("battery2mqtt/" + MQTT_TOPIC + '/' + dir, json.dumps(payload), qos=MQTT_QOS, retain=False)

    sleep(INTERVAL)
