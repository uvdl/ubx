#!/usr/bin/env python3

from ubloxMessage import UbloxMessage
from smbus2 import SMBusWrapper
import time
import logging

def readBytesAvailable(bus):
    block = bus.read_i2c_block_data(0x42, 0xfd, 2)
    bytesAvailable = (block[0] << 8) + block[1]

    return bytesAvailable

def readBytes(bus, numBytes):
    numBlocks, remainder = divmod(numBytes, 32)

    i = 0

    data = []

    while i < numBlocks:
        block = bus.read_i2c_block_data(0x42, 0xff, 32)
        data.extend(block)
        i += 1

    if remainder > 0:
        block = bus.read_i2c_block_data(0x42, 0xff, remainder)
        data.extend(block)

    return data

def printHex(block, header=True):
    numBlocks, remainder = divmod(len(block), 16)

    i = 0
    while i < numBlocks:
        hexString = ' '.join('{:02x}'.format(x) for x in block[16*i:16*i+8])
        hexString += ' '
        hexString += ' '.join('{:02x}'.format(x) for x in block[16*i+8:16*i+16])
        
        if header:    
            hexString = '{:02d}) '.format(i) + hexString

        print(hexString)

        i += 1

    if remainder > 0:
        hexString = ' '.join('{:02x}'.format(x) for x in block[16*i:16*i+8])
        if remainder > 8:
            hexString += ' '
            hexString += ' '.join('{:02x}'.format(x) for x in block[16*i+8:16*i+16])
        if header:
            hexString = '{:02d}) '.format(i) + hexString
        print(hexString)  

class UbloxI2C(object):
    def __init__(self, bus, ubloxAddress=0x42):
        self.bus = bus
        self.ubloxAddress = ubloxAddress

    def poll(self, messageType):
        logging.info('Polling for {}...'.format(messageType))

        bytesAvailable = readBytesAvailable(bus)
        if bytesAvailable > 0:
            logging.info('Dumping buffer [{} bytes]...'.format(bytesAvailable))
            readBytes(bus, bytesAvailable)
        
        message = UbloxMessage.buildMessage(messageType, 0, [])
        bus.write_i2c_block_data(0x42, 0xff, message)
        
        time.sleep(0.01)

        bytesAvailable = readBytesAvailable(bus)

        if bytesAvailable == 0:
            raise Exception('Failed to get response!')
        else:
            logging.info('Bytes available: {}'.format(bytesAvailable))
        
        message = readBytes(bus, bytesAvailable)
        msgFormat, data, remainder = UbloxMessage.parse(message)

        if msgFormat != messageType:
            raise Exception('Response was of a different type! Got {} instead of {}!'.format(msgFormat, messageType))

        return data

    def sendConfig(self, messageType, size, packet):
        pass


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bus', '-b', type=int, default=11, help='I2C bus number')
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    with SMBusWrapper(args.bus) as bus:
        ublox = UbloxI2C(args.bus)
        data = ublox.poll('MON-VER')

        print('    Software version: {}'.format(data[0]['SWVersion'].decode('ascii').strip()))
        print('    Hardware version: {}'.format(data[0]['HWVersion'].decode('ascii').strip()))
        for i in range(1, len(data)):
            print('    Extension: {}'.format(data[i]['Extension'].decode('ascii').strip()))
