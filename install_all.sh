#!/usr/bin/env bash

projectRoot=$(pwd)

echo "A venv is now mandatory, if you wish to install globally do so manually."

python3 -c "print" > /dev/null 2> /dev/null
if [[ $? == 0 ]]; then
    echo "Found Python3"
else
    echo "Python3 was not found, exiting..." >&2
    exit 1
fi

echo "Making venv... (This will take a while)"

echo "Trying -m venv..."
python3 -m venv httyd_env
if [[ $? != 0 ]]; then
    echo "Failed with -m venv, trying virtualenv."
    virtualenv -p python3 httyd_env
    if [[ $? != 0 ]]; then
        echo "Could not run virtualenv, please report error message."
        exit 1
    else
        echo "virtualenv succeeded..."
    fi
else
    echo "-m venv succeeded..."
fi

source httyd_env/bin/activate

#if [[ -e ${projectRoot}/requirements.txt ]]; then
#    echo "Found global requirements.txt in ${projectRoot}"
#    pip3 install -r ${projectRoot}/requirements.txt --upgrade
#else
#    echo "No global requirements.txt in ${projectRoot}"
#fi

find ${projectRoot} -name "setup.py" -maxdepth 2 -execdir python3 {} install \;

