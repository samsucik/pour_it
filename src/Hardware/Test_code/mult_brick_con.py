import rpyc

# setup connection to main motor control brick
#host name or IP address of EV3
conn1 = rpyc.classic.connect('ev3dev1.local')
conn2 = rpyc.classic.connect('ev3dev2.local')

#import ev3dev.ev3
brick1 = conn1.modules['ev3dev.ev3']
brick2 = conn2.modules['ev3dev.ev3']

import time
from time import sleep

brick1.Sound.speak("Hello from brick 1")
brick2.Sound.speak("Hello from brick 2")
    