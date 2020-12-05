# battery2mqtt
*Push information about batteries in your system to MQTT*

I thought of this project when I switched to using my old laptop as my Home Assistant server. I wanted to track its battery level in Home Assistant to use in automations. I'm very new to Python, so I'm sure there's room for improvement here--I'd love to hear any suggestions (just be gentle, please).

# Summary
`battery2mqtt` can monitor current battery percentage, charging status, etc. for any batteries present at `/sys/class/power_supply`. The MQTT topic format is `battery2mqtt/$TOPIC/$NAME` where `$TOPIC` is the topic you define and `$NAME` is the name of each battery. For example, if `/sys/class/power_supply/BAT0` is present in your system and you choose `server` to be the topic, the full topic will be `battery2mqtt/server/BAT0`.

# Instructions
1. Clone repo: `git clone https://github.com/Tediore/battery2mqtt`
2. Enter directory: `cd battery2mqtt`
3. Build image: `docker build . -t battery2mqtt`
4. Customize `docker-compose.yaml` to fit your needs
5. `docker-compose up -d`

Example compose file with all possible environmental variables listed:
```yaml
version: '3'
services:
  battery2mqtt:
    container_name: battery2mqtt
    image: battery2mqtt:latest
    environment:
    - MQTT_HOST=10.0.0.2
    - MQTT_PORT=1883
    - MQTT_USER=user
    - MQTT_PASSWORD=password
    - MQTT_TOPIC=server
    - MQTT_QOS=1
    - INTERVAL=60
    - MONITORED_CONDITIONS=status,capacity
    volumes:
    - /sys/class/power_supply:/sys/class/power_supply:ro
    restart: unless-stopped
```

# Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_HOST` | `None` | IP address or hostname of the MQTT broker to connect to. |
| `MQTT_PORT` | `1883` | The port the MQTT broker is bound to. |
| `MQTT_USER` | `None` | The user to send to the MQTT broker. |
| `MQTT_PASSWORD` | `None` | The password to send to the MQTT broker. |
| `MQTT_TOPIC` | `server` | The topic to send the payload to. |
| `MQTT_QOS` | `1` | The MQTT QoS level. |
| `INTERVAL` | `60` | How often (in seconds) battery2mqtt polls for battery info. |
| `MONITORED_CONDITIONS` | (See below) | Battery properties to send to MQTT (must be a comma-separated string.) |

# Monitored conditions
You can specify only those conditions that you'd like to track. The default is to track `alarm, capacity, capacity_level, present, status, and voltage_now`. You can add more conditions (found at `/sys/class/power_supply/$NAME`) or choose only those you want to track. The variable in your `docker-compose.yaml` must follow this format: `alarm,capacity,capacity_level,present,status,voltage_now`

# Example Home Assistant configuration
```yaml
sensor:
- platform: mqtt
  name: Server battery
  state_topic: &battery_topic "battery2mqtt/server/BAT0"
  value_template: "{{ value_json.capacity }}"
  unit_of_measurement: '%'
  icon: 'mdi:battery'
  json_attributes_topic: *battery_topic
```