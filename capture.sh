#!/bin/bash

DATETIME=`date +'%Y%m%dT%H%M%S'`

if [ $# -eq 0 ]; then
    OUTPUT_PATH=.
else
    OUTPUT_PATH=$1
fi

./configure.sh

./stream.py --device /dev/ttyHSL2 -o ${OUTPUT_PATH}/UBLOX_${DATETIME}.ubx