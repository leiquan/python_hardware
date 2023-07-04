# 在手机上安装 Serial Bluetooth Terminal 这款 APP，用来测试蓝牙数据交互：开关灯的命令从 Android 手机发出，树莓派 Pico 收到每条命令之后，相应地打开或关闭 LED。
# 在尚未與裝置連線之前，HC-05板子上的LED將快速閃爍；若進入AT模式，LED將慢速閃爍（兩秒閃爍一次）。HC-05的AT命令，採用38400bps的速率傳送。
# 筆者購買的HC-05板子上面有一個按鍵，根據廠商提供的電路，這個按鍵接在藍牙模組的34腳：
# 所以先按著板子上的開關，再通電，即可讓此藍牙模組進入AT模式（通電之後，即可放開開關）。
# https://swf.com.tw/?p=712&cpage=1


# 问号指令表示查询
import uos
import machine
import utime

print(uos.uname())  # 列出開發板的資訊
uart0 = machine.UART(0, baudrate=38400)  # 38400 专门用于at模式通信


def sendCMD_waitResp(cmd, uart=uart0):
    print("CMD: " + cmd)
    uart.write(cmd)
    waitResp(uart)
    print()


def waitResp(uart=uart0):

    resp = b""
    if uart.any():
            resp = b"".join([resp, uart.read(1)])

    print(resp)
    return resp


print(uart0)
print("- uart0 -")

waitResp()


sendCMD_waitResp("AT\r\n")  # 测试指令
sendCMD_waitResp("AT+NAMEcloth\r\n")  # 设置名字
sendCMD_waitResp("AT+ROLE=0\r\n")  # 设置从机模式
sendCMD_waitResp("AT+NAME?\r\n")  # 查询名字
sendCMD_waitResp("AT+VERSION?\r\n")  # 顯示藍芽版本
sendCMD_waitResp("AT+UART?\r\n")  # 顯示設定速率
sendCMD_waitResp("AT+UART?\r\n")  # 顯示設定速率
sendCMD_waitResp("AT+ROLE?\r\n")  # 顯示角色，0為Slave，1為Master
sendCMD_waitResp("AT+CMODE?\r\n")  # 查詢目前工作模式
sendCMD_waitResp("AT+ADDR?\r\n")  # 顯示藍芽位址
sendCMD_waitResp("AT+RESET\r\n")  # 重置蓝牙模块


print("Done")
