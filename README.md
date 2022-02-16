# battery2mqtt
*Push information about batteries in your system to MQTT*

I thought of this project when I switched to using my old laptop as my Home Assistant server. I wanted to track its battery level in Home Assistant to use in automations. Hopefully others can find it useful as well.

# Summary
`battery2mqtt` can monitor current battery percentage, charging status, etc. for any batteries present at `/sys/class/power_supply`. The MQTT topic format is `battery2mqtt/$TOPIC/$NAME` where `$TOPIC` is the topic you define and `$NAME` is the name of each battery. For example, if `/sys/class/power_supply/BAT0` is present in your system and you choose `server` to be the topic, the full topic will be `battery2mqtt/server/BAT0`. The topic for sensor availability would be `battery2mqtt/server/status`.

# Instructions

**Option 1: Manual build**
1. Clone repo: `git clone https://github.com/Tediore/battery2mqtt`
2. Enter directory: `cd battery2mqtt`
3. Build image: `docker build . -t battery2mqtt`
4. Customize `docker-compose.yaml` to fit your needs
5. `docker-compose up -d`

**Option 2: Docker Hub**
1. Follow steps 4 and 5 above using `tediore/battery2mqtt:latest` as the image.

Example docker-compose.yaml with all possible environmental variables listed:
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
    - MONITORED_CONDITIONS=status,capacity,energy_now,energy_full,energy_full_design,power_now,voltage_now
    - BATTERY_HEALTH=1
    - TIME_REMAINING=1
    - SHOW_UNITS=1
    - AC_ADAPTER=1
    - LOG_LEVEL=info
    volumes:
    - /sys/class/power_supply:/sys/class/power_supply:ro
    restart: unless-stopped
```

Example `docker run` command with all possible environmental variables:
```
docker run --name battery2mqtt \
-e MQTT_HOST=10.0.0.2 \
-e MQTT_PORT=1883 \
-e MQTT_USER=user \
-e MQTT_PASSWORD=password \
-e MQTT_TOPIC=server \
-e MQTT_QOS=1 \
-e INTERVAL=60 \
-e MONITORED_CONDITIONS=status,capacity,energy_now,energy_full,energy_full_design,power_now,voltage_now \
-e BATTERY_HEALTH=1 \
-e TIME_REMAINING=1 \
-e SHOW_UNITS=1 \
-e AC_ADAPTER=1 \
-e LOG_LEVEL=info \
-v /sys/class/power_supply:/sys/class/power_supply:ro \
tediore/battery2mqtt:latest
```

# Configuration
| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `MQTT_HOST` | `None` | True | IP address or hostname of the MQTT broker to connect to. |
| `MQTT_PORT` | `1883` | False | The port the MQTT broker is bound to. |
| `MQTT_USER` | `None` | False | The user to send to the MQTT broker. |
| `MQTT_PASSWORD` | `None` | False | The password to send to the MQTT broker. |
| `MQTT_TOPIC` | `server` | True | The topic prefix to send the payload to. |
| `MQTT_QOS` | `1` | False | The MQTT QoS level. |
| `INTERVAL` | `60` | False | How often (in seconds) battery2mqtt polls for battery info. |
| `MONITORED_CONDITIONS` | (See below) | True | Battery properties to send to MQTT (must be a comma-separated string). |
| `BATTERY_HEALTH` | `1` | False | Enable/disable battery health percentage calculation. Set to 0 to disable. |
| `TIME_REMAINING` | `1` | False | Enable/disable time remaining estimate (in hours). Set to 0 to disable. |
| `SHOW_UNITS` | `1` | False | Enable/disable power units in the MQTT payload. Set to 0 to disable. |
| `AC_ADAPTER` | `0` | False | Enable/disable AC adapter status. Set to 1 to enable. |
| `LOG_LEVEL` | `info` | False | Set minimum log level. Valid options are `debug`, `info`, `warning`, and `error`. |

# Multiple instances
If you plan on using `battery2mqtt` on more than one machine, it is very important that you use a **different MQTT_TOPIC for each instance**; otherwise, you _will_ experience issues with LWT.

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

\* Batteries lose capacity with each charge cycle. *Energy full* shows the actual full capacity of the battery due to wear; *Energy full design* shows the capacity the battery was able to hold when factory fresh.

# Battery health and time remaining calculations
The default is to also provide a battery health percentage calculation by dividing `energy_full` by `energy_full_design`. This can be disabled by setting `BATTERY_HEALTH` to `0` in your `docker-compose.yaml`. 
Similiarly, an estimate of time remaining on battery (in hours) is calculated by dividing `energy_now` by `power_now`. This can be disabled by setting `TIME_REMAINING` to `0` in your `docker-compose.yaml`.

# AC adapter monitoring
You can monitor the status of the AC adapter (online or offline) by setting `AC_ADAPTER` to `1`. This is disabled by default.

# Example Home Assistant configuration
```yaml
sensor:
- platform: mqtt
  name: Server battery
  state_topic: &server_battery_topic "battery2mqtt/server/BAT0"
  value_template: "{{ value_json.capacity }}"
  unit_of_measurement: '%'
  json_attributes_topic: *server_battery_topic
  availability_topic: "battery2mqtt/server/status"
  device_class: battery
```

# TODO
1. ~~Implement LWT~~
2. ~~Add proper logging~~
3. Add Home Assistant MQTT autodiscovery?
4. ???
5. Profit
