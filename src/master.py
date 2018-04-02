from time import sleep
import sys
from vision.camera import *
from Software.pouring import *
from Software.turn_to_bottle import *
from speech.Speech import *

# remote python setup
import rpyc

# setup connection to main motor control brick
#host name or IP address of EV3
conn1 = rpyc.classic.connect('ev3dev1.local')
conn2 = rpyc.classic.connect('ev3dev2.local')
brick1 = conn1.modules['ev3dev.ev3']
brick2 = conn2.modules['ev3dev.ev3']
run = conn2.modules['subprocess']
ev3proxy = conn2.modules['ev3_proxy']

######## brick 1 objects ########
arm = brick1.MediumMotor("outD")
opener = brick1.MediumMotor("outC")

######### brick 2 objects #######
gripper = brick2.MediumMotor("outA")
leftM = brick2.LargeMotor('outC')
rightM = brick2.LargeMotor('outD')
uhead = brick2.UltrasonicSensor()
atStartSensor = brick2.ColorSensor('in4')

# for color sensor in mode 'COL_COLOR' the following values are true for its output
# 0=unknown, 1=black, 2=blue, 3=green, 4=yellow, 5=red, 6=white, 7=brown
atStartSensor.mode = 'COL-COLOR'

# component objects created

# set up camera, setup turning, setup pouring
# cam.capture_custom_shapes()
cam = Camera()
cam.load_custom_shapes()
turn = turn_to_bottle()
pourer = Pouring()
speechRecog = Speech()

# global variables
height_threshold = 40
cam_offset = 15

def openGripper():
    gripper.run_forever(speed_sp=-100)

def closeGripper():
    gripper.run_forever(speed_sp=100)

# move to turn_to_bottle class
def approach_bottle(shape):
    ev3proxy.motors_run(speed=50)
    # If within 10 centimeters stop
    # make more harsh on pi
    print ("In bottle approach")
    while uhead.distance_centimeters > 12:
        print("Still approaching")
        x, _ = cam.stream_and_detect(wantedShape=shape, showStream=True, continuousStream=False, timeToRun=1)
        if x is not None:
            # re-adjust alignment if shape moves more than 5 centers either way
            print()
            if x < cam.cam_width - cam_offset or x > cam.cam_width + cam_offset:
                print("re-aligning to bottle")
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

def openBottle():
    opener.run_timed(speed_sp=800, time_sp=(20000+12000))
    arm.run_timed(speed_sp=400, time_sp=20000)
    sleep(20+12)
    pourer.run_timed(speed_sp=50, time_sp=5000)
    sleep(5)
    arm.run_timed(speed_sp=-600, time_sp=13400)
    sleep(13.4)

########## code segment #########
#brick2.Sound.speak("Hello and welcome to the demo")

#sleep(3)

# receive shape from user
#brick2.Sound.speak("please present card").wait()

# make sure gripper is open before searching for a bottle
#openGripper()
#sleep(2)
#gripper.stop()

# make sure wheels are stopped
#ev3proxy.motors_stop()

# gets shape from the user
# TODO: change to speech class method
# shape = cam.get_desired_shape()

# using speech class to get users selection of drink
drink_option = speechRecog.get_drink_option()

# TODO: drinks option to shape
drink_to_shape = {'WATER': 'heart', 'MEDICINE': 'triangle', 'LEMONADE': 'circle'}
shape = drink_to_shape[drink_option]

print(shape)
brick2.Sound.speak("Your shape was " + shape)
sleep(2)

# lift gripper out of the way of camera
pourer.timedLift(2000)

# start pid to move robot pass camera so pid can check for shape as it travels
pid = run.Popen(["python3", "XNO_pid_slow.py"])

# activate camera to detect shape user has presented
x = None
i = 0
while x is None:
    x, height = cam.stream_and_detect(wantedShape=shape, showStream=False, multiThread=False)
    print("shape detected: " + str(x))
    if ((x is not None) and i < 2 ):
        i += 1
        x = None
    # changes thresh holds for bottle approach and bottle align
    if (height is not None )and height < height_threshold:
        x = None
    if atStartSensor.value() == 5:
        brick2.Sound.speak("Your bottle has not been found").wait()
        brick2.Sound.speak("Robot has finished")
        sys.exit(0)

# kill PID process on brick when camera finds bottle stop motors all they will still run
pid.kill()
ev3proxy.motors_stop()

# turns robot to bottle
print("adjusting angle of robot to face bottle")
turn.adjust_angle(cam, shape)

brick2.Sound.speak("aligned with bottle")
sleep(4)

# move towards bottle
approach_bottle(shape)
brick2.Sound.speak("bottle approached")

# initialise slow approach after alignment
turn.adjust_angle(cam, shape, tol=range(cam.cam_width-cam_offset,cam.cam_width+cam_offset), time_to_run=100)

# open gripper
openGripper()

# return gripper to lowest point
pourer.stopPourer()

# slow approach code
slow_approach()

# grip bottle
closeGripper()

# wait until bottle is gripped before lifting
sleep(1)
brick2.Sound.speak("lifting bottle")

# lift bottle out of the way of ultra sonic sensor
pourer.liftPourer()

sleep(13)

brick2.Sound.speak("moving back to line")

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

# extend opener arm to remove the bottle gap then
openBottle()

brick2.Sound.speak("pouring")
# when back at pouring area initialise pouring
pourer.pour_it()

# wait for pouring to complete
sleep(11)

brick2.Sound.speak("returning to start")

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

brick2.Sound.speak("returned to start and lowering bottle")

# return pouring platform
pourer.stopPourer()

sleep(2)

# open gripper
openGripper()
gripper.stop()

brick2.Sound.speak("bottle returned")
sleep(1)

brick2.Sound.speak("I'm finished. UGHHHHHHH").wait()

# clean up code
cam.destroy_camera()
