import time
import sys
from camera import *

from turn_to_bottle import turn_to_bottle
# from ..Software import forward

# remote python setup
import rpyc
conn = rpyc.classic.connect('ev3dev')
run = conn.modules['subprocess']
ev3 = conn.modules['ev3dev.ev3']

cam = Camera()

gripper = ev3.MediumMotor("outA")
pourer = ev3.LargeMotor('outB')
leftM = ev3.LargeMotor('outC')
rightM = ev3.LargeMotor('outD')
uhead = ev3.UltrasonicSensor('in1')

# set up camera, setup turning
# cam.capture_custom_shapes()
cam.load_custom_shapes()
print("before turn bottle")
turn = turn_to_bottle()

def openGripper():
    gripper.run_forever(speed_sp=-100)

def closeGripper():
    # gripper.ramp_up_sp()
    gripper.run_forever(speed_sp=100)

# move to turn_to_bottle class
def approach_bottle(shape):
    rightM.run_forever(speed_sp=100)
    leftM.run_forever(speed_sp=100)

    # If within 10 centimeters stop
    while uhead.distance_centimeters > 10:
        x, _ = cam.stream_and_detect(wantedShape=shape, showStream=True, continuousStream=False, timeToRun=1)
        if x is not None:
            # re-adjust alignment if shape moves more than 5 centers either way
            if x < 75 or x > 85:
                rightM.stop()
                leftM.stop()
                turn.adjust_angle(cam, shape)
                leftM.run_timed(speed_sp=100, time_sp=200)
                time.sleep(1)
                rightM.run_forever(speed_sp=100)
                leftM.run_forever(speed_sp=100)

    rightM.stop()
    leftM.stop()

########## code segment #########

# receive shape from user
ev3.Sound.speak("please present card").wait()

shape = cam.get_desired_shape()

print(shape)
ev3.Sound.speak("Your shape was " + shape)
time.sleep(4)
ev3.Sound.speak("please remove card")
time.sleep(2)

# start pid to move robot pass camera so pid can check for shape as it travels
pid = run.Popen(["python3", "forward.py"])

# activate camera to detect shape user has presented
x = None
i = 0
while x is None:
    x, height = cam.stream_and_detect(wantedShape=shape, showStream=True)
    print("shape detected: " + str(x))
    if ((x is not None) and i < 2 ):
        i += 1
        x = None
    if (height is not None )and height < 13:
        x = None

# kill PID process on brick when camera finds bottle stop motors all they will still run
pid.kill()
leftM.stop()
rightM.stop()

# turns robot to bottle
print("WE ARE HERE")
turn.adjust_angle(cam, shape)

ev3.Sound.speak("aligned with bottle")
time.sleep(4)

# move towards bottle
approach_bottle(shape)
ev3.Sound.speak("bottle approached")

# initialise slow approach after alignment
# turn.adjust_angle(cam, shape)
# slow approach code

# check for proximity within 1cm

# grip bottle

# lift bottle out of the way of ultra sonic sensor

# go back to line
# turn.goBackUntilLine(motors_power=80, break_value=60)

# run pid to go around loop

# when back at pouring area initialise pouring

time.sleep(2)
ev3.Sound.speak("opening gripper")
openGripper()
time.sleep(2)
# return to line

# run PID back to start around the loop

# clean up code
cam.destroy_camera()
