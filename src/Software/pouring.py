#remote python call setup
import rpyc
conn = rpyc.classic.connect('ev3dev2.local') #host name or IP address of EV3
brick2 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3

from time import  sleep

class Pouring:

    def __init__(self):
        self.pourer = brick2.LargeMotor('outB')
        self.gripper = brick2.MediumMotor('outA')
        self.touchSensor = brick2.TouchSensor()

    def startPouring(self):
        self.pourer.run_forever(speed_sp=-50)

    def timedLift(self, time):
        self.pourer.run_timed(speed_sp=-50,time_sp=time)

    def timedDescent(self,speed,time):
        self.pourer.run_timed(speed_sp=speed,time_sp=time)

    def stopPourer(self):
        print("STOP Pourer")
        self.pourer.run_forever(speed_sp=50)
        while True:
            if self.touchSensor.value() == 1:
                self.pourer.stop()
                print("pourer stopped")
                break

    def liftPourer(self):
        self.pourer.run_timed(time_sp=11300, speed_sp=-50, stop_action="hold")

    def pour_it(self):
        self.pourer.run_timed(time_sp=9000, speed_sp=-70)
        sleep(9)
        self.pourer.run_timed(time_sp=9000, speed_sp=70)

if __name__ == '__main__':
    p = Pouring()
    p.gripper.run_forever(speed_sp=-200)
    sleep(1)
    p.gripper.run_forever(speed_sp=200)
    sleep(1)
    print("lift pourer")
    p.liftPourer()
    sleep(13)
    print("pouring")
    p.pour_it()
    sleep(12)
    print("return to initial position")
    p.stopPourer()
    sleep(5)
    p.gripper.stop()
