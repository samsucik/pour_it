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
ev3proxy = conn.modules['ev3_proxy']

cam = Camera()

gripper = ev3.MediumMotor("outA")
pourer = ev3.LargeMotor('outB')
leftM = ev3.LargeMotor('outC')
rightM = ev3.LargeMotor('outD')
uhead = ev3.UltrasonicSensor()


# set up camera, setup turning
# cam.capture_custom_shapes()
cam.load_custom_shapes()
print("before turn bottle")
turn = turn_to_bottle()

def openGripper():
    gripper.run_forever(speed_sp=-100)

def closeGripper():
    gripper.run_forever(speed_sp=100)

# move to turn_to_bottle class
def approach_bottle(shape):
    ev3proxy.motors_run(speed=50)

    # If within 10 centimeters stop
    # make more harsh on pi
    while uhead.distance_centimeters > 12:
        x, _ = cam.stream_and_detect(wantedShape=shape, showStream=True, continuousStream=False, timeToRun=1)
        if x is not None:
            # re-adjust alignment if shape moves more than 5 centers either way
            if x < 77 or x > 83:
                ev3proxy.motors_stop()
                turn.adjust_angle(cam, shape)
                # leftM.run_timed(speed_sp=100, time_sp=200)
                time.sleep(1)
                ev3proxy.motors_run(speed=100)
    ev3proxy.motors_stop()

def slow_approach():
    ev3proxy.motors_run(speed=25)

    while not uhead.distance_centimeters == 255:
        True

    ev3proxy.motors_stop()

########## code segment #########

# receive shape from user
ev3.Sound.speak("please present card").wait()

# make sure gripper is open before searching for a bottle
openGripper()
time.sleep(2)
gripper.stop()

leftM.stop()
rightM.stop()

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
    x, height = cam.stream_and_detect(wantedShape=shape, showStream=True,multiThread=False)
    print("shape detected: " + str(x))
    if ((x is not None) and i < 2 ):
        i += 1
        x = None
    # changes thresh holds for bottle approach and bottle align
    if (height is not None )and height < 11:
        x = None

# kill PID process on brick when camera finds bottle stop motors all they will still run
pid.kill()
ev3proxy.motors_stop()

# turns robot to bottle
print("adjusting angle of robot to face bottle")
turn.adjust_angle(cam, shape)

ev3.Sound.speak("aligned with bottle")
time.sleep(4)

# move towards bottle
approach_bottle(shape)
ev3.Sound.speak("bottle approached")

# initialise slow approach after alignment
turn.adjust_angle(cam, shape, tol=range(79, 82), time_to_run=100)

# open gripper
openGripper()

# slow approach code
slow_approach()

# grip bottle
closeGripper()

time.sleep(1)

# lift bottle out of the way of ultra sonic sensor
pourer.run_forever(speed_sp=-50)
time.sleep(10)
pourer.stop(stop_action="brake")

# go back to line
turn.goBack2Phase(motors_power=80)
ev3proxy.motors_stop()


# run pid to go around loop
pid = run.Popen(["python3", "forward.py"])

# when back at pouring area initialise pouring

# clean up code
cam.destroy_camera()
