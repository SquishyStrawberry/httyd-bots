#!/usr/bin/env bash

# Exists on error.
set -e
projectRoot=$(pwd)

if hash python3; then
    echo "Found Python3"
    if hash pip3; then
        echo "Found Pip3"
    else
        echo "Pip3 was not found, exiting..." >&2
        exit 1
    fi
else
    echo "Python3 was not found, exiting..." >&2
    exit 1
fi

echo "A Venv is now mandatory. If you wish to install globally, please do so manually."
echo "Making Venv... (this will take a while.)"
python3 -m venv httyd_env
source httyd_env/bin/activate

# To make sure you get the new version.
pip3 freeze | egrep "(?i)thornado|irc[-_]helper|cloudjumper" | xargs pip3 uninstall -y
if [[ -e ${projectRoot}/requirements.txt ]]; then
    echo "Found global requirements.txt in ${projectRoot}"
    pip3 install -r ${projectRoot}/requirements.txt --upgrade
else
    echo "No global requirements.txt in ${projectRoot}"
fi

find ${projectRoot} -name "setup.py" -maxdepth 2 -execdir python3 {} install \;

