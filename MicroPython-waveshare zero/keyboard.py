from machine import Pin
import time

L1 = Pin(1, Pin.OUT)
L2 = Pin(2, Pin.OUT)
L3 = Pin(3, Pin.OUT)
L4 = Pin(4, Pin.OUT)

C1 = Pin(5, Pin.IN, Pin.PULL_DOWN)
C2 = Pin(6, Pin.IN, Pin.PULL_DOWN)
C3 = Pin(7, Pin.IN, Pin.PULL_DOWN)
C4 = Pin(8, Pin.IN, Pin.PULL_DOWN)


def readLine(line, characters):

    line.value(1)

    if C1.value() == 1:
        print(characters[0])
    if C2.value() == 1:
        print(characters[1])
    if C3.value() == 1:
        print(characters[2])
    if C4.value() == 1:
        print(characters[3])

    line.value(0)


try:
    while True:
        readLine(L1, ["1", "2", "3", "A"])
        readLine(L2, ["4", "5", "6", "B"])
        readLine(L3, ["7", "8", "9", "C"])
        readLine(L4, ["*", "0", "#", "D"])
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n Application stopped!")
