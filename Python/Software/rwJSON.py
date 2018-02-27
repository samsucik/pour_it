import json
import os
from collections import OrderedDict

class rwJSON:

    def __init__(self):
        self.dict = OrderedDict()
        self.dict['commands'] = []

    # This function should be called after each call to the motors.
    # Time should be the time the motors run for (at the specified speeds).
    def addCommand(self, left_sp, right_sp, time):
        auxdict = {}
        auxdict['left_sp'] = left_sp
        auxdict['right_sp'] = right_sp
        auxdict['time']   = time
        self.dict['commands'].append(auxdict)

    # Saves the added values to a .json file (named after the second argument).
    def saveCommands(self, filename, path=''):
        filenamex = filename
        if(not filename.endswith('.json')):
            filenamex = filename + '.json'
        pathx = path + filenamex
        with open(pathx, 'w') as f:
            json.dump(self.dict, f)
            print('Values successfully saved')

    # Read the commands previously given to the robot from filename.json, located at path.
    # path can be omitted, in which case the .json file must be in the same place as rwJSON.py.
    def readCommands(filename,path=''):
        filenamex = filename
        if(not filename.endswith('.json')):
            filenamex = filename + '.json'

        pathx = path + filenamex

        if(os.path.isfile(pathx)):
            dict = json.load(open(pathx))
            if('commands' in dict):
                return dict['commands']
                # The commands will be returned as a list of dictionaries.
            else:
                print('The information from the JSON file has the wrong format')
                return []
        else:
            print('JSON file not found')
            return []



