from paho.mqtt.client import Client as client
import statistics
import csv
import matplotlib.pyplot
import time
from datetime import datetime
from configparser import ConfigParser, UNNAMED_SECTION
import requests

SEC_IN_48_HRS = 60 * 60 * 24 * 2 
tds_levels = [] # temporarily holds TDS measurements (to average out)
has_notified = False # used for tracking whether notification sent already or not 

config = ConfigParser(allow_unnamed_section=True)
config.read('~/Documents/python/tds_meter/server/config.ini')

# get values from config file
MQTT_TOPIC = config.get(UNNAMED_SECTION, 'mqtt_topic')
MAX_LENGTH = config.get(UNNAMED_SECTION, 'reading_buffer_count')
DATA_SAVE_DIR = config.get(UNNAMED_SECTION, 'data_save_dir')
DATA_FILE_PATH = config.get(UNNAMED_SECTION, 'data_path')
MIN_TDS = config.get(UNNAMED_SECTION, 'min_tds')

PUSHOVER_API = config.get(UNNAMED_SECTION, 'pushover_api')
PUSHOVER_USER = config.get(UNNAMED_SECTION, 'pushover_user')

def message_received(client, userdata, msg):
    """ Things that are run every time an MQTT message is received."""

    message = msg.payload.decode() # turn message into a string
    topic = msg.topic # save MQTT serve one more topic
    print(f'Received message \'{message}\' from topic \'{topic}')
    add_temp(message)

client.subscribe(MQTT_TOPIC) # subscribe to MQTT topic
client.on_message = message_received # set function to add temp

def add_temp(value):
    """ Temporarily adds measurement to measurement list.
        Takes the mean, logs the data, and sends notification by default
    """

    if len(tds_levels) < int(MAX_LENGTH):
        tds_levels.append(float(value))
    else:
        avg = statistics.fmean(tds_levels)
        log(avg)
        if avg <= float(MIN_TDS) and not has_notified:
            notify(avg)
        tds_levels = []

def log(value):
    """ Appends data onto new line of CSV file """

    with open(DATA_SAVE_DIR + DATA_FILE_PATH, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(time.time(), value)

def filter_data():
    """ Keep only the data with a timestamp in the last 48 hours """

    with open(DATA_SAVE_DIR + DATA_FILE_PATH, 'r') as file:
        reader = csv.reader(file)
        min_time = time.time() - SEC_IN_48_HRS
        data = [row for row in reader if float(row[0]) >= min_time]
        for index, value in enumerate(data):
            data[index] = map(float, value)
        return data

def plot():
    """ Plot data in the past 48 hours """

    data = filter_data()
    x = [datapt[0] for datapt in data]
    y = [datapt[1] for datapt in data]
    figure, axes = matplotlib.pyplot.subplots()
    axes.plot(x, y)
    axes.set(xlabel='time (hrs)', ylabel='TDS (ppm)', title='TDS values in last 48 hrs')
    axes.grid()
    filename = DATA_SAVE_DIR + datetime.now().strftime('%Y%m%d%H%M%S' + '.jpg')
    figure.savefig(filename)
    return filename

def notify(value):
    """ Post HTTP data to the Pushover API """
    
    global has_notified
    filename = plot()
    with open(filename, 'rb') as file:
        binary_image = file.read()
    json_data = {'token': PUSHOVER_API,
                 'user': PUSHOVER_USER, 
                 'title': 'AeroGarden', 
                 'message': f'The TDS of your AeroGarden is currently {value}ppm. Please add nutrients.',
                 'attachment': binary_image}
    with requests.post(url='https://api.pushover.net/1/messages.json', json=json_data) as response:
        try:
            response = requests.post(url='https://api.pushover.net/1/messages.json', json=json_data) 
            response.raise_for_status()
            print('Made HTTPS POST request')
            has_notified = True
        except ConnectionError as err:
            print(err)