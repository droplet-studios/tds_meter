from cqrobot.ADS1115_ReadVoltage import read_voltage
from mqtt import connect_mqtt, publish_mqtt

MQTT_TOPIC = 'aerogarden/tds' # topic to publish messages to

def main():
    connect_mqtt()
    while True:
        message = read_voltage()
        publish_mqtt(MQTT_TOPIC, message)
            
main()