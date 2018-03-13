import ev3dev.ev3  as ev3

class EV3Proxy:
    def __init__(self):
        self.leftM = ev3.LargeMotor('outC')
        self.rightM = ev3.LargeMotor('outD')

    def motors_stop(self):
        self.rightM.stop()
        self.leftM.stop()

    def motors_run(self, speed=100):
        self.rightM.run_forever(speed_sp=speed)
        self.leftM.run_forever(speed_sp=speed)


def motors_stop():
    rightM = ev3.LargeMotor('outD')
    leftM = ev3.LargeMotor('outC')
    rightM.stop()
    leftM.stop()

def motors_run(speed=100):
    rightM = ev3.LargeMotor('outD')
    leftM = ev3.LargeMotor('outC')
    rightM.run_forever(speed_sp=speed)
    leftM.run_forever(speed_sp=speed)