import os
import sys
import json
from time import sleep
import paho.mqtt.client as mqtt
import logging

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_CLIENT = os.getenv('MQTT_CLIENT', 'battery2mqtt')
MQTT_QOS = int(os.getenv('MQTT_QOS', 1))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'server')
INTERVAL = int(os.getenv('INTERVAL', 60))
MONITORED_CONDITIONS = os.environ.get('MONITORED_CONDITIONS','status,capacity,energy_now,energy_full,energy_full_design,power_now,voltage_now')
SHOW_UNITS = int(os.getenv('SHOW_UNITS', 1))
BATTERY_HEALTH = int(os.getenv('BATTERY_HEALTH', 1))
TIME_REMAINING = int(os.getenv('TIME_REMAINING', 1))
AC_ADAPTER = int(os.getenv('AC_ADAPTER', 0))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

if LOG_LEVEL.lower() not in ['debug', 'info', 'warning', 'error']:
    logging.basicConfig(level='INFO', format='%(asctime)s %(levelname)s: %(message)s')
    logging.warning(f'Selected log level "{LOG_LEVEL}" is not valid; using default')
else:
    logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s: %(message)s')

client = mqtt.Client(MQTT_CLIENT)

monitored_conditions = MONITORED_CONDITIONS.split(',')
path = "/sys/class/power_supply/"
dirs = os.listdir(path)

payload = {}
health_calc = {}
time_remaining = {}
mqtt_connected = False

def mqtt_connect():
    # Connect to MQTT broker, set LWT, and start loop
    global mqtt_connected
    try:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.will_set("battery2mqtt/" + MQTT_TOPIC + '/status', 'offline', 0, True)
        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_start()
        client.publish("battery2mqtt/" + MQTT_TOPIC + '/status', 'online', 0, True)
        logging.info('Connected to MQTT broker.')
        mqtt_connected = True
    except Exception as e:
        logging.error(f'Unable to connect to MQTT broker: {e}')
        sys.exit()

def check_conditions():
    # Check that the conditions the user requested are present on the system
    for dir in dirs:
        if not dir.startswith('AC'):
            for name in monitored_conditions:
                try:
                    with open(path + dir + '/' + name, 'r') as file:
                        file.read()
                    if LOG_LEVEL == 'DEBUG':
                        logging.debug(f'Condition "{name}" found.')
                except:
                    logging.warning(f'Condition "{name}" not found.')

def get_info():
    # Get requested conditions and generate/send MQTT payload
    global payload
    for dir in dirs:
        if AC_ADAPTER:
            if dir.startswith('AC'):
                try:
                    with open(path + dir + '/online', 'r') as file:
                        payload['ac_adapter'] = 'online' if int(file.read()) else 'offline'
                except:
                    pass

        for name in monitored_conditions:
            try:
                with open(path + dir + '/' + name, 'r') as file:
                    if name in ['alarm', 'capacity', 'cycle_count', 'online', 'present']:
                        payload[name] = int(file.read().replace('\n',''))
                    elif name.startswith('voltage') or name.startswith('energy') or name.startswith('power'):
                        if name.startswith('voltage'):
                            unit = ' V' if SHOW_UNITS else ''
                        elif name.startswith('energy'):
                            unit = ' Wh' if SHOW_UNITS else ''
                        else:
                            unit = ' W' if SHOW_UNITS else ''

                        if SHOW_UNITS:
                            payload[name] = str(round(float(file.read().replace('\n','')) / 1000000,2)) + unit
                        else:
                            payload[name] = round(float(file.read().replace('\n','')) / 1000000,2)
                    else:
                        payload[name] = file.read().replace('\n','')
            except:
                pass

        if BATTERY_HEALTH:
            unit = ' %' if SHOW_UNITS else ''
            try:
                for name in ['energy_full_design', 'energy_full']:
                    with open(path + dir + '/' + name, 'r') as file:
                        health_calc[name] = int(file.read().replace('\n',''))
                if SHOW_UNITS:
                    payload['battery_health'] = str(round((health_calc['energy_full'] / health_calc['energy_full_design']) * 100,2)) + unit
                else:
                    payload['battery_health'] = round((health_calc['energy_full'] / health_calc['energy_full_design']) * 100,2)
            except:
                pass
        
        if TIME_REMAINING:
            unit = ' h' if SHOW_UNITS else ''
            try:
                for name in ['energy_now', 'power_now']:
                    with open(path + dir + '/' + name, 'r') as file:
                        time_remaining[name] = int(file.read().replace('\n',''))
                if SHOW_UNITS:
                    payload['time_remaining'] = str(round((time_remaining['energy_now'] / time_remaining['power_now']),2) if round((time_remaining['energy_now'] / time_remaining['power_now']),2) < 24 else '> 24') + unit
                else:
                    payload['time_remaining'] = round((time_remaining['energy_now'] / time_remaining['power_now']),2) if round((time_remaining['energy_now'] / time_remaining['power_now']),2) < 24 else '> 24'
            except:
                pass

        try:
            if not dir.startswith('AC'):
                client.publish("battery2mqtt/" + MQTT_TOPIC + '/' + dir, json.dumps(payload), MQTT_QOS, False)
                if LOG_LEVEL == 'DEBUG':
                    logging.debug('Sending MQTT payload: ' + str(payload))
        except Exception as e:
            logging.error(f'Message send failed: {e}')

check_conditions()
mqtt_connect()

while mqtt_connected:
    get_info()
    sleep(INTERVAL)
