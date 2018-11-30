#!/usr/bin/env python2

import logging
from ublox import Ublox
from ubloxMessage import UbloxMessage
import time
import datetime

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', '-d', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
    parser.add_argument('--loop', '-l', action='store_true', help='Keep sending requests in a loop')
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
    osErrorCount = 0

    while True:
        try:
            packet = ublox.poll('MON-VER', maxRetries=1)
            UbloxMessage.printMessage('MON-VER', packet, header=datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]\n'))
            osErrorCount = 0
        except KeyboardInterrupt:
            break
        except OSError:
            osErrorCount += 1
            print('\n*** OS ERROR ({}) ***'.format(osErrorCount))
        except TypeError:
            print('*** FAILED TO GET RESPONSE! ***')
            pass
        
        if not args.loop:
            break

        time.sleep(0.5)
