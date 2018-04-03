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
speech = Speech()
cam_centre = int(cam.cam_width/2)
# global variables
height_threshold = 35
cam_offset = 12

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
                turn.adjust_angle(cam, shape,tol=range(cam_centre-cam_offset,cam_centre+cam_offset))
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
    arm.run_timed(speed_sp=-400, time_sp=20000)
    sleep(20+12)
    pourer.timedDescent(speed=50,time=5000)
    sleep(5)
    arm.run_timed(speed_sp=600, time_sp=13400)
    sleep(13.4)
    pourer.timedLift(time=5000)
    sleep(5)

########## code segment #########
#speech.say("Hello and welcome to the demo")

#sleep(3)

# receive shape from user
#speech.say("please present card").wait()

# make sure gripper is open before searching for a bottle
openGripper()
sleep(2)
gripper.stop()

# make sure wheels are stopped
ev3proxy.motors_stop()

# gets shape from the user
# TODO: change to speech class method
# shape = cam.get_desired_shape()

# using speech class to get users selection of drink

#drink_option = speech.get_drink_option()
drink_option = "WATER"

# TODO: drinks option to shape
drink_to_shape = {'WATER': 'heart', 'MEDICINE': 'triangle', 'LEMONADE': 'circle'}
shape =  'heart'
#drink_to_shape[drink_option]

print(shape)
speech.say("Now searching for bottle with shape " + shape)
sleep(2)

# lift gripper out of the way of camera
pourer.timedLift(4000)
speech.say("raising bottle")
sleep(4)

# start pid to move robot pass camera so pid can check for shape as it travels
pid = run.Popen(["python3", "XNO_pid_slow.py"])

# activate camera to detect shape user has presented
x = None
i = 0
while x is None:
    x, height = cam.stream_and_detect(wantedShape=shape, showStream=False, multiThread=False)
    print("shape detected: " + str(x))
    # changes thresh holds for bottle approach and bottle align
    if (height is not None )and height < height_threshold:
        x = None
    if atStartSensor.value() == 2:
        speech.say("Sorry, I haven't found your bottle.")

# kill PID process on brick when camera finds bottle stop motors all they will still run
pid.kill()
ev3proxy.motors_stop()

# turns robot to bottle
print("Adjusting angle of robot to face bottle.")
speech.say("I am readjusting my position to face the bottle of {}.".format(drink_option))
turn.adjust_angle(cam, shape, tol=range(cam_centre-cam_offset,cam_centre+cam_offset), time_to_run=100)

speech.say("I am now facing the bottle.")
sleep(4)

# move towards bottle
approach_bottle(shape)
speech.say("I have approached the bottle.")

# initialise slow approach after alignment
turn.adjust_angle(cam, shape, tol=range(cam_centre-6,cam_centre+6))

sleep(1)
# open gripper
openGripper()

# return gripper to lowest point
pourer.stopPourer()
print("lowering gripper")
sleep(3)

speech.say("I am now coming closer to the bottle.")
# slow approach code
slow_approach()

# grip bottle
closeGripper()
speech.say("I am holding the bottle of {} and will bring it to you shortly.".format(drink_option))

# wait until bottle is gripped before lifting
sleep(2)
print("lifting bottle")

# lift bottle out of the way of ultra sonic sensor
pourer.liftPourer()

sleep(13)

speech.say("I will now return with the bottle to the black line.")

# go back to line
turn.goBack2Phase(motors_power=80)
ev3proxy.motors_stop()

# run pid to go around loop, using fast pid
pid = run.Popen(["python3", "XNO_pid.py"])

speech.say("I am now back to the black line coming back to pour the {} for you.".format(drink_option))

# wait until pid returns us to the start
# indicated by the blue tape marker
while not (atStartSensor.value() == 2):
    pass

# stop pid that is running arround the loop
ev3proxy.motors_stop()
pid.kill()
ev3proxy.motors_stop()

speech.say("Now I will open the bottle.")

# extend opener arm to remove the bottle gap then
openBottle()
speech.say("I have opened the bottle. Now I will pour you some {}.".format(drink_option))
sleep(3)

print("pouring")

# when back at pouring area initialise pouring
pourer.pour_it()

# wait for pouring to complete
sleep(11)

speech.say("I have poured you a glass of {}. Enjoy!".format(drink_option))

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

speech.say("I am back to my starting position.")

# return pouring platform
pourer.stopPourer()

sleep(2)

# open gripper
openGripper()
gripper.stop()

print("bottle returned")
sleep(1)

speech.say("It was my pleasure to serve you. I am YARR - Your Assistive Rehydration Robot. Thank you for using me")

# clean up code
cam.destroy_camera()
