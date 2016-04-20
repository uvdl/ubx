#!/usr/bin/python
# Copyright (C) 2016 Berkeley Applied Analytics <john.kua@berkeleyappliedanalytics.com>
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


# Enable or disable the use of NMEA.

import ubx
import struct
import calendar
import os
import gobject
import logging
import sys
import socket
import time

def callback():
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--startType', choices=['hot', 'warm', 'cold'], default='cold', help='Specify the start type. This controls what data is cleared. Use the \'clear\' option to specify individual sections to clear.')
    parser.add_argument('--clear', '-c', choices=ubx.navBbrMaskShiftDict.keys() + ['all', 'none'], nargs='+', default=None, help='Specify the data structures to clear. This overrides \'startType\'.')
    parser.add_argument('--mode', '-m', choices=ubx.resetModeDict.keys(), default='hw', help='Specify the restart mode.\nsw: Controlled software reset\nswGnssOnly: Controlled software reset (GNSS Only)\nhw: Hardware reset (Watchdog) immediately\nhwShutdown: Hardware reset (Watchdog) after shutdown\ngnssStop: Controlled GNSS stop\ngnssStart: Controlled GNSS start')
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()
    
    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)

    if args.clear is None:
        if args.startType == 'hot':
            navBbrMask = 0
        elif args.startType == 'warm':
            navBbrMask = 1
        elif args.startType == 'cold':
            navBbrMask = 0xff
    else:
        navBbrMask = ubx.buildMask(args.clear, ubx.navBbrMaskShiftDict)

    resetMode = ubx.resetModeDict[args.mode]

    print('Sending restart command... this will not be ACKed.')
    t.send("CFG-RST", 4, {'nav_bbr': navBbrMask, 'Reset': resetMode})

