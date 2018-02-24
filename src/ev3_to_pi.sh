#!/bin/sh
# NOT FULLY TESTED
# Script to be run on ev3 brick, as it starts RPYC server then ssh in to the pi
# running the main function of our robot code.
# ssh keys need to be exchanged/set-up before as password will be request
# otherwise meaning the script cannot proceed
echo "start rpyc server, run as background task"
./rpyc_server.sh &
echo "connecting to pi"
# Need final name and path location of initial python script
ssh -t pi@raspberrypi.local 'source ~/.profile; workon cv; python pour_it/src/Software/forward.py'
echo "returned from pi connection"
