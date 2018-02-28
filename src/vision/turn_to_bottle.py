# !/usr/bin/env python3
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3
from time import time, sleep
import math
import sys
import json

class turn_to_bottle:

    def __init__(self):
        self.leftM = ev3.LargeMotor('outB')
        self.rightM = ev3.LargeMotor('outA')
        self.cline = ev3.ColorSensor('in4')
        self.cline.mode = 'COL-REFLECT'
        self.leftM.run_direct()
        self.rightM.run_direct()
        self.ultrasonic = ev3.UltrasonicSensor()
        self.camera_aspect_width = 160
        self.base_speed = 0
        self.turn_speed_boost = 50
        self.leftm = []
        self.rightm = []

    #returns speed multiplier for the motor to ramp up
    def step_turn(self,x_coord):
        proportion = float((x_coord/float(self.camera_aspect_width))*100)
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
            return 1.0*(proportion-50)/10
        elif (proportion >= 60) and (proportion < 80):
            return 1
        elif (proportion >= 80) and (proportion < 90):
            return 1*((10-(proportion-80))/10)
        elif (proportion >= 90) and (proportion <= 100):
            return 1*((proportion-90)/10)
        else:
            return 0

    def drive(self,force):
        speed_rightM = self.base_speed
        speed_leftM = self.base_speed
        if force >= 0:
            speed_leftM = self.base_speed + (force*self.turn_speed_boost)
        else:
            speed_rightM = self.base_speed + (force*self.turn_speed_boost)

        self.rightM.run_timed(speed_sp=speed_rightM, time_sp=200)
        self.leftM.run_timed(speed_sp=speed_leftM, time_sp=200)
        self.leftm.append(speed_leftM)
        self.rightm.append(speed_rightM)

    def get_motor_speeds(self):
        movements = {
            'rightM': self.rightm,
            'leftM': self.leftm,
        }
        return movements

    def turn_to_bottle(self, pattern_x_coord):
        self.drive(self.step_turn(pattern_x_coord))

    def turn_once(self, x_coord):
        diff = math.fabs(x_coord-(self.camera_aspect_width/2))
        print("Diff: " + str(diff))
        speed_rightM = 0
        speed_leftM = 0
        if x_coord <= self.camera_aspect_width/2:
            speed_rightM = self.base_speed + ( (diff**(0.30))*self.turn_speed_boost)
            if speed_rightM < 80:
                speed_rightM =80
            print("speed Left: " + str(speed_rightM))
        else:
            speed_leftM = self.base_speed + ( (diff**(0.30))*self.turn_speed_boost)
            if speed_leftM < 80:
                speed_leftM = 80
            print("speed right: " + str(speed_leftM))

        self.rightM.run_timed(time_sp=100, speed_sp=int(speed_rightM ))
        self.leftM.run_timed(time_sp=100, speed_sp=int(speed_leftM ))

    def adjust_angle(self, cam, shape):
        # change to finite loop
        while True:
            x = cam.stream_and_detect(wantedShape=shape, showStream=True, continuousStream=False, timeToRun=1.0)
            if x is not None:
                self.turn_once(x)
            print("X: " + str(x))

            # values at which the robot will think its facing bottle directly, 80 is centre
            if x in [80]:
                print("broke")
                break

    def goBackUntilLine(self, motors_power, break_value):
        # self.leftM.run_direct()
        # self.rightM.run_direct()
        # self.leftM.duty_cycle_sp = -motors_power
        # self.rightM.duty_cycle_sp = -motors_power]
        self.leftM.run_forever(speed_sp=-motors_power)
        self.rightM.run_forever(speed_sp=-motors_power)
        while True:
            start_time = time()
            if self.cline.value() <= break_value:
                break
            print('goBackUntilLine loop: ' + str(time() - start_time))
            print(self.cline.value())