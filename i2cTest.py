#!/usr/bin/env python3

from ubloxMessage import UbloxMessage
from smbus2 import SMBusWrapper
import time

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

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--bus', '-b', type=int, default=11, help='I2C bus number')
    args = parser.parse_args()

    with SMBusWrapper(args.bus) as bus:
        bytesAvailable = readBytesAvailable(bus)
        if bytesAvailable > 0:
            print('\nDumping buffer [{} bytes]...'.format(bytesAvailable))
            readBytes(bus, bytesAvailable)

        # Send MON-VER
        print('\nSending MON-VER request...')
        message = UbloxMessage.buildMessage("MON-VER", 0, [])
        printHex(message, False)
        bus.write_i2c_block_data(0x42, 0xff, message)
        
        time.sleep(0.01)
        
        bytesAvailable = readBytesAvailable(bus)
        print('\nBytes available: {}'.format(bytesAvailable))
        
        message = readBytes(bus, bytesAvailable)
        msgFormat, data, remainder = UbloxMessage.parse(message)
        print('\nReceived message: {}'.format(msgFormat))
        if msgFormat == 'MON-VER':
            print('    Software version: {}'.format(data[0]['SWVersion'].decode('ascii').strip()))
            print('    Hardware version: {}'.format(data[0]['HWVersion'].decode('ascii').strip()))
            for i in range(1, len(data)):
                print('    Extension: {}'.format(data[i]['Extension'].decode('ascii').strip()))
        else:
            for dictionary in data:
                print(dictionary)

        if remainder is not None:
            print('\nRemainder [{} bytes]...'.format(len(remainder)))
            printHex(remainder)
