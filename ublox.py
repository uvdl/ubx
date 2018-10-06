import ubx
import gobject
import logging
import time

class Ublox(object):
    def __init__(self, device, quiet=True):
        self.loop = gobject.MainLoop()
        self.pollMaxRetries = 3
        self.quiet = quiet
        self.requestedMessageTypes = None
        self.message = None
        if device is not None:
            self.parser = ubx.Parser(self._waitForMessage, device=device)
        else:
            self.parser = ubx.Parser(self._waitForMessage)

    def setBaudRate(self, baudRate, baudRatesToTry=[9600, 115200]):
        for hostBaudRate in baudRatesToTry:
            # Set the host baud rate
            logging.info('Setting host baud rate to {}...'.format(hostBaudRate))
            self.parser.setBaudRate(hostBaudRate)
            # time.sleep(0.01)
                
            # Does this baud rate match the ublox?
            packet = self.poll('CFG-PRT')

            if packet is None:
                logging.info('No response at {} baud...'.format(hostBaudRate))
                continue
                
            logging.info('Received response at {} baud...'.format(hostBaudRate))
            if packet[1]['Baudrate'] == baudRate:
                logging.info('Baud rate is already set to the desired speed!')
                return True

            # Attempt to set the ublox baud rate
            newBaudRateRetries = 0
            while (newBaudRateRetries < 3):
                newBaudRateRetries += 1

                # Send CFG-PRT to configure the ublox baud rate
                logging.info('Attempting to configure the ublox to {} baud...'.format(baudRate))
                packet[1]['Baudrate'] = baudRate
                temp = self.sendConfig('CFG-PRT', 20, packet, maxRetries=1)
                time.sleep(0.1)

                # Set the host to the desired baud rate
                logging.info('Switching host baud rate to {}...'.format(baudRate))
                self.parser.setBaudRate(baudRate)
                
                # Poll for CFG-PRT
                newPacket = self.poll('CFG-PRT')
                if newPacket is not None:
                    if newPacket[1]['Baudrate'] == baudRate:
                        logging.info('Baud rate successfully set!')
                        return True
                else:
                    logging.info('Failed to set the ublox baud rate!')

                # Set the host to the desired baud rate
                logging.info('Resetting host baud rate to {}...'.format(hostBaudRate))
                self.parser.setBaudRate(hostBaudRate)
                
        raise Exception('Failed to set baud rate!')

    def poll(self, messageType, maxRetries=5, timeout=100):
        logging.info('Polling for {}...'.format(messageType))

        retries = 0
        while retries < maxRetries:
            self.message = None

            # Configure timeout
            timeoutSourceId = gobject.timeout_add(timeout, self._timeout)

            # Send poll message
            self.requestedMessageTypes = [messageType]
            self.parser.send(messageType, 0, [])

            # Look for response
            self.loop.run()

            # Clear timeout
            timeoutTriggered = self._clearTimeout(timeoutSourceId)

            if self.message is not None:
                ty, packet = self.message
                return packet

            retries += 1
            logging.info('retries: {}'.format(retries))
            time.sleep(0.1)

        return None

    def sendConfig(self, messageType, size, packet, maxRetries=5, timeout=100):
        logging.info('Sending {}...'.format(messageType))

        retries = 0
        while retries < maxRetries:
            self.message = None
            # Configure timeout
            timeoutSourceId = gobject.timeout_add(timeout, self._timeout)

            # Send config message
            self.requestedMessageTypes = ['ACK-ACK', 'ACK-NACK']
            self.parser.send(messageType, size, packet)

            # Look for response
            self.loop.run()

            # Clear timeout
            timeoutTriggered = self._clearTimeout(timeoutSourceId)

            if self.message is not None:
                ty, newPacket = self.message

                # Validate that the ACK is for our CFG message
                clsId, msgId = ubx.CLIDPAIR[ty]
                if newPacket[0]['ClsID'] != clsId or newPacket[0]['MsgID'] != msgId:
                    continue

                if ty == 'ACK-NACK':
                    raise Exception('ublox receiver responded with {}!'.format(ty))

                logging.info('Config message acknowledged by ublox.')
                return newPacket

            retries += 1
            # print('retries: {}'.format(retries))

        return None

    def _timeout(self):
        self.loop.quit()

    def _clearTimeout(self, sourceId):
        timeoutTriggered = True
        context = self.loop.get_context()
        if self.message is not None:
            gobject.source_remove(sourceId)
            timeoutTriggered = False
        return timeoutTriggered
    
    def _waitForMessage(self, ty, packet):
        logging.debug("Received %s" % repr([ty, packet]))
        if ty in self.requestedMessageTypes:
            self.message = ty, packet
            self.loop.quit()
