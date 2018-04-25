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

state = 0

def callback(ty, packet):
    global state
    if state == 0 and ty == "CFG-PRT":
        print(packet)
        if args.state == '1':
            # NMEA
            packet[1]["In_proto_mask"] = packet[1]["In_proto_mask"] | 2
            packet[1]["Out_proto_mask"] = packet[1]["Out_proto_mask"] | 2
        else:
            packet[1]["In_proto_mask"] = packet[1]["In_proto_mask"] & 0xfd
            packet[1]["Out_proto_mask"] = packet[1]["Out_proto_mask"] & 0xfd
        print(packet)
        t.send("CFG-PRT", 20, packet)
        state = 1
    elif state == 1 and ty == "ACK-ACK":
        loop.quit()
    return True

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('state', choices=['0', '1'], help='Sets the NMEA mode - 0 for off, 1 for on')
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR)

    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)
    t.send("CFG-PRT", 0, [])
    loop.run()
