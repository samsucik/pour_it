#!/bin/bash
# source ~./profile 
# workon cv 
# starts the remote server on brick 1 and 2 
ssh robot@ev3dev1 'nohup python3 /usr/bin/rpyc_classic.py < /dev/null > /dev/null 2> /dev/null  &'
ssh robot@ev3dev2 'nohup python3 /usr/bin/rpyc_classic.py < /dev/null > /dev/null 2> /dev/null  &'
sleep 30
echo "After sleep"
python src/Hardware/Test_code/mult_brick_con.py
# turn off servers
ssh robot@ev3dev1 'killall python3'
ssh robot@ev3dev2 'killall python3'
