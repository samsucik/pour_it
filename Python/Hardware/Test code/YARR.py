# !/usr/bin/env python3
from ev3dev.ev3 import *
import time

# Motor setup
m1 = MediumMotor('outA')
rightM = LargeMotor('outB')
leftM = LargeMotor('outC')

# colour setup
c1 = ColorSensor('in2')
c2 = ColorSensor('in3')


# setting ,mode for color sensors  to return values 0-7
c2.mode('COL-COLOR')
c1.mode('COL-COLOR')

colours = ['unknown', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown']

while colours[c1.value()] == 'unknown':
    print("color not selected")
    time.sleep(1)

chosen = c1.value()
time.sleep(1)

print("colour choosen", chosen)
Sound.speak(colours[c1.value()])
time.sleep(1)

print("Motor A is connected:", m1.connected)
print("Color senor mode: ", c1.mode)

# put camera arm camera arm down and
m1.run_timed(time_sp=600, speed_sp=-200)
time.sleep(1)
leftM.run_timed(time_sp=5000, speed_sp=900)
rightM.run_timed(time_sp=5000, speed_sp=900)

# Stop when chosen colour is found by second colour sensor
while not (c2.value() == chosen):
    print("help!!")

Sound.speak("Thank you")

leftM.stop()
rightM.stop()
time.sleep(2)
m1.run_timed(time_sp=600, speed_sp=200)
time.sleep(2)
leftM.run_timed(time_sp=1500, speed_sp=500)
