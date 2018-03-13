#remote python call setup
import rpyc
conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3

from time import  sleep

class Pouring:

    def __init__(self):
        self.gripper = ev3.MediumMotor("outA")
        self.pourer = ev3.LargeMotor('outB')
        self.touchSensor = ev3.TouchSensor()

    def openGripper(self):
        self.gripper.run_forever(speed_sp=-100)

    def closeGripper(self):
        self.gripper.run_forever(speed_sp=200)

    def startPouring(self):
        self.pourer.run_forever(speed_sp=-50)

    def stopPourer(self):
        k = True
        while k == True:
            while self.touchSensor.value(0) and (k == True):
                self.pourer.stop()
                k = False

    def liftPourer(self):
        self.pourer.run_timed(time_sp=14000, speed_sp=-50)

    def pour_it(self):
        self.pourer.run_timed(time_sp=5000, speed_sp=-70)
        sleep(7)
        self.pourer.run_timed(time_sp=5000, speed_sp=70)

    # def returnPourer(self):
    #     self.gripper.run_forever(speed_sp=200)
    #     self.pourer.run_forever(speed_sp=50)
    #     self.stopPourer()



if __name__ == '__main__':
    p = Pouring()
    p.liftPourer()
