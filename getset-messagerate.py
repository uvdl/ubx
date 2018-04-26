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
state = 0
lastStateTransitionTime = None

def printMessage(packet):
    print('\nMessage Rate Configuration (CFG-MSG)')
    print('--------------------------------------')
    messageClass = packet[0]['msgClass']
    messageId = packet[0]['msgId']
    if (messageClass, messageId) in ubx.CLIDPAIR_INV:
        messageName = ubx.CLIDPAIR_INV[(messageClass, messageId)]
        print('Message Name: {}'.format(messageName))
    else:
        print('Message Name: Unknown')
    print('Message Class: {}'.format(messageClass))
    print('Message ID: {}'.format(messageId))
    for i, block in enumerate(packet[1:]):
        print('Port: {} -> Rate: {}'.format(i, block['rate']))

def setMessageRate(packet, messageRate):
    '''This takes a CFG-MSG packet and modifies it to set the message rate'''

    for port in args.port:
        packet[port+1]['rate'] = messageRate

    return packet

def callback(ty, packet):
    global state, lastStateTransitionTime
    if ty == "CFG-MSG":
        if args.setRate is None:
            printMessage(packet)
            loop.quit()
        else:
            if state == 0:
                print('\n********************')
                print(' Old configuration')
                print('********************')
                printMessage(packet)
                packet = setMessageRate(packet, args.setRate)

                packetSize = 2 + 1*(len(packet)-1)
                print('\nSending new configuration...')
                t.send("CFG-MSG", packetSize, packet)
                state = 1
                lastStateTransitionTime = time.time()
            elif state == 2:
                print('\n********************')
                print(' New configuration')
                print('********************')
                printMessage(packet)
                loop.quit()
    elif ty == "ACK-ACK":
        if args.setRate is not None and state == 1:
            print('\nNew configuration accepted!')
            t.send("CFG-MSG", 2, {'msgClass': messageClass, 'msgId': messageId})
            state = 2
            lastStateTransitionTime = time.time()
    else:
        elapsed = time.time() - lastStateTransitionTime
        if elapsed > 1:
            if state < 2:
                loop.quit()
                import sys; sys.exit(1)
            else:
                print('\n*** Was not able to read back new config, but was acknowledged')
                loop.quit()


    return True

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--clid', nargs=2, help='Specify the message class and ID')
    group.add_argument('--name', help='Specify the message name')
    parser.add_argument('--setRate', '-s', type=int, help='Sets the message rate. 1 means send every nav message, 2 means send every other nav message, etc.')
    parser.add_argument('--port', '-p', default=[1], type=int, action='append', help='Select a port to set: 0=DDC(I2C), 1=UART1, 3=USB, 4=SPI',)
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR)

    def parseHexDecString(hexDecString):
        if hexDecString.lower().startswith('0x'):
            return int(hexDecString, 16)
        else:
            return int(hexDecString)

    if args.clid is not None:
        messageClass, messageId = args.clid
        messageClass = parseHexDecString(messageClass)
        messageId = parseHexDecString(messageId)
    elif args.name is not None:
        messageClass, messageId = ubx.CLIDPAIR[args.name]

    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)
    t.send("CFG-MSG", 2, {'msgClass': messageClass, 'msgId': messageId})
    lastStateTransitionTime = time.time()
    loop.run()

