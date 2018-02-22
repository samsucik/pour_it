# !/usr/bin/env python3
from ev3dev.ev3 import *
from time import time, sleep

leftM = LargeMotor('outD')
rightM = LargeMotor('outA')


# Color sensor for following the line.
cline = ColorSensor('in2')
cline.mode = 'COL-REFLECT'

# Variable used for detecting a button press ()
btn = Button()

f = open('ReflectiveValsVSTime.txt', "w+")

angles = ['90 degrees', '67.5 degrees', '45 degrees', '22.5 degrees']

for angle in angles:
    Sound.speak(angle)
    while(not btn.any()):
        x = 1
    leftM.run_direct()
    rightM.run_direct()
    leftM.duty_cycle_sp = -30
    rightM.duty_cycle_sp = -30
    start_time = time()
    end_time = start_time + 2.5
    f.write(angle + "\n")
    while(time() < end_time):
        f.write(str(time()) + " " + str(cline.value()) + "\n")
    leftM.stop()
    rightM.stop()

f.close()


