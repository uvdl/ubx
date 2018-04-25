def parseCfgMsg(packets):
    requests = {}
    responses = {}
    active = {}
    for packet in packets:
        msgClass = packet[0]['msgClass']
        msgId = packet[0]['msgId']
        if len(packet) == 1:
            requests[msgClass, msgId] = packet[0]
        elif len(packet) > 1:
            response = packet[0]
            rates = [el['rate'] for el in packet[1:]]
            response['rates'] = rates
            responses[msgClass, msgId] = response
            if np.any(rates):
                active[msgClass, msgId] = response
    return requests, responses, active

def parseCfgPrt(cfgPrtInfo):
    portInfo = {}
    for packet in cfgPrtInfo:
        if len(packet) == 2:
            portInfo[packet[1]['PortID']] = packet[1]

    return portInfo

if __name__=='__main__':
    import ubx
    import numpy as np
    import matplotlib.pyplot as plt
    import pickle
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    args = parser.parse_args()

    f = open(args.input, 'rb')
    data = pickle.load(f)

    cfgMsgInfo = data['CFG-MSG']

    requests, responses, active = parseCfgMsg(cfgMsgInfo)

    cfgPrtInfo = data['CFG-PRT']
    portInfo = parseCfgPrt(cfgPrtInfo)

    print('Requests: {}'.format(len(requests)))
    print('Responses: {} / Missing responses: {}'.format(len(responses), len(requests) - len(responses)))
    print('Active: {}'.format(len(active)))

    for key in sorted(active.keys()):
        messageName = ubx.CLIDPAIR_INV[key]
        rateStrings = ['{}: {}'.format(i, rate) for i, rate in enumerate(active[key]['rates'])]
        rateString = ' | '.join(rateStrings)
        print('{:10}: {}'.format(messageName, rateString))

    print('\nMissing responses:')
    for msgClsId in sorted(requests.keys()):
        if msgClsId not in responses:
            messageName = ubx.CLIDPAIR_INV[msgClsId] if msgClsId in ubx.CLIDPAIR_INV else 'UNKNOWN'
            print('{:10}:{}, {}'.format(messageName, hex(msgClsId[0]), hex(msgClsId[1])))

    print('\nBy port')
    for portId in sorted(portInfo.keys()):
        portName = ubx.PORTID_INV[portId]
        print('{}: Baud Rate: {}'.format(portName, portInfo[portId]['Baudrate']))
        for key in sorted(active.keys()):
            if active[key]['rates'][portId] > 0:
                messageName = ubx.CLIDPAIR_INV[key]
                print('    {:10}: {}'.format(messageName, active[key]['rates'][portId]))

