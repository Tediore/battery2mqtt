import os
import sys
import json
from time import sleep
import paho.mqtt.client as mqtt
from threading import Thread as t
import logging

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
AC_ADAPTER = int(os.getenv('AC_ADAPTER', 0))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

class Battery:
    def __init__(self):
        self.monitored_conditions = MONITORED_CONDITIONS.split(',')
        self.payload = {}
        self.health_calc = {}
        self.time_remaining = {}

    def check_conditions(self):
        # Check that the conditions the user requested are present on the system
        for dir in dirs:
            if not dir.startswith('AC'):
                for name in self.monitored_conditions:
                    try:
                        with open(path + dir + '/' + name, 'r') as file:
                            file.read()
                        if LOG_LEVEL == 'DEBUG':
                            logging.debug(f'Condition "{name}" found.')
                    except:
                        logging.warning(f'Condition "{name}" not found.')

    def get_info(self):
        # Get requested conditions and generate/send MQTT payload
        while True:
            for dir in dirs:
                if AC_ADAPTER:
                    if dir.startswith('AC'):
                        try:
                            with open(path + dir + '/online', 'r') as file:
                                self.payload['ac_adapter'] = 'online' if int(file.read()) else 'offline'
                        except:
                            pass

                for name in self.monitored_conditions:
                    try:
                        with open(path + dir + '/' + name, 'r') as file:
                            if name in ['alarm', 'capacity', 'cycle_count', 'online', 'present']:
                                self.payload[name] = int(file.read().replace('\n',''))
                            elif name.startswith('voltage') or name.startswith('energy') or name.startswith('power'):
                                if name.startswith('voltage'):
                                    unit = ' V' if SHOW_UNITS else ''
                                elif name.startswith('energy'):
                                    unit = ' Wh' if SHOW_UNITS else ''
                                else:
                                    unit = ' W' if SHOW_UNITS else ''

                                if SHOW_UNITS:
                                    self.payload[name] = str(round(float(file.read().replace('\n','')) / 1000000,2)) + unit
                                else:
                                    self.payload[name] = round(float(file.read().replace('\n','')) / 1000000,2)
                            else:
                                self.payload[name] = file.read().replace('\n','')
                    except:
                        pass

                if BATTERY_HEALTH:
                    unit = ' %' if SHOW_UNITS else ''
                    try:
                        for name in ['energy_full_design', 'energy_full']:
                            with open(path + dir + '/' + name, 'r') as file:
                                self.health_calc[name] = int(file.read().replace('\n',''))
                        if SHOW_UNITS:
                            self.payload['battery_health'] = str(round((self.health_calc['energy_full'] / self.health_calc['energy_full_design']) * 100,2)) + unit
                        else:
                            self.payload['battery_health'] = round((self.health_calc['energy_full'] / self.health_calc['energy_full_design']) * 100,2)
                    except:
                        pass
                
                if TIME_REMAINING:
                    unit = ' h' if SHOW_UNITS else ''
                    try:
                        for name in ['energy_now', 'power_now']:
                            with open(path + dir + '/' + name, 'r') as file:
                                self.time_remaining[name] = int(file.read().replace('\n',''))
                        if SHOW_UNITS:
                            self.payload['time_remaining'] = str(round((self.time_remaining['energy_now'] / self.time_remaining['power_now']),2) if round((self.time_remaining['energy_now'] / self.time_remaining['power_now']),2) < 24 else '> 24') + unit
                        else:
                            self.payload['time_remaining'] = round((self.time_remaining['energy_now'] / self.time_remaining['power_now']),2) if round((self.time_remaining['energy_now'] / self.time_remaining['power_now']),2) < 24 else '> 24'
                    except:
                        pass

                try:
                    if not dir.startswith('AC'):
                        client.publish("battery2mqtt/" + MQTT_TOPIC + '/' + dir, json.dumps(self.payload), MQTT_QOS, False)
                        if LOG_LEVEL == 'DEBUG':
                            logging.debug('Sending MQTT payload: ' + str(self.payload))
                except Exception as e:
                    logging.error(f'Message send failed: {e}')
            try:
                client.publish("battery2mqtt/" + MQTT_TOPIC + '/status', 'online', 0, True)
            except Exception as e:
                logging.error(f'Message send failed: {e}')
            sleep(INTERVAL)

def mqtt_connect():
    # Connect to MQTT broker and set LWT
    try:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        client.will_set("battery2mqtt/" + MQTT_TOPIC + '/status', 'offline', 0, True)
        client.connect(MQTT_HOST, MQTT_PORT)
        client.publish("battery2mqtt/" + MQTT_TOPIC + '/status', 'online', 0, True)
        logging.info('Connected to MQTT broker.')
    except Exception as e:
        logging.error(f'Unable to connect to MQTT broker: {e}')
        sys.exit()

if __name__ == '__main__':
    if MQTT_HOST == None:
        logging.error('Please specify the IP address or hostname of your MQTT broker.')
        sys.exit()

    if LOG_LEVEL.lower() not in ['debug', 'info', 'warning', 'error']:
        logging.basicConfig(level='INFO', format='%(asctime)s %(levelname)s: %(message)s')
        logging.warning(f'Selected log level "{LOG_LEVEL}" is not valid; using default')
    else:
        logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s: %(message)s')

    client = mqtt.Client(f'battery2mqtt_{MQTT_TOPIC}')
    path = "/sys/class/power_supply/"
    dirs = os.listdir(path)
    b = Battery()

    b.check_conditions()
    mqtt_connect()
    polling_thread = t(target=b.get_info, daemon=True)
    polling_thread.start()
    client.loop_forever()