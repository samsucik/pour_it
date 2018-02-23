# !/usr/bin/env python3
from ev3dev.ev3 import *
from time import time, sleep

rightM = LargeMotor('outB')
leftM = LargeMotor('outC')
sensor = ColorSensor('in3')
sensor.mode = 'COL-REFLECT'


def driveForward(time, speed):
    rightM.run_timed(time_sp=time, speed_sp=speed)
    leftM.run_timed(time_sp=time, speed_sp=speed)


def turnRight90():
    rightM.run_timed(time_sp=1500, speed_sp=-400)
    leftM.run_timed(time_sp=1500, speed_sp=400)


def turnLeft90():
    rightM.run_timed(time_sp=1500, speed_sp=400)
    leftM.run_timed(time_sp=1500, speed_sp=-400)


# The following code has been taken from: https://github.com/Klabbedi/ev3/blob/master/README.md


def setReflectiveVals():
    # leftM.run_timed(time_sp=1500,speed_sp=-400)
    # rightM.run_timed(time_sp=1500,speed_sp=-400)
    max_ref = 0
    min_ref = 100
    end_time = time() + 1.5
    while time() < end_time:
        read = sensor.value()
        if max_ref < read:
            max_ref = read
        if min_ref > read:
            min_ref = read
        if max_ref > 90:
            leftM.stop()
            rightM.stop()
    leftM.stop()
    rightM.stop()
    print('Max: ' + str(max_ref))
    print('Min: ' + str(min_ref))
    sleep(1)

power = 30
minRef = 4
maxRef = 77
target = 40  # % of white we want

# PID controller parameters.
kp = float(0.65)
kd = 0
ki = float(0)

direction = -1  # -1 if left side of darker floor, 1 otherwise.

btn = Button()


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


def run(power, target, kp, kd, ki, direction, minRef, maxRef):
    lastError = error = integral = 0
    leftM.run_direct()
    rightM.run_direct()
    end_time = time() + 4
    while (not btn.any() and time() < end_time):
        refRead = sensor.value()

        # Is it ok if refRead-minRef will be negative?
        error = target - (100 * (refRead - minRef) / (maxRef - minRef))
        derivative = error - lastError
        lastError = error
        integral = float(0.5) * integral + error
        course = (kp * error + kd * derivative + ki * integral) * direction
        for (motor, pow) in zip((leftM, rightM), steering2(course, power)):
            motor.duty_cycle_sp = pow
        sleep(0.01)  # Aprox 100Hz

run(power, target, kp, kd, ki, direction, minRef, maxRef)
# setReflectiveVals()  # Uncomment for setting new reflection values.
print('Stopping motors')
leftM.stop()
rightM.stop()
