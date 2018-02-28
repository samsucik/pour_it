import time
from camera import *
from turn_to_bottle import turn_to_bottle
# from ..Software import forward

# remote python setup
import rpyc
conn = rpyc.classic.connect('ev3dev')
run = conn.modules['subprocess']
ev3 = conn.modules['ev3dev.ev3']

cam = Camera()

print("here")
leftM = ev3.LargeMotor('outB')
rightM = ev3.LargeMotor('outA')
uhead = ev3.UltrasonicSensor('in1')

# move to turn_to_bottle class
def approach_bottle():
    rightM.run_forever(speed_sp=100)
    leftM.run_forever(speed_sp=100)

    while uhead.distance_centimeters > 10:
        x = cam.stream_and_detect(wantedShape='circle', showStream=True, continuousStream=False, timeToRun=1)
        if x < 70 or x > 90:
            rightM.stop()
            leftM.stop()
            turn.adjust_angle(cam)
            rightM.run_forever(speed_sp=100)
            leftM.run_forever(speed_sp=100)

    rightM.stop()
    leftM.stop()

# set up camera, setup turning
# cam.capture_custom_shapes()
cam.load_custom_shapes()
print("before turn bottle")
turn = turn_to_bottle()


# receive shape from user
ev3.Sound.speak("please present card").wait()
shape = None
while shape is None:
    print("waiting on shape")
    shape = cam.read_shape_from_card()
    print(shape)

print(shape)
ev3.Sound.speak("Your shape was" + shape)
time.sleep(4)
ev3.Sound.speak("please remove card")
time.sleep(2)

# start pid to move robot pass camera so pid can check for shape as it travels
pid = run.Popen(["python3", "forward.py"])

# activate camera to detect shape user has presented

x = None
while x is not None:
    print(x)
    x = cam.stream_and_detect(wantedShape=shape, showStream=True)

# kill PID process on brick when camera finds bottle stop motors all they will still run
pid.kill()
leftM.stop()
rightM.stop()

#turns robot to bottle needs bottles
turn.adjust_angle(cam, shape)

# move towards bottle
# approach_bottle()

# return to line

# run PID back to start around the loop

# clean up cod
cam.destroy_camera()
