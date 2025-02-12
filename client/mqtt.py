import os
import wifi

import socketpool
import ssl
import adafruit_minimqtt.adafruit_minimqtt as MQTT 

import led
from led import LED2

from time import sleep

MAX_RETRIES = 10 # max retries for connections

# initialise socket pool and ssl context
SOCKET_POOL = socketpool.SocketPool(wifi.radio)
SSL_CONTEXT = ssl.create_default_context()

# initialise wifi connection
for i in range(MAX_RETRIES):
    try:
        print('Attempting Wi-Fi connection...')
        wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
        print('Connected to Wi-Fi!')
        led.wifi_connected()
        break
    except Exception as err:
        print(err)
else:
    led.error()

# initialise MQTT client
MQTT_CLIENT = MQTT.MQTT(broker='192.168.1.40',
                        socket_pool=SOCKET_POOL,
                        ssl_context=SSL_CONTEXT)

# runs when MQTT connected
def connected():
    print('Connected to MQTT broker!')
    led.mqtt_connected()

# runs when MQTT disconnected (attempts to reconnect MQTT)
def disconnected():
    print('MQTT disconnected. Attempting reconnection...')
    led.mqtt_disconnected()
    connect_mqtt()

MQTT_CLIENT.on_connect = connected
MQTT_CLIENT.on_disconnect = disconnected

# function to repeatedly retry mqtt connections
def connect_mqtt():
    for i in range(MAX_RETRIES):
        try:
            print('Attempting MQTT connection...')
            MQTT_CLIENT.connect()
            break
        except Exception as err:
            print(err)
    else:
        led.error()

def publish_mqtt(topic, message):
    MQTT_CLIENT.publish(topic, message)
    print('MQTT message published!')
    led.mqtt_sent()