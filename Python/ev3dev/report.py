# This script provides procedures to output stati and changes 
# concerning the pseudo-ev3 test to the user.

# this script just sources the the right language
# from .report_en import *

# pour_it uses own report module that uses pre-programmed
# percept providers instead of getting them from command line
from .report_pour_it import *
