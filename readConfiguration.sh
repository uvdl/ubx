#!/bin/bash

# Defaults
DEVICE=/dev/ttyHS1
RATE=115200
PORT=1
RESETCONFIG=0

show_help() {
    echo
    echo "Usage: readConfiguration -d DEVICE -r RATE"
    echo 
    echo "    -d DEVICE    Specify the device path. Defaults to /dev/ttyHSL2."
    echo "                 On OS X with a USB connection, should be /dev/cu.usbmodem*"
    echo "    -r RATE      Specify the baud rate. Should be 9600 or 115200."
    echo "                 Defaults to 115200."
    echo 
}

show_error() {
    echo 
    echo "***************************"
    echo "* CONFIGURATION READ FAILED!!! *"
    echo "***************************"
    echo
}

OPTIND=1         # Reset in case getopts has been used previously in the shell.

while getopts "h?d:r:c" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    d)  DEVICE=$OPTARG
        ;;
    r)  
        RATE=$OPTARG
        ;;
    esac
done

if [ ! -e $DEVICE ]; then
    echo 
    echo "*** ${DEVICE} does not exist!"
    echo 
    exit 1
fi

if [ ! -c $DEVICE ]; then
    echo 
    echo "*** ${DEVICE} is not a character device!"
    echo 
    exit 1
fi

if [[ $DEVICE = *"usbmodem"* ]]; then
  PORT=3
fi

case "$RATE" in
    9600) ;;
    115200) ;;
    *) 
        echo 
        echo "*** Invalid baud rate!"
        show_help
        exit 1
        ;;
esac

stty -F $DEVICE $RATE

# Get power mode (CFG-PMS)
./get-powermode --device $DEVICE

# Get high nav rate (CFG-HNR)
./get-highnavrate.py --device $DEVICE
if [ $? -eq 1 ]
then
    show_error
    exit 1
fi

# Get GNSS measurement rate (CFG-RATE)
./get-logging-rate.py --device $DEVICE
if [ $? -eq 1 ]
then
    show_error
    exit 1
fi
