import paho.mqtt.client as mqtt
import statistics
import csv
import matplotlib.pyplot
import time
from datetime import datetime
import tomllib
import requests

SEC_IN_48_HRS = 60 * 60 * 24 * 2
SEC_IN_HOUR = 60 * 60
tds_levels = [] # temporarily holds TDS measurements (to average out)
has_notified = False # used for tracking whether notification sent already or not 

# the file path should be changed depending on where the config file is saved to
with open('/home/jellyman/aerogarden/config.toml', 'rb') as file:
    config = tomllib.load(file)

    # set constants from config file
    MQTT_TOPIC = config['mqtt_topic']
    MQTT_BROKER = config['mqtt_broker']

    MAX_LENGTH = config['reading_buffer_count']
    DATA_SAVE_DIR = config['data_save_dir']
    DATA_FILE_PATH = config['data_path']
    MIN_TDS = config['min_tds']

    PUSHOVER_API = config['pushover_api']
    PUSHOVER_USER = config['pushover_user']

def add_temp(value):
    """ Temporarily adds measurement to measurement list.
        Takes the mean, logs the data, and sends notification by default
    """

    global tds_levels
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
        writer.writerow([time.time(), value])
        print(f'Data written to \'{DATA_SAVE_DIR + DATA_FILE_PATH}\'')

def filter_data():
    """ Keep only the data with a timestamp in the last 48 hours """

    with open(DATA_SAVE_DIR + DATA_FILE_PATH, 'r') as file:
        reader = csv.reader(file)
        time_now = time.time()
        min_time = time_now - SEC_IN_48_HRS
        data = [row for row in reader if float(row[0]) >= min_time] # filter out data recorded over 48 hours ago
        for index, value in enumerate(data):
            data[index] = list(map(float, value)) # make each piece of data (time, value) into floats from string
            data[index][0] = (data[index][0] - time_now) / SEC_IN_HOUR # set time as difference between time data recorded and creation of graph, in hours
        return data

def plot():
    """ Plot data in the past 48 hours """

    data = filter_data()
    x = [datapt[0] for datapt in data]
    y = [datapt[1] for datapt in data]
    figure, axes = matplotlib.pyplot.subplots()
    axes.plot(x, y)
    axes.set(xlabel='time (hrs)', ylabel='TDS (ppm)', title='TDS values in last 48 hrs', xlim=(None, 0), ylim=(0, None))
    axes.grid()
    filename = DATA_SAVE_DIR + datetime.now().strftime('%Y%m%d%H%M%S' + '.jpg')
    figure.savefig(filename)
    print(f'Plot saved to \'{filename}\'')
    return filename

def notify(value):
    """ Post HTTP data to the Pushover API """
    
    global has_notified
    filename = plot()
    data = {'token': PUSHOVER_API,
                 'user': PUSHOVER_USER, 
                 'title': 'AeroGarden', 
                 'message': f'The TDS of your AeroGarden is currently {value}ppm. Please add nutrients.',
                 }
    file = {"attachment": ('graph.jpg', open(filename, 'rb'), 'image/jpeg')}
    with requests.post(url='https://api.pushover.net/1/messages.json', 
                       data=data,
                       files=file
                       ) as response:
        try:
            print(response.text)
            response.raise_for_status()
            print('Made HTTPS POST request to Pushover API')
            has_notified = True
        except ConnectionError as err:
            print(err)

def connected(client, userdata, flags, reason_code, properties):
    """ Subscribe to topic whenever connected to MQTT broker """

    print('Connected to broker')
    client.subscribe(MQTT_TOPIC) # subscribe after connect to broker

def message_received(client, userdata, msg):
    """ Get the received data and pass it to function to be processed """

    message = msg.payload.decode() # turn message into a string
    topic = msg.topic # save MQTT serve one more topic
    print(f'Received message \'{message}\' from topic \'{topic}\'')
    add_temp(message)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_message = message_received 
client.on_connect = connected

client.connect(MQTT_BROKER) # client is the same device as the broker

client.loop_forever() # persists network connection and reconnects