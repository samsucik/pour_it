
# If the virtual environment hasn't been set up yet, 
# set it up and install all dependencies.
if [ ! -f "./bin/activate" ]; then
	echo "Re-creating the virtual environment..."
	python3 -m venv .
	source ./bin/activate
	echo "Installing requirements..."
	pip3 install -r requirements.txt
	echo "Exiting..."
	deactivate
else
	echo "Virtual environment already exists"
fi