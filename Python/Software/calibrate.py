# !/usr/bin/env python3
from ev3dev.ev3 import *
from time import time, sleep
import os

def getMaxReflVal(cline):
    if os.path.isfile("/home/robot/calibration.txt"):
        f = open("calibration.txt", 'r')
        message = f.read()
        nums = message.split(',')
        maxRef = int(nums[1])

        return maxRef
    else:
        while True:
            sleep(4)
            Sound.speak("Present white card.")
            sleep(4)
            max_ref = 0

            end_time = time() + 1.5
            while time() < end_time:
                read = cline.value()
            if read > max_ref:
                max_ref = read

            if max_ref < 70:
                sleep(3)
                Sound.speak("Reading failed. Trying again.")
                sleep(3)
            else:
                break
        sleep(4)
        Sound.speak("Max reflective value read.")
        sleep(4)
        return max_ref

def getMinReflVal(cline):
    if os.path.isfile("/home/robot/calibration.txt"):
        f = open("calibration.txt", 'r')
        message = f.read()
        nums = message.split(',')
        minRef = int(nums[0])
        return minRef
    else:
        while True:
            sleep(4)
            Sound.speak("Present black card.")
            sleep(4)
            min_ref = 100

            end_time = time() + 1.5
            while time() < end_time:
                read = cline.value()
                if read < min_ref:
                    min_ref = read

            if min_ref > 10:
                sleep(3)
                Sound.speak("Reading failed. Trying again.")
                sleep(3)
            else:
                break

        sleep(4)
        Sound.speak("Min reflective value read.")
        sleep(4)
        return min_ref


def write(minRef, maxRef):
    f = open("calibration.txt", 'w')
    f.write(str(minRef) + ',' + str(maxRef))
    f.close()

def calibrate(cline):
    minreflval = getMinReflVal(cline)
    maxreflval = getMaxReflVal(cline)

    if not os.path.isfile("/home/robot/calibration.txt"):
        write(minreflval,maxreflval)

    sleep(2)
    Sound.speak("calibration finished")
    sleep(4)
    return(minreflval,maxreflval)

