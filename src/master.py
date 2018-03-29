from time import sleep
import sys
from vision.camera import *
from Software.pouring import *
from Software.turn_to_bottle import *

# remote python setup
import rpyc
conn = rpyc.classic.connect('ev3dev.local')
run = conn.modules['subprocess']
ev3 = conn.modules['ev3dev.ev3']

ev3proxy = conn.modules['ev3_proxy']

def test_opener()
    opener_motor = ev3.MediumMotor('outA')
    arm_motor = ev3.MediumMotor('outB')
    pourer = ev3.LargeMotor('outC') 
    arm_motor.run_timed(speed_sp=200, time_sp=1000)
    # opener_motor.run_timed(speed_sp=200, time_sp=1000)
    # pourer.run_timed(time_sp=14000, speed_sp=-50)


test_opener()
sys.exit(0)

cam = Camera()

gripper = ev3.MediumMotor("outA")
leftM = ev3.LargeMotor('outC')
rightM = ev3.LargeMotor('outD')
uhead = ev3.UltrasonicSensor()
atStartSensor = ev3.ColorSensor('in4')
atStartSensor.mode = 'COL-COLOR'
# for color sensor in mode 'COL_COLOR' the following values are true for its output
# 0=unknown, 1=black, 2=blue, 3=green, 4=yellow, 5=red, 6=white, 7=brown

# set up camera, setup turning
# cam.capture_custom_shapes()
cam.load_custom_shapes()
print("before turn bottle")
turn = turn_to_bottle()
pourer = Pouring()

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
                sleep(1)
                ev3proxy.motors_run(speed=100)
    ev3proxy.motors_stop()

def slow_approach():
    ev3proxy.motors_run(speed=25)

    while not uhead.distance_centimeters == 255:
        pass

    ev3proxy.motors_stop()

########## code segment #########
ev3.Sound.speak("Hello and welcome to the demo")

sleep(3)

# receive shape from user
ev3.Sound.speak("please present card").wait()

# make sure gripper is open before searching for a bottle
openGripper()
sleep(2)
gripper.stop()

leftM.stop()
rightM.stop()

shape = cam.get_desired_shape()

print(shape)
ev3.Sound.speak("Your shape was " + shape)
sleep(4)
ev3.Sound.speak("please remove card")
sleep(2)

# start pid to move robot pass camera so pid can check for shape as it travels
pid = run.Popen(["python3", "XNO_pid_slow.py"])

# activate camera to detect shape user has presented
x = None
i = 0
# TODO: add check of colour sensor in the loo so that if it does not detect a shape
while x is None:
    x, height = cam.stream_and_detect(wantedShape=shape, showStream=False,multiThread=False)
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
sleep(4)

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

# wait until bottle is gripped before lifting
sleep(1)
ev3.Sound.speak("lifting bottle")

# lift bottle out of the way of ultra sonic sensor
pourer.liftPourer()

sleep(13)

ev3.Sound.speak("moving back to line")

# go back to line
turn.goBack2Phase(motors_power=80)
ev3proxy.motors_stop()

# run pid to go around loop, using fast pid
pid = run.Popen(["python3", "XNO_pid.py"])

# wait until pid returns us to the start
# indicated by the blue tape marker
while not (atStartSensor.value() == 2):
    pass

# stop pid that is running arround the loop
ev3proxy.motors_stop()
pid.kill()
ev3proxy.motors_stop()

ev3.Sound.speak("pouring")
# when back at pouring area initialise pouring
pourer.pour_it()

# wait for pouring to complete
sleep(11)

ev3.Sound.speak("returning to start")

# restart fast pid to return to starting position
pid = run.Popen(["python3", "XNO_pid.py"])

# value of 5 equals red
# wait until red marker is seen 
while not(atStartSensor.value() == 5):
    pass

# stop motors and kill
ev3proxy.motors_stop()
pid.kill()
ev3proxy.motors_stop()

ev3.Sound.speak("returned to start and lowering bottle")

# return pouring platform
pourer.stopPourer()

sleep(2)

# open gripper
openGripper()
gripper.stop()

ev3.Sound.speak("bottle returned")
sleep(2)

ev3.Sound.speak("I'm finished. UGHHHHHHH").wait()

# clean up code
cam.destroy_camera()
