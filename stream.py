#!/usr/bin/python
# Copyright (C) 2010 Timo Juhani Lindfors <timo.lindfors@iki.fi>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import ubx
import struct
import calendar
import os
import gobject
import logging
import sys
import socket
import time

fixTypeDict = {0: 'NO', 1: 'DR', 2: '2D', 3: '3D', 4: '3D+DR', 5: 'Time'}
fusionModeDict = {0: 'INIT', 1: 'ON', 2: 'Suspended', 3: 'Disabled'}

timestamp = 0
lat = 0
lon = 0
alt = 0
speed = 0
roll = None
pitch = None
heading = None
hdop = None
numSats = None
avgCNO = None
fix = 'No'
fusionMode = 'Unknown'
output = None
display = True
outputFile = None
dataRate = None
dataRateStartTime = None
dataCaptured = 0

def callback(ty, packet):
    global timestamp, lat, lon, alt, speed, roll, pitch, heading, hdop, numSats, avgCNO, fix, fusionMode, output, display, dataRate

    if args.raw:
        print('{}: {}'.format(ty, packet))

    if ty == 'HNR-PVT':
        timestamp = packet[0]['ITOW']/1e3
        lat = packet[0]['LAT']/1e7
        lon = packet[0]['LON']/1e7
        alt = packet[0]['HEIGHT']/1e3
        heading = packet[0]['HeadVeh']/1e5
        speed = packet[0]['Speed']/1e3
        fix = fixTypeDict[packet[0]['GPSFix']]
    
        speedMph = speed / 0.44704
        if display:
            numSatsString = '--' if numSats is None else '{:2}'.format(numSats)
            rollString = '--' if roll is None else '{:.3f}'.format(roll)
            pitchString = '--' if pitch is None else '{:.3f}'.format(pitch)
            hdopString = '--' if hdop is None else '{:.1f}'.format(hdop)
            cnoString = '--' if avgCNO is None else '{:.1f}'.format(avgCNO)
            displayString = '[{:.3f}] Pos: {:.6f}, {:.6f}, {:.3f}'.format(timestamp, lat, lon, alt)
            displayString += ' | R: {}, P: {}, Hdg {:.1f}'.format(rollString, pitchString, heading)
            displayString += ' | Fix: {}, # Sats: {}, CNO: {}, HDOP: {}, Fusion: {}'.format(fix, numSatsString, cnoString, hdopString, fusionMode) 
            displayString += ' | {:.1f} MPH'.format(speedMph)
            if dataRate is not None:
                displayString += ' | Data rate: {:.1f} Kbps'.format(dataRate/1000)
            print(displayString)

    elif ty == 'NAV-ATT':
        roll = packet[0]['Roll']/1e5
        pitch = packet[0]['Pitch']/1e5
        # heading = packet[0]['Heading']/1e5
    elif ty == 'NAV-DOP':
        hdop = packet[0]['HDOP']/100.
    elif ty == 'NAV-STATUS':
        fix = fixTypeDict[packet[0]['GPSfix']]
    elif ty == 'NAV-SVINFO':
        cno = []
        for satInfo in packet[1:]:
            if satInfo['Flags'] & 1:
                cno.append(satInfo['CNO'])
        numSats = len(cno)
        if len(cno):
            avgCNO = float(sum(cno)) / len(cno)
        else:
            avgCNO = 0
    elif ty == 'ESF-STATUS':
        fusionMode = fusionModeDict[packet[0]['FusionMode']]
        # print("{}: {}".format(ty, packet))
    else:
        return

    # if ty.startswith('$'):
    #     print packet
    # else:
    #     print("{}: {}".format(ty, packet))

def rawCallback(data):
    global outputFile, dataRate, dataRateStartTime, dataCaptured
    if outputFile is not None:
        outputFile.write(data)
    if args.raw:
        dataRateString = '{:.3f} Kbps'.format(dataRate) if dataRate is not None else '--'
        print('Data rate: {}, Data [{}]: {}'.format(dataRateString, len(data), repr(data)))
    if dataRateStartTime is None:
        dataRateStartTime = time.time()
    else:
        dataCaptured += len(data)
        curTime = time.time()
        elapsed = curTime - dataRateStartTime
        if elapsed > 2:
            dataRate = dataCaptured / elapsed * 8
            dataCaptured = 0
            dataRateStartTime = curTime

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--device', '-d', default=None)
    group.add_argument('--file', '-f', default=None)
    parser.add_argument('--output', '-o', default=None)
    parser.add_argument('--raw', action='store_true')
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.WARNING)

    if args.output is not None:
        outputFile = open(args.output, 'wb')

    if args.device:
        t = ubx.Parser(callback, device=args.device, rawCallback=rawCallback)
        try:
            gobject.MainLoop().run()
        except KeyboardInterrupt:
            gobject.MainLoop().quit()
            if outputFile is not None:
                outputFile.close()
    else:
        t = ubx.Parser(callback, device=False)
        binFile = args.file
        data = open(binFile,'r').read()
        t.parse(data)
