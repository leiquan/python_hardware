from machine import ADC
import time
 
ts = ADC(4)
cfactor = 3.3 / (65535)
 
while True:
    value = ts.read_u16() * cfactor 
    temperature = 27 - (value - 0.706)/0.001721
    print(temperature)
    time.sleep(2)


#https://104.es/2022/12/27/raspberry-pi-pico-w-dht11/