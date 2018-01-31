#!/bin/sh

# If the virtual environment hasn't been set up yet, 
# set it up and install all dependencies.
if [ ! -f "./bin/activate" ]; then
	echo "Re-creating the virtual environment..."
	pyvenv .
	source ./bin/activate
	pip install -r requirements.txt
	deactivate
fi