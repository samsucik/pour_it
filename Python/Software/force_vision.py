'''
force vision is an attempt to make the robot move towards the bottle in a curved way so that it avoids other bottles
and ends up facing directly at the middle of the bottle.
The idea is that the correctly recognised symbol for the bottle will exert a 'force' on the robot that is 
proportional to it's distance away from the robot and the position of the bottle in the camera's field of view.
In this way, the closer the robot gets to the bottle the bigger the force and the sharper the turn until the
bottle is centered in the robot's field of view thus exerting the maximum 'force'. the robot will be attracted to the 
bottle until the ultrasonic sensor says that it is close enough to pick up the bottle.
'''
# !/usr/bin/env python3
from ev3dev.ev3 import *
from time import time, sleep
import math
import sys

leftM = LargeMotor('outC')
rightM = LargeMotor('outB')
camera_aspect_width = 160
# standard deviation changes the sharpness of the turn (needs tuning)
#sd = 0.1
def sigmoid(x):
  return (1 / (1 + math.exp(-(x)))) - 0.5
'''
def normal_distribution(x):
    x_centered = x-(camera_aspect_width/2)
    mean = 0
    y = (1/(sd*math.sqrt(2*math.pi)))*math.e*(-((x_centered-mean)*(x_centered-mean)/2*(sd*sd)))
    return y
'''
def force_on_robot(pattern_x_coord, pattern_size):
    # analogous with light intensity
    pattern_intensity = 1/pattern_size
    # model as normal distribution with zero mean to give direction robot should turn
    distance_from_center = math.fabs(pattern_x_coord-80)
    if distance_from_center == 0 : distance_from_center += 0.000001
    force = pattern_intensity * (1/(distance_from_center))
    # make force positive if object on the right
    if (pattern_x_coord > camera_aspect_width/2): force = -(math.fabs(force))
    return force

def sine_mode(x_coord):
    if x_coord<=(camera_aspect_width/2):
        motor_speed_boost = math.sin(4*(x_coord-24))+1.1
    else:
        motor_speed_boost = -math.sin(4*(x_coord-24))+1.1    
    
    return motor_speed_boost

def drive(force):
    base_speed = 200
    speed_leftM = base_speed - force*100
    speed_rightM = base_speed + force*100     
    #rightM.run_timed(time_sp=100, speed_sp=speed_rightM)
    #leftM.run_timed(time_sp=100, speed_sp=speed_leftM)
    print("left motor speed: " + str(speed_leftM))
    print("right motor speed: " + str(speed_rightM))

#print(force_on_robot(float(sys.argv[1]),float(sys.argv[2])))

for x in xrange(80,0):
    drive(sine_mode(x))

