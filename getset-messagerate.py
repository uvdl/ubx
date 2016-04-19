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

def printMessage(packet):
    print('\nMessage Rate Configuration (CFG-MSG)')
    print('--------------------------------------')
    print('Message Class: {}'.format(packet[0]['msgClass']))
    print('Message ID: {}'.format(packet[0]['msgId']))
    for i, block in enumerate(packet[1:]):
        print('Port: {} -> Rate: {}'.format(i, block['rate']))

def setMessageRate(packet, messageRate):
    '''This takes a CFG-MSG packet and modifies it to set the message rate'''

    for block in packet[1:]:
        block['rate'] = messageRate

    return packet

def callback(ty, packet):
    print("callback %s" % repr([ty, packet]))
    if ty == "CFG-MSG":
        print('***********************')
        print(' Current configuration')
        print('***********************')
        printMessage(packet)
        if args.setRate is not None:
            packet = setMessageRate(packet, args.setRate)

            packetSize = 2 + 1*(len(packet)-1)
            print('\nSending new configuration...')
            t.send("CFG-MSG", packetSize, packet)
    elif ty == "ACK-ACK":
        if args.setRate is not None:
            print('\nNew configuration accepted!')
        loop.quit()
    return True

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('cls', help='Specify the message class. NMEA Std is 0xF0. NMEA PUBX is 0xF1.')
    parser.add_argument('ident', help='Specify the message id. i.e. GGA is 0x00.')
    parser.add_argument('--setRate', '-s', type=int, help='Sets the message rate. 1 means send every nav message, 2 means send every other nav message, etc.')
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()

    if args.cls is not None:
        if args.cls.startswith('0x') or args.cls.startswith('0X'):
            args.cls = int(args.cls, 16)
        else:
            args.cls = int(args.cls)

    if args.ident is not None:
        if args.ident.startswith('0x') or args.ident.startswith('0X'):
            args.ident = int(args.ident, 16)
        else:
            args.ident = int(args.ident)

    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)
    t.send("CFG-MSG", 2, {'msgClass': args.cls, 'msgId': args.ident})
    loop.run()

