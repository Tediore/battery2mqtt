FROM python:3-alpine
MAINTAINER Tediore <tediore.maliwan@gmail.com>

ADD battery2mqtt.py /

RUN pip install paho.mqtt

CMD [ "python", "./battery2mqtt.py" ]