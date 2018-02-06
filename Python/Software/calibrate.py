# !/usr/bin/env python3
from ev3dev.ev3 import *
from time import time, sleep


def getMaxReflVal():
	f = open("calibration.txt", 'r')
	message = f.read()
	nums = message.split(',')
	maxRef = int(nums[1])
	if maxRef is None:
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
	            Sound.speak("Reading failed. Trying again.")
	            sleep(3)
	        else:
	            break

	    Sound.speak("Max reflective value read.")
	    sleep(4)
	    return max_ref
	return maxRef

def getMinReflVal():
	f = open("calibration.txt", 'r')
	message = f.read()
	nums = message.split(',')
	minRef = int(nums[0])
	if minRef is not None:
	    while True:
	        Sound.speak("Present black card.")
	        sleep(4)
	        min_ref = 100

	        end_time = time() + 1.5
	        while time() < end_time:
	            read = cline.value()
	            if read < min_ref:
	                min_ref = read
	        if min_ref > 10:
	            Sound.speak("Reading failed. Trying again.")
	            sleep(3)
	        else:
	            break

	    Sound.speak("Min reflective value read.")
	    sleep(2)
	    return min_ref
	return minRef


def write(minRef, maxRef):
	f = open("calibration.txt", 'w')
	f.write(str(minRef) + ',' + str(maxRef))
	f.close()
	Sound.speak("Thank you for calibrating.")	

def calibrate():
	write(getMinReflVal(),getMaxReflVal())
	return(getMinReflVal(),getMaxReflVal())

