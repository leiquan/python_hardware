from machine import Pin, I2C
import utime as time
from dht import DHT11, InvalidChecksum

while True:
    time.sleep(5)
    pin = Pin(29, Pin.OUT, Pin.PULL_DOWN)
    sensor = DHT11(pin)
    t  = (sensor.temperature)
    h = (sensor.humidity)
    print("Temperature: {} °C".format(sensor.temperature))
    print("Humidity: {}% ".format(sensor.humidity))