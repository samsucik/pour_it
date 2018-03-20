# !/usr/bin/env python3
from time import time, sleep
import ev3dev.ev3 as ev3
from PID_NN import PID_NN
#import rpyc
#conn = rpyc.classic.connect('ev3dev') #host name or IP address of EV3
#ev3 = conn.modules['ev3dev.ev3'] #import ev3dev.ev3
import calibrate

# Steering2 and the original version of "run" have been taken from: https://github.com/Klabbedi/ev3/blob/master/README.md.

############################# SETUP + VARIABLES ########################################################################
class PID:
    def __init__(self):

        # Motors setup.
        self.leftM = ev3.LargeMotor('outC')
        self.rightM = ev3.LargeMotor('outD')

        # Color sensor for following the line.
        self.cline = ev3.ColorSensor('in2')
        self.cline.mode = 'COL-REFLECT'

        # Ultrasonic sensor for detecting the beginning and end of the track.
        self.uhead = ev3.UltrasonicSensor()

        # Controls the base power to each one of the large motors.
        self.power = 50

        # Minimum and maximum reflected light intensity values.
        self.minRef = 10
        self.maxRef = 86

        # % of white we want as the target (for the PID controller's error calculation).
        self.target = 55

        self.kp = float(0.9)
        self.ki = float(0.7)
        self.kd = float(10)

        # -1 if the robot will follow the left side of the black line, 1 otherwise (part of the PID controller).
        self.direction = -1

        self.waiting_time = 3
        self.stop_dist_cm = 13
        self.mode = 'runForever'

        # Dictionary for PID modes:
        self.mode_PID = {}

        # Variable used for detecting a button press ()
        self.btn = ev3.Button()

        self.weights_path = 'weights.txt'
        self.sensor_reads_path = 'sensor_inputs.txt'
        self.backup_path = 'backup.txt'
        self.pid_nn = PID_NN(0.01,self.target/float(100),self.weights_path,self.sensor_reads_path,self.backup_path)

        self.weights = self.pid_nn.read_weights()

    def train_NN(self,epochs=20):
        for i in range(1,epochs+1):
            self.pid_nn = PID_NN(0.05,self.target/float(100),self.weights_path,self.sensor_reads_path,self.backup_path)
            self.weights = self.pid_nn.weights
            if(self.run_NN_PID_train()):
                ev3.Sound.speak('Training model; epoch ' + str(i))
                self.pid_nn.train_model()
                sleep(2)
            if(i < epochs):
                ev3.Sound.speak("Press any button to continue training.")
                while(not btn.any()):
                    pass
            else:
                ev3.Sound.speak("Training complete")
    
    def squash_output(self,value):
        if(value < -1):
            return -1
        elif(value > 1):
            return 1
        else:
            return value

    # The robot runs until a button is pressed. 
    # Then, the reads are saved in "sensor_inputs.txt".
    def run_NN_PID_train(self):
        # self.prev_row[0] = previous I neuron input;
        # self.prev_row[1] = previous D neuron input;
        self.prev_row = [0,0]
        reads = []

        self.rightM.run_direct()
        self.leftM.run_direct()

        target = self.target/float(100)

        while(not self.btn.any()):
            refRead = self.cline.value()

            # Normalized read.
            normRead = (refRead - self.minRef) / (self.maxRef - self.minRef)
            reads.append(normRead)

            # Calculate course using the weights:
            P_input = self.weights[11] * target + self.weights[21] * normRead
            P_output = self.squash_output(P_input)
            
            I_input = self.weights[12] * target + self.weights[22] * normRead
            I_output = 0
            if(-1 <= I_input and I_input <= 1):
                I_output = I_input + self.prev_row[0]
            else:
                I_output = self.squash_output(I_input)
            self.prev_row[0] = I_input

            D_input = self.weights[13] * target + self.weights[23] * normRead
            D_output = 0
            if(-1 <= D_input and D_input <= 1):
                D_output = D_input - self.prev_row[1]
            else:
                D_output = self.squash_output(D_input)
            self.prev_row[1] = D_input

            course = self.squash_output(self.weights[1] * P_output + self.weights[2] * I_output + self.weights[3] * D_output)

            # Calculate the power each motor should be given and pass it to them.
            for (motor, pow) in zip((self.leftM, self.rightM), self.steering2(course, self.power)):
                motor.duty_cycle_sp = pow
            sleep(0.01)  # Approx 100Hz
            returnVal = self.mode_PID[self.mode](args)
        
        self.leftM.stop()
        self.rightM.stop()

        f = open(self.sensor_reads_path,'w')
        for value in reads:
            f.write(value)
        f.close()

        return True
            
        






    # course = determines how hard and in which direction the robot should turn in order to keep following the line.
    # course = calculated using kp,ki,kd
    # power = reference power we give to the wheels
    def steering2(self,course, power):
        if course >= 0:
            if course > 1:
                power_right = 0
                power_left = power
            else:
                power_left = power
                power_right = power - (power * course)
        else:
            if course < -1:
                power_left = 0
                power_right = power
            else:
                power_right = power
                power_left = power + (power * course)
        return (int(power_left), int(power_right))

    # args[0] = end_time
    # args[1] = start_time
    # returns 1 if a button was pressed.
    # returns 2 if execution time was exceeded.
    def timedCondition(self,args):
        if(not self.btn.any() and time() - args[1] < args[0]):
            return 0
        elif(time() - args[1] >= args[0]):
            return 2
        else:
            return 1

    # args[0] = waiting_time, args[1] = min_dist, args[2] = leftM, args[3] = rightM
    def runUntilStartCondition(self,args):
        if(self.uhead.distance_centimeters <= args[1]):
            args[2].stop()
            args[3].stop()
            start_time = time()
            while(time() < start_time + args[0]):
                if(self.uhead.distance_centimeters > args[1]):
                    args[2].run_direct()
                    args[3].run_direct()
                    return 0
            return 1
        elif(self.btn.any()):
            return 2
        else:
            return 0

    def runForeverCondition(self,args):
        return 0

    def createPIDmodes(self):
        self.mode_PID['runUntilStart'] = self.runUntilStartCondition
        self.mode_PID['runForever'] = self.runForeverCondition


    def generalPIDRun(self, *args, **kwargs):

        self.createPIDmodes()

        lastError = error = integral = 0

        # This mode will allow us to change the speed of the motors immediately.
        self.leftM.run_direct()
        self.rightM.run_direct()
        returnVal = 0
        while(not returnVal):
            refRead = self.cline.value()

            # Calculate the current error and its derivative.
            error = self.target - (100 * (refRead - self.minRef) / (self.maxRef - self.minRef))
            error = error/float(100)
            derivative = error - lastError
            lastError = error

            # If the error changes sign, reset the accumulated error.
            if(error * lastError < 0):
                integral = 0
            else:
                integral = float(0.5) * integral + error

            # PID controller.
            course = (self.kp * error + self.kd * derivative + self.ki * integral) * self.direction

            # Calculate the power each motor should be given and pass it to them.
            for (motor, pow) in zip((self.leftM, self.rightM), self.steering2(course, self.power)):
                motor.duty_cycle_sp = pow
            sleep(0.01)  # Approx 100Hz
            returnVal = self.mode_PID[self.mode](args)

        self.leftM.stop()
        self.rightM.stop()

        return returnVal

    # def run(self):
    #     lastError = error = integral = 0
    #     self.leftM.run_direct()
    #     self.rightM.run_direct()
    #     start_time = time()
    #     while (not self.btn.any()):
    #         checkpoint_time = time()
    #
    #         refRead = self.cline.value()
    #
    #         # Is it ok if refRead-minRef will be negative?
    #         error = self.target - (100 * (refRead - self.minRef) / (self.maxRef - self.minRef))
    #         error = error/float(100)
    #         derivative = error - lastError
    #         lastError = error
    #
    #         # If the error changes sign, reset the accumulated error.
    #         if(error * lastError < 0):
    #             integral = 0
    #         else:
    #             integral = float(0.5) * integral + error
    #
    #         course = (self.kp * error + self.kd * derivative + self.ki * integral) * self.direction
    #         for (motor, pow) in zip((self.leftM, self.rightM), self.steering2(course, self.power)):
    #             motor.duty_cycle_sp = pow
    #         sleep(0.05)
    #         print(time() - checkpoint_time)


        self.leftM.stop()
        self.rightM.stop()

if __name__ == "__main__":
    PID_obj = PID()
     # args[0] = waiting_time, args[1] = min_dist, args[2] = leftM, args[3] = rightM
    PID_obj.mode = "runForever"
    PID_obj.train_NN()
    # PID_obj.generalPIDRun(PID_obj.waiting_time,PID_obj.stop_dist_cm,PID_obj.leftM,PID_obj.rightM)
