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


# Set baudrate

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
lastStateTransitionTime = 0

def callback(ty, packet):
    global state, lastStateTransitionTime
    if ty == "CFG-PRT" and state == 0:
        packet[1]["Baudrate"] = args.baudrate
        t.send("CFG-PRT", 20, packet)
        state = 1
    elif ty == "ACK-ACK" and state == 1:
        print('\nBaud rate setting acknowledged!')
        os.system("stty -F {} {} cs8 -cstopb -parenb".format(t.device, args.baudrate))
        state = 2
        loop.quit()
    else:
        elapsed = time.time() - lastStateTransitionTime
        if elapsed > 1:
            loop.quit()

    return True

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('baudrate', type=int, choices=[9600, 115200], help='Specify the baudrate. Must be 9600 or 115200')
    parser.add_argument('--device', '-d', required=True, help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    parser.add_argument('--retries', '-r', type=int, default=2, help='Number of retries for each baudrate')
    args = parser.parse_args()

    baudRates = [9600, 115200]

    for initialBaudRate in baudRates * args.retries:
        state = 0
        lastStateTransitionTime = time.time()
        os.system("stty -F {} {} cs8 -cstopb -parenb".format(args.device, initialBaudRate))
        t = ubx.Parser(callback, device=args.device)
        t.send("CFG-PRT", 0, [])
        loop.run()
        os.close(t.fd)
        if state == 2:
            break

    if state == 2:
        print('\n*** Baud rate successfully set to {}'.format(args.baudrate))
    else:
        print('\n*** FAILED TO SET BAUDRATE!!!')


