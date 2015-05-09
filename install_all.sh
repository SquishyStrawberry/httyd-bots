#!/usr/bin/env bash

projectRoot=$(pwd)
for directory in $( ls -Cd */ | egrep ".*?\s+" ); do
    cd ${projectRoot}/${directory}
    for pyFile in $(ls -C *.py | egrep ".*?\s+"); do
        if [[ pyFile -eq "setup.py" ]]; then
            echo "Installing $projectRoot/$directory"
            python3 setup.py install
            break
        fi
    done
done
