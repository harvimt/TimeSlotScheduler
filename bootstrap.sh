#!/bin/sh

if test -f /usr/bin/virtualenv; then
  if ! test -x ./env; then
    virtualenv --no-site-packages env
  fi
  if test -f ./env/bin/python && test -f ./env/bin/pip; then
    env/bin/pip install -r requirements.txt
    if [ ! -f data.db ]; then
      env/bin/python runflaskapp.py install
      echo "In order to access and manage the web interface, a system user must be created." 
      echo "If this is the first time configuring, please use the createuser.py script to create an account."
    else
      echo "It appears that system has already been bootstrapped."
    fi
  fi
else
  echo "You must install python-virtualenv in order to build this project."
  echo "Please see http://pypi.python.org/pypi/virtualenv for more details"
fi
