#!/bin/sh

# If the virtual environment hasn't been set up yet, 
# set it up and install all dependencies.
if [ ! -f "./bin/activate" ]; then
	echo "Re-creating the virtual environment..."
	virtualenv -p python2.7 .
	source ./bin/activate
	pip install -r requirements.txt
	deactivate
else
	echo "Virtual environment already exists"
fi