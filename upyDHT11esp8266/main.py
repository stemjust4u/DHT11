import time
from umqttsimple import MQTTClient
import ubinascii
import machine
import network
import esp
from machine import Pin
import dht, ujson
esp.osdebug(None)
import gc
gc.collect()

ssid = 'Freddie-Windstream'
password = 'ironfish17'
mqtt_server = 'rpi3mqtt1'
#EXAMPLE IP ADDRESS or DOMAIN NAME
#mqtt_server = 'rpi3mqtt1'

client_id = ubinascii.hexlify(machine.unique_id())

topic_pub_data = b'esp2nred/temp/1'

last_message = 0
message_interval = 300

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connection successful')

sensor = dht.DHT11(Pin(14))
dht11D = {}
offsettemp = 0.0
offsethum = -9

def connect_mqtt():
  global client_id, mqtt_server
  client = MQTTClient(client_id, mqtt_server, user='sj4u', password='dewberry2233')
  #client = MQTTClient(client_id, mqtt_server, user=your_username, password=your_password)
  client.connect()
  print('Connected to %s MQTT broker' % (mqtt_server))
  return client

def restart_and_reconnect():
  print('Failed to connect to MQTT broker. Reconnecting...')
  time.sleep(10)
  machine.reset()

def read_sensor():
  try:
    sensor.measure()
    temp = sensor.temperature()
    # uncomment for Fahrenheit
    temp = temp * (9/5) + 32.0
    hum = sensor.humidity()
    #if (isinstance(temp, float) and isinstance(hum, float)) or (isinstance(temp, int) and isinstance(hum, int)):
    #temp = (b'{0:3.1f},'.format(temp))
    #hum =  (b'{0:3.1f},'.format(hum))
    return temp, hum
  except OSError as e:
    return('Failed to read sensor.')

try:
  client = connect_mqtt()
except OSError as e:
  restart_and_reconnect()

while True:
  try:
    if (time.time() - last_message) > message_interval:
      temp, hum = read_sensor()
      dht11D['tempf'] = temp + offsettemp
      dht11D['humidityi'] = hum + offsethum
      client.publish(topic_pub_data, ujson.dumps(dht11D))
      last_message = time.time()
  except OSError as e:
    restart_and_reconnect()