#remote python call setup
import rpyc
conn = rpyc.classic.connect('ev3dev2.local') #host name or IP address of EV3
brick2 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3

from time import  sleep

class Pouring:

    def __init__(self):
        self.pourer = brick2.LargeMotor('outB')
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
        self.pourer.run_timed(time_sp=11000, speed_sp=-50)

    def pour_it(self):
        self.pourer.run_timed(time_sp=5000, speed_sp=-70)
        sleep(7)
        self.pourer.run_timed(time_sp=5000, speed_sp=70)

if __name__ == '__main__':
    p = Pouring()
    #print("lift pourer")
    #p.liftPourer()
    #sleep(13)
    #print("pouring")
    #p.pour_it()
    #sleep(14)
    print("return to initial position")
    p.stopPourer()
