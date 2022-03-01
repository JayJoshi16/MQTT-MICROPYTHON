from machine import Pin
import network
import time
from umqtt.robust import MQTTClient
import os
import gc
import sys
import dht 

sensor = dht.DHT11(Pin(4))                  # DHT11 Sensor on Pin 4 of ESP32
led=Pin(2,Pin.OUT)                          # Onboard LED on Pin 2 of ESP32


WIFI_SSID     = '********'
WIFI_PASSWORD = '********'

random_num          = int.from_bytes(os.urandom(3), 'little')
mqtt_client_id      = bytes('client_'+str(random_num), 'utf-8')

ADAFRUIT_IO_URL     = b'io.adafruit.com' 
ADAFRUIT_USERNAME   = b'Your USERNAME of ADADRUIT IO'
ADAFRUIT_IO_KEY     = b'Your KEY'

TEMPRATURE_FEED_ID  = b'Your Feed ID'
TOGGLE_FEED_ID      = b'Your Feed ID'

ap_if = network.WLAN(network.AP_IF)         # turn off the WiFi Access Point
ap_if.active(False)

wifi = network.WLAN(network.STA_IF)         # connect the device to the WiFi network
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASSWORD)


MAX_ATTEMPTS = 20               
attempt_count = 0
while not wifi.isconnected() and attempt_count < MAX_ATTEMPTS:  # wait until the device is connected to the WiFi network
    attempt_count += 1
    print(".")
    time.sleep(1)

if attempt_count == MAX_ATTEMPTS:
    print('could not connect to the WiFi network')
    sys.exit()


client = MQTTClient(client_id=mqtt_client_id, 
                    server=ADAFRUIT_IO_URL, 
                    user=ADAFRUIT_USERNAME, 
                    password=ADAFRUIT_IO_KEY,
                    ssl=False)
try:            
    client.connect()
except Exception as e:
    print('could not connect to MQTT server {}{}'.format(type(e).__name__, e))
    sys.exit()


temprature_feed     = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, TEMPRATURE_FEED_ID), 'utf-8')
toggle_feed         = bytes('{:s}/feeds/{:s}'.format(ADAFRUIT_USERNAME, TOGGLE_FEED_ID), 'utf-8')


def cb(topic, msg):                             # Callback function
    print('Received Data:  Topic = {}, Msg = {}'.format(topic, msg))
    recieved_data = str(msg,'utf-8')            #   Recieving Data
    if recieved_data=="OFF":
        led.value(0)
    if recieved_data=="ON":
        led.value(1)
        
client.set_callback(cb)      # Callback function               
client.subscribe(toggle_feed) 


while True:
    try:
        time.sleep(2)
        sensor.measure()                    # Measuring 
        temp = sensor.temperature()         # getting Temp
        temp_f = temp * (9/5) + 32.0
        print('Temperature: %3.1f C' %temp)  
        print('Temperature: %3.1f F' %temp_f)  
        print('Humidity: %3.1f %%' %hum)

        client.publish(temprature_feed,    
                       bytes(str(temp), 'utf-8'),   # Publishing Temprature to adafruit.io
                       qos=0)
        client.check_msg()                  # non blocking function
    except OSError as e:
        print('Failed to read sensor.')
        client.disconnect()
        sys.exit()
