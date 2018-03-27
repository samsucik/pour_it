from ev3dev.ev3 import *
from time import time, sleep


class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

arm_motor = LargeMotor('outA')

getcmd = _Getch()

speed = 25
cmd = getcmd()
if cmd == 'f':
    speed *= 1
elif cmd == 'b':
    speed *= -1
else:
    speed = 0

arm_motor.run_timed(time_sp=100000, speed_sp=speed)
while True:
    print("...")
    sleep(0.1)
    cmd = getcmd()
    # print(">{}<".format(cmd))
    if cmd == 'q':
        arm_motor.stop()
        break
