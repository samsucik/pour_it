#!/bin/bash
# starts the remote server on brick 1 and 2 
ssh robot@ev3dev1.local 'nohup python3 /usr/bin/rpyc_classic.py < /dev/null > /dev/null 2> /dev/null  &'
ssh robot@ev3dev2.local 'nohup python3 /usr/bin/rpyc_classic.py < /dev/null > /dev/null 2> /dev/null  &'
