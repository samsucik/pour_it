#remote python call setup
import ev3dev.ev3 as ev3
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3
import time

gripper = ev3.MediumMotor("outA")
touchSensor = ev3.TouchSensor()
# rightM = ev3.LargeMotor('outC')
# leftM = ev3.LargeMotor('outD')
opener = ev3.MediumMotor("outC")
arm = ev3.MediumMotor("outD")
pourer = ev3.LargeMotor('outB')

# def driveForward(speed):
#     rightM.run_forever(speed_sp=speed)
#     leftM.run_forever(speed_sp=speed)
#
# def driveBackward(speed):
#     rightM.run_forever(speed_sp=speed)
#     leftM.run_forever(speed_sp=speed)
#
# def turnRight90():
#     rightM.run_forever(speed_sp=-200)
#     leftM.run_forever(speed_sp=200)
#
# def turnLeft90():
#     rightM.run_forever(speed_sp=200)
#     leftM.run_forever(speed_sp=-200)

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

def startPouring():
    pourer.run_forever(speed_sp=-50)

def returnPourer():
    pourer.run_forever(speed_sp=50)

def armExtend():
    arm.run_forever(speed_sp=-200)

def armReturn():
    arm.run_forever(speed_sp=200)

def openerBottle():
    opener.run_forever(speed_sp=800)

# -------- Run section -------

# closeGripper()
# time.sleep(3)
# openGripper()
btn = ev3.Button()

# gripper.run_timed(speed_sp=200, time_sp=3000)
##### hit enter to stop pourer
while True:
    k = input("input char: ")
    if k == "w":
        openGripper()
    elif k == "s":
        closeGripper()
    elif k == "\x1b[A":
        armExtend()
        # driveForward(200)
    elif k == "\x1b[B":
        armReturn()
        # driveBackward(-200)
    elif k == "\x1b[C":
        pass
        # turnRight90()
    elif k == "\x1b[D":
        pass
        # turnLeft90()
    elif k == "p":
        startPouring()
    elif k == "l":
        returnPourer()
    elif k == "g":
       gripper.stop()
    elif k == "z":
        arm.stop()
    elif k == "q":
        openerBottle()
    else:
        pourer.stop(stop_action="hold")
        opener.stop()
        arm.stop()
        # leftM.stop()
        # rightM.stop()



# waitFortouch()


