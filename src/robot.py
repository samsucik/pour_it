# This is meant to be the core of our robot.
# 
# It can be run on an EV3 brick as well as on
# a PC. In the latter case, it will use a tweaked
# version of the modified ev3dev package by Timon
# Reinold (see https://gitlab.com/ev3py/ev3py-runlocal).
# This enables us to do lots of SW testing while 
# not running the code directly on the EV3.

import sys, os
import logging

import ev3dev
from ev3dev.ev3 import *

import global_stuff

def init():
    logger.debug("Setting up the robot. Using environment: '{}'.".format(global_stuff.ENV))
    m1 = MediumMotor('outA')
    m1.run_timed(time_sp=600, speed_sp=-200)
    logger.info(ev3dev.__package__)
    c1 = ColorSensor('in2')
    c1.mode = 'COL-COLOR'
    n = c1.value(n=0)

class Robot():
    def __init__():
        pass

if __name__ == "__main__":
    if sys.version_info < (3,4):
        raise SystemError('Must be using Python 3.4 or higher')
    
    script_path = os.path.dirname(os.path.abspath( __file__ ))
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s]: %(message)s')
    global_stuff.LOGGER = logging.getLogger('rbt')
    global logger
    logger = global_stuff.LOGGER

    if script_path.startswith('/home/robot/'):
        logging.info("Running on real EV3 brick.")
        init()
    else:
        logging.info("Running on a PC.")
    
        if len(sys.argv) < 2:
            raise NameError("Provide environment [DEV, TEST] when running this script.")
        else:
            if sys.argv[1] == 'TEST':
                global_stuff.ENV = 'TEST'
            elif sys.argv[1] == 'DEV':
                global_stuff.ENV = 'DEV'
            else:
                raise NameError("Provided environment {} not recognised. Use 'DEV' or 'TEST'".format(sys.argv[1]))    
        init()