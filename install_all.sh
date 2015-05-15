#!/usr/bin/env bash

projectRoot=$(pwd)

if hash python3; then
    echo "Found Python3"
else
    echo "Python3 was not found, exiting..."
    exit 1
fi

if [[ -e ${projectRoot}/requirements.txt ]]; then
    echo "Found global requirements.txt in ${projectRoot}"
    pip3 install -r requirements.txt --upgrade
else
    echo "No global requirements.txt in ${projectRoot}"
fi

for directory in $( ls -Cd */ | egrep ".*?\s+" ); do
    cd ${projectRoot}/${directory}
    echo "Checking ${projectRoot}/${directory}"
    if [[ -e ${projectRoot}/${directory}/setup.py ]]; then
        echo "Installing ${projectRoot}/${directory}"
        python3 setup.py install
    else
        echo "No setup.py in ${projectRoot}/${directory}"
    fi
done
