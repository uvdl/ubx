#!/usr/bin/env python2

# Get AssistNow Online data
# Valid for 2-4 hours
# Size: 1-3 KB
# Improves TTFF to 3 seconds (typical)

# curl https://online-live1.services.u-blox.com/GetOnlineData.ashx?token=kdIs4xBnwEivvK3aQJtY9g;gnss=gps,glo;datatype=eph,alm,aux;

# AssistNow Online servers:
# https://online-live1.services.u-blox.com
# https://online-live2.services.u-blox.com

# Token (Mapper - John Kua): kdIs4xBnwEivvK3aQJtY9g

import requests
import ubx

validGnss = ['gps', 'qzss', 'glo', 'bds', 'gal']
validDatatypes = ['eph', 'alm', 'aux', 'pos']

def getOnlineData(hostUrl, token, gnss=['gps', 'glo'], datatypes=['eph', 'alm', 'aux']):
    for g in gnss:
        if g not in validGnss:
            raise ValueError('{} is not a valid GNSS! Must be one of {}'.format(g, validGnss))
    for d in datatypes:
        if d not in validDatatypes:
            raise ValueError('{} is not a valid datatype! Must be one of {}'.format(d, validDatatypes))


    url = hostUrl
    url += '/GetOnlineData.ashx?'
    url += 'token={};'.format(token)
    url += 'datatype={};'.format(','.join(datatypes))
    url += 'format=mga;'
    url += 'gnss={};'.format(','.join(gnss))
    response = requests.get(url)

    if not response.ok:
        raise Exception('Failed to get data from {}'.format(hostUrl))

    return response.content

def callback(ty, packet):
    print("callback %s" % repr([ty, packet]))

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', '-d', default=None)
    parser.add_argument('--hostUrl', '-H', default='https://online-live1.services.u-blox.com')
    parser.add_argument('--token', '-t', default='kdIs4xBnwEivvK3aQJtY9g')
    args = parser.parse_args()

    data = getOnlineData(args.hostUrl, token='kdIs4xBnwEivvK3aQJtY9g')
    print('Received ({}):\n{}'.format(len(data), data))

    import pdb; pdb.set_trace()

    if args.device is not None:
        t = ubx.Parser(callback, device=args.device)
    else:
        t = ubx.Parser(callback, device=None)

    t.parse(data)

    messageCount = 0
    while len(data) > 0:
        data = t.seekToNextUbxMessage(data)
        result = t.checkUbx(data)
        print(result)
        if result['sync'] == True:
            data = data[result['length']:]
            messageCount += 1
        else:
            print('Remaining buffer ({}): {}'.format(len(data), data))
            break
    print('Messages parsed: {}'.format(messageCount))

    # Send CFG-NAVX5 to enable ackAiding?

    # t.sendraw(data)
