#!/usr/bin/env python 

import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

def parseSvInfo(svInfo):
    epoch = []
    numSats = []
    avgCNO = []
    for info in svInfo:
        cno = []
        for sv in info[1:]:
            if sv['Flags'] & 1:
                cno.append(sv['CNO'])
        epoch.append(info[0]['ITOW']/1e3)
        numSats.append(len(cno))
        if len(cno):
            avgCNO.append(np.mean(cno))
        else:
            avgCNO.append(0)

    return epoch, numSats, avgCNO

def parseDopInfo(dopInfo):
    epoch = [packet[0]['ITOW']/1e3 for packet in dopInfo] 
    hdop = [packet[0]['HDOP']/100. for packet in dopInfo]
    vdop = [packet[0]['VDOP']/100. for packet in dopInfo]
    pdop = [packet[0]['PDOP']/100. for packet in dopInfo]
    return epoch, hdop, vdop, pdop

def parsePvtInfo(pvtInfo):
    epoch = [packet[0]['ITOW']/1e3 for packet in pvtInfo]
    lat = [packet[0]['LAT']/1e7 for packet in pvtInfo]
    lon = [packet[0]['LON']/1e7 for packet in pvtInfo]
    alt = [packet[0]['HEIGHT']/1e3 for packet in pvtInfo]
    heading = [packet[0]['HeadVeh']/1e5 for packet in pvtInfo]
    speed = [packet[0]['Speed']/1e3 for packet in pvtInfo]
    hAcc = [packet[0]['Hacc']/1e3 for packet in pvtInfo]
    hAcc = [packet[0]['Hacc']/1e3 for packet in pvtInfo]
    vAcc = [packet[0]['Vacc']/1e3 for packet in pvtInfo]
    sAcc = [packet[0]['SAcc']/1e3 for packet in pvtInfo]
    headAcc = [packet[0]['HeadAcc']/1e5 for packet in pvtInfo]
    return epoch, lat, lon, alt, heading, speed, hAcc, vAcc, sAcc, headAcc

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    args = parser.parse_args()

    f = open(args.input, 'rb')
    data = pickle.load(f)

    numSats = avgCNO = None
    try:
        svInfo = data['NAV-SVINFO']
        epoch, numSats, avgCNO = parseSvInfo(svInfo)
    except KeyError:
        print('*** NO NAV-SVINFO messages!')
        epoch = numSats = avgCNO = []
    try:
        dopInfo = data['NAV-DOP']
        epochDop, hdop, vdop, pdop = parseDopInfo(dopInfo)
    except KeyError:
        print('*** NO NAV-DOP messages!')
        epochDop = hdop = vdop = pdop = []
    try:
        pvtInfo = data['HNR-PVT']
        epochPvt, lat, lon, alt, heading, speed, hAcc, vAcc, sAcc, headAcc = parsePvtInfo(pvtInfo)
    except KeyError:
        print('*** NO HNR-PVT messages!')
        epochPvt = lat = lon = alt = heading = speed = hAcc = vAcc = sAcc = headAcc = []

    numMessages = len(data['HNR-PVT']) if 'HNR-PVT' in data else 0
    print('# HNR-PVT messages: {}'.format(numMessages))
    if numSats is not None:
        print('# sats - mean: {:.3f}, std: {:.3f}, min: {:.3f}, max: {:.3f}'.format(np.mean(numSats), np.std(numSats), np.min(numSats), np.max(numSats)))
    if avgCNO is not None:
        print('Average C/No - mean: {:.3f}, std: {:.3f}, min: {:.3f}, max: {:.3f}'.format(np.mean(avgCNO), np.std(avgCNO), np.min(avgCNO), np.max(avgCNO)))
    
    fig, ax = plt.subplots(7, sharex=True)
    ax[0].plot(epoch, numSats, color='r')
    ax[0].set_ylim([0, None])
    ax[0].set_ylabel('# Sats')
    ax[0].grid(True)
    
    ax[1].plot(epoch, avgCNO, color='g')
    ax[1].set_ylim([0, 50])
    ax[1].set_ylabel('Average C/No')
    ax[1].grid(True)

    ax[2].plot(epochDop, hdop, color='b')
    ax[2].set_ylim([0, 5])
    ax[2].set_ylabel('HDOP')
    ax[2].grid(True)

    ax[3].plot(epochPvt, hAcc, color='b')
    # ax[3].set_ylim([0, 5])
    ax[3].set_ylabel('HAcc (m)')
    ax[3].grid(True)

    ax[4].plot(epochPvt, vAcc, color='b')
    # ax[4].set_ylim([0, 5])
    ax[4].set_ylabel('VAcc (m)')
    ax[4].grid(True)

    ax[5].plot(epochPvt, np.array(sAcc)  / 0.44704, color='b')
    # ax[5].set_ylim([0, 5])
    ax[5].set_ylabel('SAcc (MPH)')
    ax[5].grid(True)

    ax[6].plot(epochPvt, headAcc, color='b')
    # ax[6].set_ylim([0, 5])
    ax[6].set_ylabel('HeadAcc (deg)')
    ax[6].grid(True)

    ax[-1].set_xlabel('GPS Epoch (sec)')

    fig, ax = plt.subplots(6, sharex=True)
    ax[0].plot(epochPvt, lat, color='r')
    # ax[0].set_ylim([0, None])
    ax[0].set_ylabel('Latitude (deg)')
    ax[0].grid(True)

    ax[1].plot(epochPvt, lon, color='g')
    # ax[1].set_ylim([0, None])
    ax[1].set_ylabel('Longitude (deg)')
    ax[1].grid(True)

    ax[2].plot(epochPvt, alt, color='b')
    # ax[2].set_ylim([0, None])
    ax[2].set_ylabel('Height (m)')
    ax[2].grid(True)

    majorLocator = MultipleLocator(90)
    ax[3].plot(epochPvt, heading, color='c')
    ax[3].yaxis.set_major_locator(majorLocator)
    ax[3].set_ylim([0, 360])
    ax[3].set_ylabel('Heading (deg)')
    ax[3].grid(True)

    ax[4].plot(epochPvt, hAcc, color='b')
    # ax[4].set_ylim([0, 5])
    ax[4].set_ylabel('HAcc (m)')
    ax[4].grid(True)

    ax[5].plot(epochPvt, np.array(speed) / 0.44704, color='m')
    # ax[5].set_ylim([0, None])
    ax[5].set_ylabel('Speed (MPH)')
    ax[5].grid(True)

    ax[-1].set_xlabel('GPS Epoch (sec)')

    plt.show()
