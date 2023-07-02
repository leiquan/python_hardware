import machine
from pico_i2c_lcd import I2cLcd
import utime as time
from dht import DHT11, InvalidChecksum
from machine import Pin

sda=machine.Pin(26)
scl=machine.Pin(27)

i2c=machine.I2C(1,sda=sda, scl=scl, freq=400000)

print('Scan i2c bus...')

devices = i2c.scan()

if len(devices) == 0:
    print("No i2c device !")
else:
    print('i2c devices found:',len(devices))

i2c_addr = devices[0]

lcd = I2cLcd(i2c, i2c_addr, 2, 16)

lcd.putstr('measuring...')

while True:
    time.sleep(3)
    pin = machine.Pin(29, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    sensor = DHT11(pin)
    
    t = sensor.temperature
    h = sensor.humidity
    lcd.clear()
    lcd.putstr("Tem: {} C\n".format(sensor.temperature))
    lcd.putstr("Hum: {} % ".format(sensor.humidity))
