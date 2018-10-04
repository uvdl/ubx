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
currentBaudRate = 0
state = -1

def callback(ty, packet):
    global state
    print("callback %s" % repr([ty, packet]))
    # Wait for initial CFG-PRT response
    if state == 0:
        if ty == "CFG-PRT":
            if currentBaudRate != args.baudRate:
                print('Sending CFG-PRT for baud rate change to {}...'.format(args.baudRate))
                packet[1]["Baudrate"] = args.baudRate
                t.send("CFG-PRT", 20, packet)
                state = 1
            else:
                print('Baudrate is already set to the desired speed!')
                state = 3
                loop.quit()
    # Wait for ACK-ACK
    elif state == 1:
        if ty == "ACK-ACK":
            if packet[1]['ClsID'] == 0x06 and packet[1]['MsgID'] = 0x00:
                print('Received ACK for CFG-PRT config message - setting serial port speed...')
                os.system("stty -F {} {}".format(t.device, args.baudRate))
                print('Polling for CFG-PRT to confirm baudrate change...')
                state = 2
        elif ty == 'ACK-NACK':
            raise Exception('Received ACK-NACK! CFG-PRT message was rejected!')
    # Wait for second CFG-PRT to confirm baud rate change
    elif state == 2:
        if ty == "CFG-PRT":
            if packet[1]['Baudrate'] == args.baudRate:
                print('Received CFG-PRT message - configuration complete.')
            else:
                raise Exception('CFG-PRT reports a baudrate ({}) that does not match the current serial port speed({})! This is very weird!'.format(packet[1]['Baudrate'], args.baudRate))
            state = 3
            loop.quit()
    return True

def timeout():
    print('Timeout!')
    loop.quit()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('baudRate', type=int, choices=[9600, 115200], help='Specify the baudrate. Must be 9600 or 115200')
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()

    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)

    # Loop through baud rates and try to reconfigure the baud rate
    for baudRate in [9600, 115200]:
        # Set the host baud rate
        currentBaudRate = baudRate
        os.system("stty -F {} {}".format(t.device, currentBaudRate))
        
        # Setup timeout and reset state machine
        timeoutSourceId = gobject.timeout_add(500, timeout)
        state = 0
        startTime = time.time()

        # Poll for CFG-PRT
        t.send("CFG-PRT", 0, [])
        loop.run()

        # Clear timeout
        gobject.source_remove(timeoutSourceId)

        # Did we succeed?
        if state == 3:
            print('Elapsed time: {}'.format(time.time() - startTime))
            break

    if state != 3:
        raise Exception('Failed to set baudrate!')


