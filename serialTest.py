#!/usr/bin/env python3

from ubloxMessage import UbloxMessage
import serial
import serial.threaded
import time
import traceback
import sys
import logging

import datetime

# messageType = 'MON-VER'
# length = 0
# data = []
# message = UbloxMessage.buildMessage(messageType, length, data)

# with serial.Serial('/dev/ttyHS1', 115200, timeout=1) as ser:
#     while True:
#         try:
#             ser.write(message)
#             # time.sleep(0.01)
#         except KeyboardInterrupt:
#             break
        
# testBuffer = b''

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
        if (self.pollTarget is not None) and (msgFormat == self.pollTarget):
            self.pollResult = (msgFormat, msgData)
            self.pollTarget = None
        else:
            logging.debug('Ignoring {}\n'.format(msgFormat))

    def poll(self, msgFormat, ser):
        length = 0
        data = []
        message = UbloxMessage.buildMessage(msgFormat, length, data)

        self.pollResult = None
        self.pollTarget = msgFormat
        ser.write(message)
        
        while self.pollResult is None:
            time.sleep(0.01)

        return self.pollResult


ser = serial.Serial('/dev/ttyHS1', 115200, timeout=1)
with serial.threaded.ReaderThread(ser, UbloxReader) as protocol:
    while True:
        try:
            msgFormat, msgData = protocol.poll('MON-VER', ser)
            UbloxMessage.printMessage(msgFormat, msgData, header=datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]\n'))
            time.sleep(0.1)
        except KeyboardInterrupt:
            break

    # while True:
    #     try:
    #         time.sleep(1)
    #     except KeyboardInterrupt:
    #         break

