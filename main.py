import machine, neopixel, time

pixel_pin = 16
pixel = neopixel.NeoPixel(machine.Pin(pixel_pin), 1)

# grb not rgb
while True:
    time.sleep(1)
    pixel[0] = (255, 0, 0)
    pixel.write()

    time.sleep(1)
    pixel[0] = (0, 255, 0)
    pixel.write()

    time.sleep(1)
    pixel[0] = (0, 0, 255)
    pixel.write()
