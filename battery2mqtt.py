import os
import json
from sys import int_info
from time import sleep
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_QOS = int(os.getenv('MQTT_QOS', 1))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'server')
INTERVAL = int(os.getenv('INTERVAL', 60))
MONITORED_CONDITIONS = os.environ.get('MONITORED_CONDITIONS','status,capacity,energy_now,energy_full,energy_full_design,power_now,voltage_now')
SHOW_UNITS = int(os.getenv('SHOW_UNITS', 1))
BATTERY_HEALTH = int(os.getenv('BATTERY_HEALTH', 1))
TIME_REMAINING = int(os.getenv('TIME_REMAINING', 1))
AC_ADAPTER = int(os.getenv('AC_ADAPTER', 1))

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
        if AC_ADAPTER == 1:
            if dir.startswith('AC'):
                try:
                    with open(path + dir + '/online', 'r') as file:
                        payload['ac_adapter'] = 'online' if int(file.read()) == 1 else 'offline'
                except:
                    pass

        for name in monitored_conditions:
            try:
                with open(path + dir + '/' + name, 'r') as file:
                    if name in ['alarm', 'capacity', 'cycle_count', 'online', 'present']:
                        payload[name] = int(file.read().replace('\n',''))
                    elif name.startswith('voltage') or name.startswith('energy') or name.startswith('power'):
                        if name.startswith('voltage'):
                            unit = ' V' if SHOW_UNITS == 1 else ''
                        elif name.startswith('energy'):
                            unit = ' Wh' if SHOW_UNITS == 1 else ''
                        else:
                            unit = ' W' if SHOW_UNITS == 1 else ''

                        if SHOW_UNITS == 1:
                            payload[name] = str(round(float(file.read().replace('\n','')) / 1000000,2)) + unit
                        else:
                            payload[name] = round(float(file.read().replace('\n','')) / 1000000,2)
                    else:
                        payload[name] = file.read().replace('\n','')
            except:
                payload[name] = "condition not found"

        if BATTERY_HEALTH == 1:
            unit = ' %' if SHOW_UNITS == 1 else ''
            try:
                for name in ['energy_full_design', 'energy_full']:
                    with open(path + dir + '/' + name, 'r') as file:
                        health_calc[name] = int(file.read().replace('\n',''))
                if SHOW_UNITS == 1:
                    payload['battery_health'] = str(round((health_calc['energy_full'] / health_calc['energy_full_design']) * 100,2)) + unit
                else:
                    payload['battery_health'] = round((health_calc['energy_full'] / health_calc['energy_full_design']) * 100,2)
            except:
                pass
        
        if TIME_REMAINING == 1:
            unit = ' h' if SHOW_UNITS == 1 else ''
            try:
                for name in ['energy_now', 'power_now']:
                    with open(path + dir + '/' + name, 'r') as file:
                        time_remaining[name] = int(file.read().replace('\n',''))
                if SHOW_UNITS == 1:
                    payload['time_remaining'] = str(round((time_remaining['energy_now'] / time_remaining['power_now']),2) if round((time_remaining['energy_now'] / time_remaining['power_now']),2) < 24 else '> 24') + unit
                else:
                    payload['time_remaining'] = round((time_remaining['energy_now'] / time_remaining['power_now']),2) if round((time_remaining['energy_now'] / time_remaining['power_now']),2) < 24 else '> 24'
            except:
                pass

    try:
        client.connect(MQTT_HOST)
        client.publish("battery2mqtt/" + MQTT_TOPIC + '/' + dir, json.dumps(payload), qos=MQTT_QOS, retain=False)
    except:
        print('Message send failed.')

    sleep(INTERVAL)
