import digitalio
import board

from time import sleep

# initialise power led
LED1 = digitalio.DigitalInOut(board.GP0)
LED1.direction = digitalio.Direction.OUTPUT
LED1.value = True

# initialise network led
LED2 = digitalio.DigitalInOut(board.GP1)
LED2.direction = digitalio.Direction.OUTPUT
LED2.value = False

# function to be called when there is repeated connection error
def error():
    while True:
        LED2.value = True
        sleep(0.25)
        LED2.value = False
        sleep(0.25)

# function to be called when connected to Wi-Fi
def wifi_connected():
        LED2.value = True
        sleep(1)
        LED2.value = False

# function to be called when connected to MQTT broker
def mqtt_connected():
     LED2.value = True

# function to be called when publish MQTT message
def mqtt_sent():
     LED2.value = False
     sleep(0.5)
     LED2.value = True

# function to be called when disconnected from MQTT broker
def mqtt_disconnected():
     LED2.value = False