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
    print('\nGNSS System Configuration (CFG-GNSS)')
    print('--------------------------------------')
    print('Message version: {}'.format(packet[0]['msgVer']))
    print('Number of hardware tracking channels available: {}'.format(packet[0]['numTrkChHw']))
    print('Number of hardware tracking channels used: {}'.format(packet[0]['numTrkChUse']))
    print('Number of config blocks following: {}\n'.format(packet[0]['numConfigBlocks']))
    for configBlock in packet[1:]:
        systemName = ubx.GNSSID_INV[configBlock['gnssId']]
        print('System: {}'.format(systemName))
        print('--> Number of reserved (min) tracking channels: {}'.format(configBlock['resTrkCh']))
        print('--> Maximum number of tracking channels: {}'.format(configBlock['maxTrkCh']))
        flags = configBlock['flags']
        enable = flags & 0x01
        signalConfigMask = flags >> 16
        signals = []
        if systemName == 'GPS':
            if signalConfigMask & 0x01:
                signals.append('GPS L1CA')
        elif systemName =='SBAS':
            if signalConfigMask & 0x01:
                signals.append('SBAS L1CA')
        elif systemName == 'Galileo':
            if signalConfigMask & 0x01:
                signals.append('Galileo E1B/C')
        elif systemName =='BeiDou':
            if signalConfigMask & 0x01:
                signals.append('BeiDou B1I')
        elif systemName =='IMES':
            if signalConfigMask & 0x01:
                signals.append('IMES L1CA')
        elif systemName =='QZSS':
            if signalConfigMask & 0x01:
                signals.append('QZSS L1CA')
            if signalConfigMask & 0x04:
                signals.append('QZSS L1SAIF')
        elif systemName =='GLONASS':
            if signalConfigMask & 0x01:
                signals.append('GLONASS L1OF')
        print('--> Configured signals: {}'.format(', '.join(signals)))
        print('--> System enabled: {}\n'.format(bool(enable)))

def setEnabledSystems(packet, enabledSystemNames):
    '''This takes a CFG-GNSS packet and modifies it to enable a set of systems 
    (GPS, GLONASS, etc) provided as a list of strings'''

    # Ensure the provided system names are valid
    for name in enabledSystemNames:
        if name not in ubx.GNSSID:
            raise Exception('{} not a valid system name! Must be one of: {}'.format(name, ', '.join(ubx.GNSSID.keys())))

    for configBlock in packet[1:]:
        systemName = ubx.GNSSID_INV[configBlock['gnssId']]
        # Enable bit is bit 0
        if systemName in enabledSystemNames:
            configBlock['flags'] |= 0x01
        else:
            # configBlock['resTrkCh'] = 0
            # configBlock['maxTrkCh'] = 0
            configBlock['flags'] &= 0xFE

    return packet

def callback(ty, packet):
    print("callback %s" % repr([ty, packet]))
    if ty == "CFG-GNSS":
        print('***********************')
        print(' Current configuration')
        print('***********************')
        printMessage(packet)
        if args.setEnabled is not None:
            packet = setEnabledSystems(packet, args.setEnabled)

            packetSize = 4 + 8*(len(packet)-1)
            print('\nSending new configuration...')
            t.send("CFG-GNSS", packetSize, packet)
    elif ty == "ACK-ACK":
        if args.setEnabled is not None:
            print('\nNew configuration accepted, requesting receiver cold start...')
            t.send("CFG-RST", 4, {'nav_bbr': 0xffff, 'Reset': 0x02}) # Cold start with controlled software reset of the GNSS only
        loop.quit()
    return True

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--setEnabled', '-s', nargs='+', choices=ubx.GNSSID.keys(), help='Sets the enabled systems. Provide a space separated list, e.g. --setEnabled GPS SBAS Galileo')
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    args = parser.parse_args()

    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback)
    t.send("CFG-GNSS", 0, [])
    loop.run()

