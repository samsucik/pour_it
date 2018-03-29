import rpyc, os

class PourItUtils():
    def __init__(self):
        self.detect_platform()
        self.set_ev3_address()
    
    def detect_platform(self):
        self.platform = 'other'
        if os.getcwd().startswith('/home/pi'):
            self.platform = 'pi'
        elif os.getcwd().startswith('/afs/inf.ed.ac.uk'):
            self.platform = 'dice'

    def set_ev3_address(self):
        self.ev3_address = 'ev3dev'
        if self.platform in ['pi', 'other']:
            self.ev3_address += '.local'


    def get_rpyc_conn(self):
        conn = rpyc.classic.connect('ev3dev')