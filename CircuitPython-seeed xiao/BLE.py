# SPDX-FileCopyrightText: 2022 Scott Shawcroft for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Simple connectable name advertisement. No services.
需要使用xiao
"""

from adafruit_ble import BLERadio

from adafruit_ble.advertising import Advertisement

ble = BLERadio()
advertisement = Advertisement()
advertisement.short_name = "HELLO"
advertisement.connectable = True

while True:
    print(advertisement)
    ble.start_advertising(advertisement, scan_response=b"")
    while not ble.connected:
        pass
    print("connected")
    while ble.connected:
        pass
    print("disconnected")
# 在这里写上你的代码 :-)
# 在这里写上你的代码 :-)
