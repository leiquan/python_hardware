"""让 Seeed Studio XIAO nRF52840 的板载 LED 持续闪烁。"""

import time
import board
import digitalio


print("--- 串口连接测试开始 ---")

BLINK_INTERVAL = 0.5  # 亮或灭各保持的时间（秒）


def blink(led, interval):
    """切换 LED 状态，并等待指定时间。"""
    led.value = not led.value
    time.sleep(interval)


led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = False  # 启动时先确保 LED 熄灭

try:
    while True:
        blink(led, BLINK_INTERVAL)
finally:
    led.deinit()  # 程序停止时释放该引脚
