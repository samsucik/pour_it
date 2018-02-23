#remote python call setup
import ev3dev.ev3 as ev3
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3
import time

gripper = ev3.MediumMotor("outC")
touchSensor = ev3.TouchSensor()
rightM = ev3.LargeMotor('outA')
leftM = ev3.LargeMotor('outD')

def driveForward(speed):
    rightM.run_forever(speed_sp=speed)
    leftM.run_forever(speed_sp=speed)

def driveBackward(speed):
    rightM.run_forever(speed_sp=speed)
    leftM.run_forever(speed_sp=speed)

def turnRight90():
    rightM.run_forever(speed_sp=-200)
    leftM.run_forever(speed_sp=200)

def turnLeft90():
    rightM.run_forever(speed_sp=200)
    leftM.run_forever(speed_sp=-200)


# gripper.run_timed(speed_sp=400, time_sp=2000)
def openGripper():
    gripper.run_forever(speed_sp=-100)

def closeGripper():
    # gripper.ramp_up_sp()
    gripper.run_forever(speed_sp=100)

def waitFortouch():
    while True:
        while touchSensor.value() == 1:
            ev3.Sound.beep()

def stopGripper():
    while True:
        if btn.any():
            gripper.stop()


# -------- Run section -------

# closeGripper()
# time.sleep(3)
# openGripper()
btn = ev3.Button()

# gripper.run_timed(speed_sp=200, time_sp=3000)

while True:
    k = input("input char: ")
    if k == "w":
        openGripper()
    elif k == "s":
        closeGripper()
    elif k == "\x1b[A":
        driveForward(200)
    elif k == "\x1b[B":
        driveBackward(-200)
    elif k == "\x1b[C":
        turnRight90()
    elif k == "\x1b[D":
        turnLeft90()
    else:
        gripper.stop()
        leftM.stop()
        rightM.stop()


# waitFortouch()


