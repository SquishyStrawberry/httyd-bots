#!/usr/bin/env bash


echo -ne "Which bot do you want to run?\n1. Cloudjumper\n2. Thornado\n> "
read option
option=${option:0}

if [ "$option" == "1" ]; then
    directory="Cloudjumper"
    command="python3 -m cloudjumper"
else 
    if [ "$option" == "2" ]; then
        directory="Thornado"
        command="python3 -m thornado"
    else
        echo "Invalid number!"
        exit 1
    fi
fi

cd ${directory}
while [[ 1 -eq 1 ]]; do
    $(${command})
done

