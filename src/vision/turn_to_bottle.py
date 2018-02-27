# !/usr/bin/env python3
from ev3dev.ev3 import *
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3
from time import time, sleep
import math
import sys
import json

leftM = ev3.LargeMotor('outC')
rightM = ev3.LargeMotor('outB')
ultrasonic = ev3.UltrasonicSensor('in4')
camera_aspect_width = 160
base_speed = 100
turn_speed_boost = 100
leftm = []
rightm = []

#returns speed multiplier for the motor to ramp up
def step_turn(x_coord):
    proportion = float((x_coord/float(camera_aspect_width))*100)
    print(x_coord)
    print(proportion)
    if (proportion >= 0) and (proportion < 10):
        return -1*((10-proportion)/10)
    elif (proportion >= 10) and (proportion < 20):
        return -(1.0*((proportion-10)/10))
    elif (proportion >= 20) and (proportion < 40):
        return -1
    elif (proportion >= 40) and (proportion < 50):
        return -(1.0*((10-(proportion-40))/10))
    elif (proportion >= 50) and (proportion < 60):
        return (1.0*((proportion-50)/10))
    elif (proportion >= 60) and (proportion < 80):
        return 1
    elif (proportion >= 80) and (proportion < 90):
        return 1*((10-(proportion-80))/10)
    elif (proportion >= 90) and (proportion <= 100):
        return 1*((proportion-90)/10)
    else:
        return 0

def drive(force):
    if force >= 0:
        speed_leftM = base_speed + (force*turn_speed_boost)
        speed_rightM = base_speed 
    else:
        speed_leftM = base_speed 
        speed_rightM = base_speed - (force*turn_speed_boost)     
         
    rightM.run_timed(time_sp=100, speed_sp=speed_rightM)
    leftM.run_timed(time_sp=100, speed_sp=speed_leftM).wait_while('running')
    leftm.append(speed_leftM)
    rightm.append(speed_rightM)

def get_motor_speeds():
    movements = {
        'rightM': rightm,
        'leftM': leftm,
    }
    return movements

def turn_to_bottle(pattern_x_coord):
    drive(step_turn(pattern_x_coord))
