#!/usr/bin/env python3

from ubloxMessage import UbloxMessage, CLIDPAIR
import serial
import serial.threaded
import time
import traceback
import logging

import datetime

class UbloxReader(serial.threaded.Protocol):
    def __init__(self):
        self.buffer = b''
        self.start = 0
        self.pollResult = None
        self.pollTarget = None

    def connection_made(self, transport):
        super(UbloxReader, self).connection_made(transport)
        logging.debug('Port opened\n')

    def data_received(self, data):
        logging.debug('Received {} bytes'.format(len(data)))
        self.buffer = self.buffer + data
        logging.debug('Buffer size: {} bytes'.format(len(self.buffer)))
        self.parse()

    def connection_lost(self, exc):
        if exc:
            traceback.print_exc(exc)
        logging.debug('Port closed\n')

    def parse(self):
        index = self.buffer.find(b'\xb5\x62')
        if index >= 0:
            self.start += index
            result = UbloxMessage.validate(self.buffer[self.start:])
            if result['valid']:
                msgFormat, msgData, remainder = UbloxMessage.parse(self.buffer[self.start:])
                self.buffer = remainder if remainder is not None else b''
                self.start = 0
                self.handle_message(msgFormat, msgData)
            else:
                # Invalid message, move past sync bytes
                if result['lengthMatch']:
                    self.buffer = self.buffer[self.start+2:]
        # Discard all but the last byte
        else:
            self.buffer = self.buffer[-1:]
            self.start = 0

    def handle_message(self, msgFormat, msgData):
        if (self.pollTarget is not None) and (msgFormat in self.pollTarget):
            self.pollResult = (msgFormat, msgData)
            self.pollTarget = None
        else:
            logging.debug('Ignoring {}\n'.format(msgFormat))

    def poll(self, ser, msgFormat, length=0, data=[], timeout=0.5, maxRetries=20):
        retries = 0
        while retries < maxRetries:        
            self.pollResult = None
            self.pollTarget = [msgFormat]

            logging.info('Polling for {} (attempt {})'.format(msgFormat, retries+1))
            self.sendMessage(ser, msgFormat, length, data)

            startTime = time.time()
            while self.pollResult is None:
                time.sleep(0.01)
                if (time.time() - startTime) > timeout:
                    logging.warn('Timeout waiting for response!')
                    break

            if self.pollResult is not None:
                return self.pollResult

            retries += 1

        raise Exception('Failed to get response!')

    def sendConfig(self, ser, msgFormat, length, data, timeout=0.5, maxRetries=20):
        retries = 0
        while retries < maxRetries:
            self.pollResult = None
            self.pollTarget = ['ACK-ACK', 'ACK-NACK']

            logging.info('Sending config message {} (attempt {})'.format(msgFormat, retries+1))
            self.sendMessage(ser, msgFormat, length, data)

            startTime = time.time()
            while self.pollResult is None:
                time.sleep(0.01)
                if (time.time() - startTime) > timeout:
                    logging.warn('Timeout waiting for ACK')
                    break

            if self.pollResult is not None:
                if self.checkAck(self.pollResult[0], self.pollResult[1], msgFormat):
                    logging.info('Config message ACKed by ublox')
                return

            retries += 1

        raise Exception('Failed to set configuration!')

    def sendMessage(self, ser, msgFormat, length, data):
        message = UbloxMessage.buildMessage(msgFormat, length, data)
        ser.write(message)

    def checkAck(self, ackMessageType, ackData, cfgMessageType):
        if ackMessageType == 'ACK-NACK':
            raise Exception('ublox receiver responded with ACK-NACK!')

        if ackMessageType != 'ACK-ACK':
            raise ValueError('This is not an ACK-ACK or ACK-NACK message! ({})\n{}'.format(ackMessageType, ackData))

        clsId, msgId = CLIDPAIR[cfgMessageType]
        if ackData[0]['ClsID'] != clsId or ackData[0]['MsgID'] != msgId:
            raise ValueError('ublox receiver ACKed a different message ({}, {})!'.format(data[0]['ClsID'], data[0]['MsgID']))

        return True


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', '-d', default='/dev/ttyHS1', help='Specify the serial port device to communicate with. e.g. /dev/ttyO5')
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

    ser = serial.Serial(args.device, 115200, timeout=1)

    with serial.threaded.ReaderThread(ser, UbloxReader) as protocol:
        while True:
            try:
                msgFormat, msgData = protocol.poll(ser, 'MON-VER')
                UbloxMessage.printMessage(msgFormat, msgData, header=datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]\n'))
                time.sleep(0.1)
            except KeyboardInterrupt:
                break
