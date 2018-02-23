![pour_it logo](./logo/pourit_logo.png | width=200)

[![Build Status](https://travis-ci.org/samsucik/pour_it.svg?branch=master)](https://travis-ci.org/samsucik/pour_it)

Project of group #1 (pour_it) for System Design Project 2017/18.

## Python Ev3 documentation
[Sensor information](https://sites.google.com/site/ev3python/learn_ev3_python/using-sensors)

## Virtual environment setup
Always use virtual environment to ensure we all use the same Python version (Python 3), packages, etc.

To set up the virtual environment:
```{r, engine='bash'}
./setup.sh
```

From now on just activate the environment using ```source bin/activate``` and deactivate using ```deactivate```.

Use ```pip3 install pkgname``` to install new packages. Remember to update [requirements.txt](./requirements.txt), preferably by running:
```{r, engine='bash'}
pip3 freeze > requirements.txt
```

and ensure (probably applies to Ubuntu users only) that requirements.txt does not contain the flawed ```pkg-resources==0.0.0``` dependency (remove the line if necessary).

## DEV vs TEST environments
In order to be able to test the code without being connected to the brick, we have the TEST environment which does not use the true ```ev3dev``` libraries but replaces them by an abstraction [obtained here](https://gitlab.com/ev3py/ev3py-runlocal) (infinite thanks to [Timon Reinold](https://gitlab.com/users/tirei/contributed)!).

More info on how to run the code in the two environments will follow soon.

Authors: [Andrew](https://github.com/Andrew-lindsay), [Bob](http://bob.com/), [Jonas](https://github.com/Jonuxs), [Max](https://github.com/mgirkins), [Mihai](https://github.com/MihaiAC), [Michael](https://github.com/mmaclennan4), [Sam](https://github.com/samsucik)
