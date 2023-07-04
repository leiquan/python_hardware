# 在手机上安装 Serial Bluetooth Terminal 这款 APP，用来测试蓝牙数据交互：开关灯的命令从 Android 手机发出，树莓派 Pico 收到每条命令之后，相应地打开或关闭 LED。
# 在尚未與裝置連線之前，HC-05板子上的LED將快速閃爍；若進入AT模式，LED將慢速閃爍（兩秒閃爍一次）。HC-05的AT命令，採用38400bps的速率傳送。
# 筆者購買的HC-05板子上面有一個按鍵，根據廠商提供的電路，這個按鍵接在藍牙模組的34腳：
# 所以先按著板子上的開關，再通電，即可讓此藍牙模組進入AT模式（通電之後，即可放開開關）。
# https://swf.com.tw/?p=712&cpage=1


# 问号指令表示查询
import uos
import machine

print(uos.uname())  # 列出開發板的資訊
uart = machine.UART(0, baudrate=9600)  # 38400 专门用于at模式通信，之后就要设置9600，不然数据传输会乱码。。。

b = bytes('hello', 'ascii')
uart.write(b)

while True:
    if uart.any() > 0:
        data = uart.read()
        print(data)
