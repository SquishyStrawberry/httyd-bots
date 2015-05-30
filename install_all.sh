#!/usr/bin/env bash

# Exists on error.
set -e
projectRoot=$(pwd)

echo "A venv is now mandatory, if you wish to install globally do so manually."

python3 -c "print" > /dev/null 2> /dev/null
if [[ $? == 0 ]]; then
    echo "Found Python3"
    pip > /dev/null 2> /dev/null
    if [[ $? == 0 ]]; then
        echo "Found Pip3"
    else
        echo "Pip was not found, exiting..." >&2
        exit 1
    fi
else
    echo "Python3 was not found, exiting..." >&2
    exit 1
fi

echo "Making venv... (This will take a while)"
python3 -m venv httyd_env || virtualenv -p python3 httyd_env
source httyd_env/bin/activate

if [[ -e ${projectRoot}/requirements.txt ]]; then
    echo "Found global requirements.txt in ${projectRoot}"
    pip3 install -r ${projectRoot}/requirements.txt --upgrade
else
    echo "No global requirements.txt in ${projectRoot}"
fi

find ${projectRoot} -name "setup.py" -maxdepth 2 -execdir python3 {} install \;

