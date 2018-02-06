# !/usr/bin/env python3
from ev3dev.ev3 import *
from time import time, sleep

# Steering2 and the original version of "run" have been taken from: https://github.com/Klabbedi/ev3/blob/master/README.md.

# Motors setup.
armM = MediumMotor('outA')
leftM = LargeMotor('outC')
rightM = LargeMotor('outB')

# Color sensor for following the line.
cline = ColorSensor('in3')
cline.mode = 'COL-REFLECT'

# Color sensor for detecting colored card + correct bottle.
carm = ColorSensor('in2')
carm.mode = 'COL-COLOR'

# Ultrasonic sensor for detecting the beginning and end of the track.
uhead = UltrasonicSensor('in4')

# Time for the robot to make the turn at the end (ultrasonic sensor's detection is paused during this time).
time_for_turn = 7

colours = ['unknown', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown']

# Controls the base power to each one of the large motors.
power = 30

# Minimum and maximum reflected light intensity values.
minRef = 4
maxRef = 77

# % of white we want as the target (for the PID controller's error calculation).
target = 40

# PID controller parameters (need to be re-tuned if the robot changes drastically in the future demos).
kp = float(2)
kd = 1
ki = float(0.5)

# -1 if the robot will follow the left side of the black line, 1 otherwise (part of the PID controller).
direction = -1

# Colored bottle the robot needs to find.
bottle_col = 0

# End of the line minimum distance (cm) between ultrasonic sensor and margin of our workspace.
stop_dist_first = 32
stop_dist_second = 5

# Start minimum distance (cm)

# Variable used for detecting a button press ()
btn = Button()

# Makes the robot drive forward for time_, with speed.
def driveForward(time_, speed):
    rightM.run_timed(time_sp=time_, speed_sp=speed)
    leftM.run_timed(time_sp=time_, speed_sp=speed)

# Hard-coded right turn (mainly for testing).
def turnRight90():
    rightM.run_timed(time_sp=1500, speed_sp=-400)
    leftM.run_timed(time_sp=1500, speed_sp=400)

# Hard-coded left turn (mainly for testing).
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

# course = determines how hard and in which direction the robot should turn in order to keep following the line.
# course = calculated using kp,ki,kd
# power = reference power we give to the wheels
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


# Hardcoded turn: called when robot finds the correct bottle and needs to turn.
def goBackAndTurn():
    print("goBackAndTurn: reached")
    rightM.run_timed(time_sp=1200, speed_sp=-200)
    leftM.run_timed(time_sp=1200, speed_sp=-200)
    sleep(2)
    leftM.run_timed(time_sp=1050,speed_sp=400)
    sleep(2)
    rightM.run_forever(speed_sp=300)
    leftM.run_forever(speed_sp=300)
    while(not(btn.any())):
        if(uhead.distance_centimeters <= 5):
            leftM.stop()
            rightM.stop()
            break

# Make the robot follow the line for a set amount of time.
def runTimed(timeRun, power, target, kp, kd, ki, direction, minRef, maxRef):
    print("runTimed: reached")
    lastError = error = integral = 0
    leftM.run_direct()
    rightM.run_direct()
    end_time = time() + timeRun
    while (not btn.any() and time() < end_time):
        print("runTimed: loop " + time())
        refRead = cline.value()

        # Is it ok if refRead-minRef will be negative?
        error = target - (100 * (refRead - minRef) / (maxRef - minRef))
        derivative = error - lastError
        lastError = error
        if(error * lastError < 0):
            integral = 0
        else:
            integral = float(0.5) * integral + error
        course = (kp * error + kd * derivative + ki * integral) * direction
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Aprox 100Hz

# The following method will be run after the colored card has been confirmed.
# runDemo is the only variant of run which will be thoroughly commented.
def runDemo(time_for_turn, minDist1, minDist2, power, target, kp, kd, ki, direction, minRef, maxRef):
    print("runDemo: reached")
    lastError = error = integral = 0

    # This mode will allow us to change the speed of the motors immediately.
    leftM.run_direct()
    rightM.run_direct()

    # "switch" for figuring out why the robot stopped.
    sw = 0

    # Run loop as long as no button has been pressed.
    while (not btn.any()):
        print("runDemo: main loop")
        # Break loop if the color sensor has detected the correct bottle.
        if(carm.value() == bottle_col):
            sw = 1
            break
        # Break loop if the robot has reached the end of the line of bottles.
        if(uhead.distance_centimeters <= minDist1):
            sw = 2
            break

        # Read the current reflected light intensity.
        refRead = cline.value()

        # Calculate the current error and its derivative.
        error = target - (100 * (refRead - minRef) / (maxRef - minRef))
        derivative = error - lastError
        lastError = error

        # If the error changes sign, reset the accumulated error.
        if(error * lastError < 0):
            integral = 0
        else:
            integral = float(0.5) * integral + error

        # PID controller.
        course = (kp * error + kd * derivative + ki * integral) * direction

        # Calculate the power each motor should be given and pass it to them.
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Approx 100Hz
    # If the loop was broken, stop both motors and retract the arm.
    leftM.stop()
    rightM.stop()
    armM.run_timed(time_sp=600, speed_sp=200)
    sleep(1)
    # If the bottle is detected, go back and turn towards it.
    if(sw == 1):
        print("runDemo: bottle detected")
        goBackAndTurn()
    # If the end of the line was reached, call the "runUntilStart" method.
    elif(sw == 2):
        print("runDemo: end of line reached")
        sleep(2)
        runUntilStart(time_for_turn,minDist2,power,target,kp,kd,ki,direction,minRef,maxRef)
    else:
        print("runDemo: execution interrupted by button press")

# This method will be called after the robot reached the end of the line of bottles.
def runUntilStart(time_for_turn, minDist,power,target,kp,kd,ki,direction,minRef,maxRef):
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
        if error * lastError < 0:
            integral = 0
        else:
            integral = float(0.5) * integral + error
        course = (kp * error + kd * derivative + ki * integral) * direction
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Aprox 100Hz
    rightM.stop()
    leftM.stop()

# Method for setting bottle_col.
def presentColoredCard():
    sleep(2)

    # Wait for input on control sensor.
    while True:

        Sound.speak("Provide colored card.")
        sleep(3)

        while carm.value() == 0 or carm.value() == 1:
            print("No color inputted")
            sleep(1)

        usr_col = carm.value()

        Sound.speak("Your color was " + colours[usr_col])
        sleep(3)
        Sound.speak("Confirm color")
        sleep(3)

        while carm.value() == 0 or carm.value()==1:
            print("No color inputted")
            sleep(1)

        confirm_val = carm.value()

        if confirm_val == usr_col:
            Sound.speak("Colours match")
            global bottle_col
            bottle_col = confirm_val # set color of bottle that needs to be found
            sleep(2.5)
            break
        else:
            Sound.speak("Colours do not match")
            sleep(2)

#################### Start of script.
#Sound.speak("Starting calibration.")
#sleep(2)

# Getting + setting the min and max reflective values.
#maxRef = getMaxReflVal()
#minRef = getMinReflVal()

# Calibration succeeded.
presentColoredCard()

armM.run_timed(time_sp=600, speed_sp=-200)
sleep(3)

# Move along line of bottles and stop when either the sensor detects the stopping sign or the color sensor detects the
# correct color.
runDemo(time_for_turn, stop_dist_first, stop_dist_second, power, target, kp, kd, ki, direction, minRef, maxRef)