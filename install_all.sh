#!/usr/bin/env bash

original=$(pwd)
for i in $( ls -Cd */ | egrep ".*?\s+" ); do
    cd $original/$i
    echo "Installing $original/$i"
    python3 setup.py install
done
