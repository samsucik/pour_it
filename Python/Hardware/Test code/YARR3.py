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
c2.mode = 'COL-COLOR'
c1.mode = 'COL-COLOR'

colours = ['unknown', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown']

def driveForward(time, speed):
    rightM.run_timed(time_sp=time, speed_sp=speed)
    leftM.run_timed(time_sp=time, speed_sp=speed)

def turnRight90():
    rightM.run_timed(time_sp=1500, speed_sp=-400)
    leftM.run_timed(time_sp=1500, speed_sp=400)

def turnLeft90():
    rightM.run_timed(time_sp=1500, speed_sp=400)
    leftM.run_timed(time_sp=1500, speed_sp=-400)

while colours[c1.value()] == 'unknown' or  colours[c1.value()] == 'black':
    print("color not selected")
    time.sleep(1)

chosen = colours[c1.value()]
time.sleep(1)

print("colour choosen", chosen)
Sound.speak(chosen)
time.sleep(1)

print("Motor A is connected:", m1.connected)
print("Color senor mode: ", c1.mode)

# put camera arm camera arm down and
m1.run_timed(time_sp=600, speed_sp=-200)
time.sleep(1)
driveForward(5000,500)

# Stop when chosen colour is found by second colour sensor
while not ((colours[c2.value()] == 'unknown') or (colours[c2.value()] == 'black')):
    print(c2.value())
print(colours[c2.value()])
Sound.speak("Thank you")

leftM.stop()
rightM.stop()
time.sleep(2)
turnRight90()
m1.run_timed(time_sp=600, speed_sp=200)
