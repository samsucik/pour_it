# !/usr/bin/env python3
# from ev3dev.ev3 import *
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3
from time import time, sleep

leftM = ev3.LargeMotor('outB')
rightM = ev3.LargeMotor('outA')


# Color sensor for following the line.
cline = ev3.ColorSensor('in4')
cline.mode = 'COL-REFLECT'

# Variable used for detecting a button press ()
btn = ev3.Button()

f = open('ReflectiveValsVSTime.txt', "w+")
powers = [20,30,40,50]
angles = ['90 degrees', '67.5 degrees', '45 degrees', '22.5 degrees']


for power in powers:
    f.write('power: ' + str(power) + "\n")
    ev3.Sound.speak(power)
    for angle in angles:
        sleep(1)
        ev3.Sound.speak(angle)
        while(not btn.any()):
            x = 1
        leftM.run_direct()
        rightM.run_direct()
        leftM.duty_cycle_sp = -power
        rightM.duty_cycle_sp = -power
        start_time = time()
        end_time = start_time + 2.5
        f.write(angle + "\n")
        while(time() < end_time):
            f.write(str(time()) + " " + str(cline.value()) + "\n")
        leftM.stop()
        rightM.stop()

f.close()