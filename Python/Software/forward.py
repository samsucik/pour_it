# !/usr/bin/env python3
from ev3dev.ev3 import *
from time import time, sleep

# Steering2 and the original version of "run" have been taken from: https://github.com/Klabbedi/ev3/blob/master/README.md.

# Motor setup
armM = MediumMotor('outA')
leftM = LargeMotor('outC')
rightM = LargeMotor('outB')

cline = ColorSensor('in3')
cline.mode = 'COL-REFLECT'

carm = ColorSensor('in2')
carm.mode = 'COL-COLOR'

uhead = UltrasonicSensor('in4')

time_for_turn = 7

colours = ['unknown', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown']

power = 30
minRef = 4
maxRef = 77
target = 40  # % of white we want

# PID controller parameters.
kp = float(2)
kd = 1
ki = float(0.5)

direction = -1  # -1 if left side of darker floor, 1 otherwise.

# Color of the bottle the robot must find.
bottle_col = 'black'

# End of the line minimum distance (cm) between ultrasonic sensor and stopping cardboard.
stop_dist_first = 32

btn = Button()

def driveforward(time_, speed):
    rightM.run_timed(time_sp=time_, speed_sp=speed)
    leftM.run_timed(time_sp=time_, speed_sp=speed)

def turnRight90():
    rightM.run_timed(time_sp=1500, speed_sp=-400)
    leftM.run_timed(time_sp=1500, speed_sp=400)


def turnLeft90():
    rightM.run_timed(time_sp=1500, speed_sp=400)
    leftM.run_timed(time_sp=1500, speed_sp=-400)

def getMaxReflVal():
    while True:
        sleep(4)
        Sound.speak("Present white card.")
        sleep(4)
        max_ref = 0

        end_time = time() + 1.5
        while time() < end_time:
            read = cline.value()
            if read > max_ref:
                max_ref = read

        if max_ref < 70:
            Sound.speak("Reading failed. Trying again.")
            sleep(3)
        else:
            break

    Sound.speak("Max reflective value read.")
    sleep(4)
    return max_ref

def getMinReflVal():
    while True:
        Sound.speak("Present black card.")
        sleep(4)
        min_ref = 100

        end_time = time() + 1.5
        while time() < end_time:
            read = cline.value()
            if read < min_ref:
                min_ref = read
        if min_ref > 10:
            Sound.speak("Reading failed. Trying again.")
            sleep(3)
        else:
            break

    Sound.speak("Min reflective value read.")
    sleep(2)
    return min_ref


def steering2(course, power):
    if course >= 0:
        if course > 100:
            power_right = 0
            power_left = power
        else:
            power_left = power
            power_right = power - ((power * course) / 100)
    else:
        if course < -100:
            power_left = 0
            power_right = power
        else:
            power_right = power
            power_left = power + ((power * course) / 100)
    return (int(power_left), int(power_right))


# Hardcoded turn for when the robot finds the correct bottle and needs to turn.
def goBackAndTurn():
    rightM.run_timed(time_sp=1200, speed_sp=-200)
    leftM.run_timed(time_sp=1200, speed_sp=-200)
    sleep(1.5)
    leftM.run_timed(time_sp=1050,speed_sp=400)
    sleep(1)
    rightM.run_forever(speed_sp=300)
    leftM.run_forever(speed_sp=300)
    while(True):
        if(uhead.distance_centimeters <= 5):
            leftM.stop()
            rightM.stop()
            break


def runTimed(timeRun, power, target, kp, kd, ki, direction, minRef, maxRef):
    lastError = error = integral = 0
    leftM.run_direct()
    rightM.run_direct()
    end_time = time() + timeRun
    while (not btn.any() and time() < end_time):
        refRead = cline.value()

        # Is it ok if refRead-minRef will be negative?
        error = target - (100 * (refRead - minRef) / (maxRef - minRef))
        derivative = error - lastError
        lastError = error
        integral = float(0.5) * integral + error
        course = (kp * error + kd * derivative + ki * integral) * direction
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Aprox 100Hz

def runDemo(time_for_turn, minDist, power, target, kp, kd, ki, direction, minRef, maxRef):
    print("Reached runDemo")
    lastError = error = integral = 0
    leftM.run_direct()
    rightM.run_direct()
    while (not btn.any() and carm.value() != bottle_col and uhead.distance_centimeters > minDist):
        refRead = cline.value()
        error = target - (100 * (refRead - minRef) / (maxRef - minRef))
        derivative = error - lastError
        lastError = error
        integral = float(0.5) * integral + error
        course = (kp * error + kd * derivative + ki * integral) * direction
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Approx 100Hz
    leftM.stop()
    rightM.stop()
    if(carm.value() == bottle_col):
        armM.run_timed(time_sp=600,speed_sp=200)
        goBackAndTurn()
    elif(uhead.distance_centimeters <= minDist):
        armM.run_timed(time_sp=600,speed_sp=200)
        sleep(2)
        runUntilStart(time_for_turn,5,power,target,kp,kd,ki,direction,minRef,maxRef)

def runUntilStart(time_for_turn,minDist,power,target,kp,kd,ki,direction,minRef,maxRef):
    print("Reached runUntilStart")
    lastError = error = integral = 0
    leftM.run_direct()
    rightM.run_direct()
    end_time = time() + time_for_turn
    while (not btn.any() and (time() < end_time or uhead.distance_centimeters > minDist)):
        refRead = cline.value()
        # Is it ok if refRead-minRef will be negative?
        error = target - (100 * (refRead - minRef) / (maxRef - minRef))
        derivative = error - lastError
        lastError = error
        integral = float(0.5) * integral + error
        course = (kp * error + kd * derivative + ki * integral) * direction
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Aprox 100Hz
    rightM.stop()
    leftM.stop()

#################### Start of script.
Sound.speak("Starting calibration.")
sleep(2)

# Getting + setting the min and max reflective values.
maxRef = getMaxReflVal()
minRef = getMinReflVal()

# Calibration succeeded.

sleep(2)
Sound.speak("Provide colored card.")
sleep(3)

# Must make sure arm is in correct position?

# Wait for input on control sensor.
while True:

    while carm.value() == 0:
        print("No color inputted")
        sleep(1)

    usr_col = carm.value()

    Sound.speak("Your color was " + colours[usr_col])
    sleep(3)
    Sound.speak("Confirm color")
    sleep(3)

    while carm.value() == 0:
        print("No color inputted")
        sleep(1)

    confirm_val = carm.value()

    if confirm_val == usr_col:
        Sound.speak("Colours match")
        bottle_col = confirm_val # set color of bottle that needs to be found
        sleep(1)
        break
    else:
        Sound.speak("Colours do not match")
        sleep(2)

armM.run_timed(time_sp=600, speed_sp=-200)
sleep(3)

# Move along line of bottles and stop when either the sensor detects the stopping sign or the color sensor detects the
# correct color.
runDemo(time_for_turn, stop_dist_first, power, target, kp, kd, ki, direction, minRef, maxRef)























