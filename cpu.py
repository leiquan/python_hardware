# 在这里写上你的代码 :-)
import machine,uos


machine.freq(240000000) # set the CPU frequency to 240 MHz

s = machine.freq()          # get the current frequency of the CPU



print(uos.uname())
