1.使用官方推荐的thonny或者vs code；可以直接从thonny install 或者从官网下载uf2

2.安装扩展：Pico-W-Go；

3.命令面板搜索：pico，点击：config project；可能需要connect；

4.点击底部的run，就能运行；

5.如果丢失链接，拔掉重新插一下，再运行代码；记住，窗口要在当前代码那里，不能打开readme再点击运行，否则会报错；

6.如果要使用自定义的函数库，需要上传到zero上去，可以使用thonny或者底栏的all commands 进行upload；比如这个dht.py库文件，dht11就需要引用他，必须上传到板子上

7.要想启动后自动运行，必须把文件名设置为main.py，必须带后缀


-------------
nRF52840 的xiao，也可以使用Circuit Python 来运行。。。。。已刷，然后可以直接使用mu editor来开发


-------
mu editor 比较友好，可以直接开发circuitpython的 xiao，也可以开发zero（pico）。因此使用这个。也能支持多窗口，比arduino靠谱。唯一的坏处是，circuit的不能直接run。也不能上传文件到zero？【实验证明，不需要上传文件，貌似import会自动引用进去，智能】