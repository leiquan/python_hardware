#使用seeed xiao调试，需要手机端安装Blue Fruit Connect 的APP才能发送uart信息
#uart 不仅能发送消息，还拥有一些已经定义好的控制功能，可以直接使用Blue Fruit Connect上下左右
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

ble = BLERadio()
ble.name = "Smart Cloth"

uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

while True:
    
    ble.start_advertising(advertisement)
    
    while not ble.connected:
        pass
        
    while ble.connected:
        
        con = ble.connections[0]
        
        print(con)
        
        ble.stop_advertising()
        
        msg = uart.read()
        if msg:
            print(msg)
            uart.write(msg)
        else:
            print('no msg')
