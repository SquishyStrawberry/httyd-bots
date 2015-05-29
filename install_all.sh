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

echo -ne "It is heavily reccomended you make a virtual enviorement. Do you want to make one? [y/n]\n> "
read userChoice
if [[ ${userChoice:0} != 'n' ]]; then
    echo "Making venv... (this will take a while\!)"
    python3 -m venv httyd_venv
    source httyd_venv/bin/activate
else
    echo "The packages will be installed globally."
fi


# To make sure you get the new version.
pip3 freeze | egrep "(?i)thornado|irc[-_]helper|cloudjumper" | xargs pip3 uninstall -y
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
