#使用seeed xiao调试，需要手机端安装Blue Fruit Connect 的APP才能发送uart信息
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
        one_byte = uart.read(1)
        if one_byte:
            print(one_byte)
            uart.write(one_byte)
        else:
            print('no msg')