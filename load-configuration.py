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
from ubx import clearMaskShiftDict, buildMask

loop = gobject.MainLoop()

def callback(ty, packet):
    print("callback %s" % repr([ty, packet]))
    if ty == "ACK-ACK":
        print('Settings loaded successfully!')
        loop.quit()
    elif ty == "ACK-NACK":
        print('Failed to load settings!')
        loop.quit()
    return True

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('settings', nargs='+', choices=(clearMaskShiftDict.keys() + ['all', 'none']), help='Specify the settings to be reset to default. \'all\' will reset all settings and \'none\' will save none.')
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()

    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)
    loadMask = buildMask(args.settings, clearMaskShiftDict)

    print('Loading from saved configuration...')
    t.send("CFG-CFG", 12, {'clearMask': 0, 'saveMask': 0, 'loadMask': loadMask})
    loop.run()
