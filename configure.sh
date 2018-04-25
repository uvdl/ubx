#!/bin/bash

DEVICE=/dev/ttyHSL2

# Reset message configuration
./load-defaultconfiguration.py msgConf --device $DEVICE

# Disable all NMEA messages
./set-nmea.py --device $DEVICE 0

# Enable desired messages
./getset-messagerate.py --device $DEVICE --name ESF-STATUS --setRate 1
# ./getset-messagerate.py --device $DEVICE --name ESF-RAW --setRate 1
./getset-messagerate.py --device $DEVICE --name HNR-PVT --setRate 1
./getset-messagerate.py --device $DEVICE --name NAV-PVT --setRate 1
./getset-messagerate.py --device $DEVICE --name NAV-ATT --setRate 1
./getset-messagerate.py --device $DEVICE --name NAV-DOP --setRate 1
./getset-messagerate.py --device $DEVICE --name NAV-STATUS --setRate 1
./getset-messagerate.py --device $DEVICE --name NAV-SVINFO --setRate 1
./set-highnavrate.py --device $DEVICE 20

echo "ublox configuration complete"