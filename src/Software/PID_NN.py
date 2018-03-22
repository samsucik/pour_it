from os.path import isfile
import math


class PID_NN:

    # This version has a fixed learning rate -> may need to update it.
    def __init__(self, learning_rate, target, weights_path, sensor_reads_path,  backup_path):
        # same as target in PID, but divided by 100; squash it between 1 and -1 just in case.
        self.target = self.squash_output(target)
        # sensor input values (why compute params twice?) -> not sure how fast the PID loop will do the calculations so I want to keep it as lightweight as possible.
        self.ys = []
        self.params = []  # neuron inputs and outputs; [[u12,u21,u22,u23,u31],[x12,x21,x22,x23,x31]]
        self.learning_rate = learning_rate  # start with 0.01 then vary the scale
        self.weights = dict()  # weights
        weights_keys = [1, 2, 3, 11, 12, 13]  # weights keys
        for key in weights_keys:
            self.weights[key] = 0

        self.weights_path = str(weights_path)
        self.sensor_reads_path = str(sensor_reads_path)
        self.backup_path = str(backup_path)
        self.read_weights()  # Initialize weights.

    def squash_output(self,value):
        if(value < -1):
            return -1
        elif(value > 1):
            return 1
        else:
            return value

    def read_training_values(self):
        if(isfile(self.sensor_reads_path)):
            f = open(self.sensor_reads_path, 'r')
            lines = f.readlines()
            for i in range(len(lines)-1):
                y = float(lines[i])
                self.ys.append(y)
            self.nr_train_points = len(lines) - 1
            f.close()
        else:
            print('File not found')

    def read_weights(self):
        if(isfile(self.weights_path)):
            f = open(self.weights_path, 'r')
            lines = f.readlines()
            self.weights[11], self.weights[12], self.weights[13] = map(float, lines[0].split(" "))
            self.weights[1], self.weights[2], self.weights[3] = map(float, lines[1].split(" "))
            f.close()
            return self.weights

    def save_and_backup_weights(self):
        f1 = open(self.weights_path, 'w')
        f2 = open(self.backup_path, 'a+')
        line1 = str(round(self.weights[11],4)) + ' ' + str(round(self.weights[12],4)) + ' ' + str(round(self.weights[13],4)) + '\n'
        line3 = str(round(self.weights[1],4)) + ' ' + str(round(self.weights[2],4)) + ' ' + str(round(self.weights[3],4)) + '\n'
        f1.write(line1)
        f2.write(line1)
        f1.write(line3)
        f2.write(line3)
        f1.close()
        f2.close()

    def first_pass(self, y):
        row = []
        us = []
        xs = []
        us.append(y)
        xs.append(self.squash_output(y))
        us.append(self.weights[11] * (self.target - us[0]))
        xs.append(self.squash_output(us[1]))
        us.append(self.weights[12] * (self.target - us[0]))
        xs.append(self.squash_output(us[2]))
        us.append(self.weights[13] * (self.target - us[0]))
        xs.append(self.squash_output(us[3]))
        us.append(self.weights[1] * xs[1] + self.weights[2] * xs[2] + self.weights[3] * xs[3])
        xs.append(self.squash_output(us[4]))
        row.append(us)
        row.append(xs)
        return row

    # One row in self, starting from y (NOT THE FIRST ROW).
    def one_pass(self, prev_row, y):
        row = []
        us = []
        xs = []
        us.append(y)
        xs.append(self.squash_output(y))
        us.append(self.weights[11] * (self.target - us[0]))
        xs.append(self.squash_output(us[1]))

        us.append(self.weights[12] * (self.target - us[0]))
        if(us[2] < -1 or us[2] > 1):
            xs.append(self.squash_output(us[2]))
        else:
            xs.append(us[2] + prev_row[0][2])

        us.append(self.weights[13] * (self.target - us[0]))
        if(us[3] < -1 or us[3] > 1):
            xs.append(self.squash_output(us[3]))
        else:
            xs.append(us[3] - prev_row[0][3])

        us.append(self.weights[1] * xs[1] + self.weights[2] * xs[2] + self.weights[3] * xs[3])
        xs.append(self.squash_output(us[4]))
        row.append(us)
        row.append(xs)

        return row

    # Taken from: https://stackoverflow.com/questions/5595425/what-is-the-best-way-to-compare-floats-for-almost-equality-in-python
    def isclose(self, a, abs_tol=0.01):
        return a < abs_tol

    # LAST ROW MUST BE SHAVED !!!!
    def backprop(self):
        sigma_i = [0, 0, 0]
        sigma_ij = [0, 0, 0]

        for k in range(1, len(self.ys)-1):
            denominator = self.params[k][1][4] - self.params[k-1][1][4]
            if(self.isclose(denominator)):
                continue
            # delta_i is minused already.
            delta_i = (self.ys[k] - self.target) * (self.ys[k+1]-self.ys[k]) / denominator
            sigma_i = [sigma_i[i] + delta_i * self.params[k][1][i+1] for i in range(3)]
            for j in range(3):
                denominator = self.params[k][0][j+1] - self.params[k-1][0][j+1]
                if(self.isclose(denominator)):
                    continue
                sigma_ij[j] = sigma_ij[j] + delta_i * self.weights[j+1] * (self.params[k+1][1][j+1] - self.params[k][1][j+1]) / denominator

        for i in range(1, 4):
            self.weights[i] = self.weights[i] - self.learning_rate * sigma_i[i-1]
            id_ij = 10 + i
            self.weights[id_ij] = self.weights[id_ij] - self.learning_rate * sigma_ij[i-1]

    def train_model(self):
        self.read_training_values()
        try:

            if(len(self.ys) == 0):
                raise ValueError()

            self.read_weights()

            self.params.append(self.first_pass(self.ys[0]))

            for y in self.ys[1:]:
                self.params.append(self.one_pass(self.params[-1],y))

            self.backprop()
            print(self.weights)
            self.save_and_backup_weights()
            return True

        except ValueError:
            print('Values could not be read from the file.')
