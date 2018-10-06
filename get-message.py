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
import logging
from ublox import Ublox
import ubx

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('messageType', choices=ubx.CLIDPAIR.keys())
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.ERROR)

    ublox = Ublox(args.device)
    message = ublox.poll(args.messageType)
    if message is not None:
        print('{}: {}'.format(args.messageType, message))
    else:
        print('Failed to get message!')




