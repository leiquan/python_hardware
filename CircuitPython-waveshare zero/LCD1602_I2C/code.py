import time
import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice

print("--- 串口连接测试开始 ---")

# --- Standalone PCF8574 1602 LCD Driver ---
class PCF8574_LCD:
    def __init__(self, i2c, address=0x27):
        self.i2c_device = I2CDevice(i2c, address)
        self.backlight = 0x08  # 0x08 = On, 0x00 = Off
        self.buf = bytearray(1)

        # Initialization sequence for HD44780 in 4-bit mode
        time.sleep(0.05)
        self._write_4bit(0x30)
        time.sleep(0.005)
        self._write_4bit(0x30)
        time.sleep(0.001)
        self._write_4bit(0x30)
        self._write_4bit(0x20)  # Set 4-bit mode

        # Display configuration
        self.command(0x28)  # 2 lines, 5x8 font
        self.command(0x0C)  # Display on, cursor off, blink off
        self.command(0x06)  # Entry mode: increment automatically
        self.clear()

    def _write_cmd(self, val):
        with self.i2c_device as i2c:
            self.buf[0] = val
            i2c.write(self.buf)

    def _pulse_enable(self, val):
        self._write_cmd(val | 0x04)  # Enable high
        time.sleep(0.0005)
        self._write_cmd(val & ~0x04) # Enable low
        time.sleep(0.0005)

    def _write_4bit(self, value):
        self._pulse_enable(value | self.backlight)

    def send(self, value, mode):
        # High nibble
        self._write_4bit((value & 0xF0) | mode)
        # Low nibble
        self._write_4bit(((value << 4) & 0xF0) | mode)

    def command(self, value):
        self.send(value, 0x00) # RS = 0 for commands

    def write_char(self, value):
        self.send(value, 0x01) # RS = 1 for data

    def clear(self):
        self.command(0x01) # Clear display
        time.sleep(0.002)

    def message(self, text):
        for char in text:
            if char == '\n':
                self.command(0xC0)  # Move cursor to line 2
            else:
                self.write_char(ord(char))

# --- Main Hardware Initialization ---
# Initialize I2C on GP26 (SDA) and GP27 (SCL)
i2c_bus = busio.I2C(scl=board.GP27, sda=board.GP26)

print("Initializing PCF8574 LCD...")
try:
    lcd = PCF8574_LCD(i2c_bus, address=0x27)
    print("LCD Initialized Successfully!")

    # Run loop test
    while True:
        lcd.clear()
        lcd.message("RP2040-Zero\nHello CircuitPy!")
        time.sleep(1)

        lcd.clear()
        lcd.message("Line 0 Test\nLine 1 Test")
        time.sleep(1)

except Exception as e:
    print(f"Error starting LCD: {e}")
