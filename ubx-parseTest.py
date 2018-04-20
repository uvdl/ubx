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


# Parse UBX from stdin.

import ubx
import struct
import calendar
import os
#import gobject
import logging
import sys
import time
import pynmea2

messageCounts = {}

def callback(ty, *args):
    print("callback %s %s" % (ty, repr(args)))
    
    if ty.startswith('$'):
        try:
            nmea = pynmea2.parse(args[0])
            print nmea
        except:
            print('*** CANNOT PARSE {}!'.format(ty))

    if ty not in messageCounts:
        messageCounts[ty] = 0
    messageCounts[ty] += 1

    if ty == 'NAV-SVINFO':
        for item in args[0]:
            print item
            
if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.exit('Usage: %s <Binary filename>' % sys.argv[0])

    t = ubx.Parser(callback, device=False)
    binFile = sys.argv[1]
    data = open(binFile,'r').read()
    t.parse(data)

    print('')
    totalMessages = 0
    for key in sorted(messageCounts.keys()):
        print('{}: {}'.format(key, messageCounts[key]))
        totalMessages += messageCounts[key]

    print('\nTotal: {}'.format(totalMessages))
