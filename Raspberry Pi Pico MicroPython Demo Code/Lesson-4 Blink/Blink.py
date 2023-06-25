import machine
import utime

led_onboard = machine.Pin(16, machine.Pin.OUT)

while True: 
    led_onboard.value(1)
    print(1)
    utime.sleep(5) 
    led_onboard.value(0)
    print(0)
    utime.sleep(5)


这个代码有问题，因为zero把简单led更新成了rgb，控制方法有变化