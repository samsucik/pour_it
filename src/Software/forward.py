# !/usr/bin/env python3
from time import time, sleep
# import ev3dev.ev3 as ev3
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3
import calibrate

# Steering2 and the original version of "run" have been taken from: https://github.com/Klabbedi/ev3/blob/master/README.md.

############################# SETUP + VARIABLES ########################################################################
# Motors setup.
#armM = MedsiumMotor('outA')
leftM = ev3.LargeMotor('outB')
rightM = ev3.LargeMotor('outA')

# Color sensor for following the line.
cline = ev3.ColorSensor('in4')
cline.mode = 'COL-REFLECT'

# Color sensor for detecting colored card + correct bottle.
#carm = ColorSensor('in2')
#carm.mode = 'COL-COLOR'

# Ultrasonic sensor for detecting the beginning and end of the track.
uhead = ev3.UltrasonicSensor('in1')

# Time for the robot to make the turn at the end (ultrasonic sensor's detection is paused during this time).
time_for_turn = 7

colours = ['unknown', 'black', 'blue', 'green', 'yellow', 'red', 'white', 'brown']

# Controls the base power to each one of the large motors.
power = 30

# Minimum and maximum reflected light intensity values.
minRef = 4
maxRef = 77

# % of white we want as the target (for the PID controller's error calculation).
target = 70

# PID controller parameters (need to be re-tuned if the robot changes drastically in the future demos).
# kp = float(2)
# kd = 1
# ki = float(0.5)
kp = float(0.7)
ki = float(0.6)
kd = 4

# -1 if the robot will follow the left side of the black line, 1 otherwise (part of the PID controller).
direction = -1

# Colored bottle the robot needs to find.
bottle_col = 0

# End of the line minimum distance (cm) between ultrasonic sensor and margin of our workspace.
stop_dist_first = 32
stop_dist_second = 5

# Dictionary for PID modes:
mode_PID = {}

# Variable used for detecting a button press ()
btn = ev3.Button()

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
        ev3.Sound.speak("Present white card.")
        sleep(4)
        max_ref = 0

        end_time = time() + 1.5
        while time() < end_time:
            read = cline.value()
            if read > max_ref:
                max_ref = read

        if max_ref < 70:
            ev3.Sound.speak("Reading failed. Trying again.")
            sleep(3)
        else:
            break

    ev3.Sound.speak("Max reflective value read.")
    sleep(4)
    return max_ref

def getMinReflVal():
    while True:
        ev3.Sound.speak("Present black card.")
        sleep(4)
        min_ref = 100

        end_time = time() + 1.5
        while time() < end_time:
            read = cline.value()
            if read < min_ref:
                min_ref = read
        if min_ref > 10:
            ev3.Sound.speak("Reading failed. Trying again.")
            sleep(3)
        else:
            break

    ev3.Sound.speak("Min reflective value read.")
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
    rightM.run_timed(time_sp=1150, speed_sp=-200)
    leftM.run_timed(time_sp=1150, speed_sp=-200)
    sleep(2)
    leftM.run_timed(time_sp=1750,speed_sp=200)
    sleep(2)
    rightM.run_forever(speed_sp=200)
    leftM.run_forever(speed_sp=200)
    while(not(btn.any())):
        if(uhead.distance_centimeters <= 5):
            leftM.stop()
            rightM.stop()
            break

# args[0] = end_time
# args[1] = start_time
# returns 1 if a button was pressed.
# returns 2 if execution time was exceeded.
def timedCondition(args):
    if(not btn.any() and time() - args[1] < args[0]):
        return 0
    elif(time() - args[1] >= args[0]):
        return 2
    else:
        return 1

##################NEXT 2 CONDITIONS SHOULD BE REWRITTEN IF NEEDED##################################################

# args[0] = waiting_time, args[1] = minDist, args[2] = leftM, args[3] = rightM
def runUntilStartCondition(args):
    if(uhead.distance_centimeters < args[1]):
        args[2].stop()
        args[3].stop()
        sleep(args[0])
        if(uhead.distance_centimeters < args[1]):
            return 0
        else:
            args[2].run_direct()
            args[3].run_direct()
            return 1
    elif(btn.any()):
        return 0
    else:
        return 2

