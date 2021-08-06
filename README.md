# battery2mqtt
*Push information about batteries in your system to MQTT*

I thought of this project when I switched to using my old laptop as my Home Assistant server. I wanted to track its battery level in Home Assistant to use in automations. I'm very new to Python, so I'm sure there's room for improvement here.

# Summary
`battery2mqtt` can monitor current battery percentage, charging status, etc. for any batteries present at `/sys/class/power_supply`. The MQTT topic format is `battery2mqtt/$TOPIC/$NAME` where `$TOPIC` is the topic you define and `$NAME` is the name of each battery. For example, if `/sys/class/power_supply/BAT0` is present in your system and you choose `server` to be the topic, the full topic will be `battery2mqtt/server/BAT0`.

# Instructions

**Option 1: Pull from Docker Hub**
`docker pull tediore/battery2mqtt:latest` (https://hub.docker.com/r/tediore/battery2mqtt)

**Option 2: Manual build**
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
    - BATTERY_HEALTH=1
    - TIME_REMAINING=1
    - SHOW_UNITS=1
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
| `MQTT_TOPIC` | `server` | The topic prefix to send the payload to. |
| `MQTT_QOS` | `1` | The MQTT QoS level. |
| `INTERVAL` | `60` | How often (in seconds) battery2mqtt polls for battery info. |
| `MONITORED_CONDITIONS` | (See below) | Battery properties to send to MQTT (must be a comma-separated string). |
| `BATTERY_HEALTH` | `1` | Set to 1 to enable battery health percentage calculation or 0 to disable. |
| `TIME_REMAINING` | `1` | Set to 1 to enable time remaining estimate (in hours) or 0 to disable. |
| `SHOW_UNITS` | `1` | Set to 1 to show power units in the MQTT payload or 0 to disable. |

# Monitored conditions
You can specify only those conditions that you'd like to track. The default is to track `status, capacity, energy_now, energy_full, energy_full_design, power_now, voltage_now`. You can add more conditions (found at `/sys/class/power_supply/$NAME`) or choose only those you want to track. The variable in your `docker-compose.yaml` must follow this comma-separated format:

```
status,capacity,energy_now,energy_full,energy_full_design,power_now,voltage_now
```
A summary of these conditions is below.
| Condition | Description | Unit |
|-----------|-------------|------|
| Status | Battery status (charging, discharging, full) | None |
| Capacity | Current battery percentage | % |
| Energy now | Current battery capacity | Wh (watt-hours) |
| Energy full | Battery capacity when full | Wh |
| Energy full design | Original battery capacity when full* | Wh |
| Power now | Current power consumption | W |
| Voltage now | Current battery voltage | V |
| Battery health | (See next section) | % |
| Time remaining | (See next section) | Hr |

* Batteries lose capacity with each charge cycle. *Energy full* shows the actual current full capacity of the battery due to wear; *Energy full design* shows the capacity the battery was designed to hold when factory fresh.

# Battery health and time remaining calculations
The default is to also provide a battery health percentage calculation by dividing `energy_full` by `energy_full_design`. This can be disabled by setting `BATTERY_HEALTH` to `0` in your `docker-compose.yaml`. 
Similiarly, an estimate of time remaining on battery (in hours) is calculated by dividing `energy_now` by `power_now`. This can be disabled by setting `TIME_REMAINING` to `0` in your `docker-compose.yaml`.

# Example Home Assistant configuration
```yaml
sensor:
- platform: mqtt
  name: Server battery
  state_topic: &server_battery_topic "battery2mqtt/server/BAT0"
  value_template: "{{ value_json.capacity }}"
  unit_of_measurement: '%'
  icon: 'mdi:battery'
  json_attributes_topic: *server_battery_topic
```
