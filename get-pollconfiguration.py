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

loop = gobject.MainLoop()

def callback(ty, packet):
    print("callback %s" % repr([ty, packet]))
    if ty == "CFG-INF":
        pass
        # if sys.argv[1] == "on":
        #     # NMEA
        #     packet[1]["In_proto_mask"] = 1
        #     packet[1]["Out_proto_mask"] = 2
        # else:
        #     # only UBX
        #     packet[1]["In_proto_mask"] = 1
        #     packet[1]["Out_proto_mask"] = 1
        # t.send("CFG-PRT", 20, packet)
    elif ty == "ACK-ACK":
        loop.quit()
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('protocol', choices=['ubx', 'nmea'], help='Specify the protocol to get the configuration for.')
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()
    
    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)

    if sys.argv[1] == 'ubx':
        t.send("CFG-INF", 1, {'ProtocolID': 0})
    elif sys.argv[1] == 'nmea':
        t.send("CFG-INF", 1, {'ProtocolID': 1})
    else:
        print 'Protocol must be \'ubx\' or \'nmea\''
    loop.run()