def createPIDmodes():
    mode_PID['timed'] = timedCondition
    mode_PID['runUntilStart'] = runUntilStartCondition

# mode and params:
# 'timed' -> args[0] = time() + amount of time you want it to run for.
#
def generalPIDRun(mode, power, target, direction, kp, kd, ki, minRef, maxRef, *args, **kwargs):
    print('FML')

    createPIDmodes()

    lastError = error = integral = 0

    # This mode will allow us to change the speed of the motors immediately.
    leftM.run_direct()
    rightM.run_direct()

    while(not mode_PID[mode](args)):
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

    leftM.stop()
    rightM.stop()

    return 0

def run(power, target, kp, kd, ki, direction, minRef, maxRef):
    lastError = error = integral = 0
    leftM.run_direct()
    rightM.run_direct()
    end_time = time() + 4
    while (not btn.any()):
        refRead = cline.value()

        # Is it ok if refRead-minRef will be negative?
        error = target - (100 * (refRead - minRef) / (maxRef - minRef))
        derivative = error - lastError
        lastError = error

        # If the error changes sign, reset the accumulated error.
        if(error * lastError < 0):
            integral = 0
        else:
            integral = float(0.5) * integral + error


        course = (kp * error + kd * derivative + ki * integral) * direction
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Aprox 100Hz
    leftM.stop()
    rightM.stop()

# Method for setting bottle_col.
# def presentColoredCard():
#     sleep(2)
#
#     # Wait for input on control sensor.
#     while True:
#
#         ev3.Sound.speak("Provide colored card.")
#         sleep(3)
#
#         while carm.value() == 0 or carm.value() == 1:
#             print("No color inputted")
#             sleep(1)
#
#         usr_col = carm.value()
#
#         ev3.Sound.speak("Your color was " + colours[usr_col])
#         sleep(3)
#         ev3.Sound.speak("Confirm color")
#         sleep(3)
#
#         while carm.value() == 0 or carm.value()==1:
#             print("No color inputted")
#             sleep(1)
#
#         confirm_val = carm.value()
#
#         if confirm_val == usr_col:
#             ev3.Sound.speak("Colours match")
#             global bottle_col
#             bottle_col = confirm_val # set color of bottle that needs to be found
#             sleep(2.5)
#             break
#         else:
#             ev3.Sound.speak("Colours do not match").wait()
#             sleep(2)

#################### Start of script ################

(minRef,maxRef) = calibrate.calibrate(cline)
(minRef,maxRef) = (10,73)

###################################################TESTING REACHING BLACK LINE AGAIN + RETURNING########################
run(power, target, kp, kd, ki, direction, minRef, maxRef)
#
# from rwJSON import rwJSON
#
# writejson = rwJSON()
#
# motorSpeeds = [(30,0),(30,30),(30,0),(30,30)]
#
# for (left_sp,right_sp) in motorSpeeds:
#
#     leftM.run_timed(time_sp = 1500,duty_cycle_sp = left_sp)
#     rightM.run_timed(time_sp = 1500, duty_cycle_sp = right_sp)
#     writejson.addCommand(left_sp,right_sp,1500)
#     sleep(1.6)
#
# writejson.saveCommands('commands')
#
# def goBackUntilLine():
#     commandList = rwJSON.readCommands('commands')
#     index = 0
#     while(cline.value() > 20 and index < len(commandList)):
#         leftM.run_timed(time_sp = commandList[index]['time'], duty_cycle_sp = -commandList[index]['left_sp'])
#         rightM.run_timed(time_sp = commandList[index]['time'], duty_cycle_sp = -commandList[index]['right_sp'])
#         startTime = time()
#         while(time() < startTime + commandList[index]['time']):
#             if(cline.value() < 20):
#                 leftM.stop()
#                 rightM.stop()
#                 break
#         if(cline.value() < 20):
#             leftM.stop()
#             rightM.stop()
#             break
#         else:
#             index += 1
#     if(cline.value() > 20):
#         leftM.stop()
#         rightM.stop()
#         print('goBackUntilLine FAILED')
#     else:
#         generalPIDRun('runUntilStart', power, target, direction, kp, kd, ki, minRef, maxRef, 3, 10, leftM, rightM)
#
# goBackUntilLine()




