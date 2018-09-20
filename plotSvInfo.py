#!/usr/bin/env python 

import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import struct

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

def parseAttInfo(attInfo):
    epoch = [packet[0]['ITOW']/1e3 for packet in attInfo]
    roll = [packet[0]['Roll']/1e5 for packet in attInfo]
    pitch = [packet[0]['Pitch']/1e5 for packet in attInfo]
    heading = [packet[0]['Heading']/1e5 for packet in attInfo]
    rollAcc = [packet[0]['AccRoll']/1e5 for packet in attInfo]
    pitchAcc = [packet[0]['AccPitch']/1e5 for packet in attInfo]
    headingAcc = [packet[0]['AccHeading']/1e5 for packet in attInfo]

    return epoch, roll, pitch, heading, rollAcc, pitchAcc, headingAcc

def parseInsInfo(insInfo, offset):
    epoch = [packet[0]['ITOW']/1e3 + offset for packet in insInfo] 
    reserved = [packet[0]['Reserved'] for packet in insInfo]
    xAngRate = [packet[0]['XAngRate']/1e3 for packet in insInfo]
    yAngRate = [packet[0]['YAngRate']/1e3 for packet in insInfo]
    zAngRate = [packet[0]['ZAngRate']/1e3 for packet in insInfo]
    xAccel = [packet[0]['XAccel']/1e3 for packet in insInfo]
    yAccel = [packet[0]['YAccel']/1e3 for packet in insInfo]
    zAccel = [packet[0]['ZAccel']/1e3 for packet in insInfo]
    bitfields = [packet[0]['Bitfield0'] for packet in insInfo]
    version = [bf & 0xF for bf in bitfields]
    angRateValid = [(bool(bf & 0x10), bool(bf & 0x20), bool(bf & 0x40)) for bf in bitfields]
    accelValid = [(bool(bf & 0x80), bool(bf & 0x100), bool(bf & 0x200)) for bf in bitfields]

    return epoch, xAngRate, yAngRate, zAngRate, xAccel, yAccel, zAccel, version, angRateValid, accelValid, reserved

def parseMeasInfo(measInfo, sssToEpochPoly, offset):
    timeTag = [packet[0]['TimeTag']/1e3 for packet in measInfo]
    epoch = sssToEpochPoly(timeTag) + offset
    flags = [packet[0]['Flags'] for packet in measInfo]
    calibTagValid = [bool(f & 0x8) for f in flags]
    timeMarkSent = [f & 0x3 for f in flags]
    timeMarkEdge = [bool(f & 0x4) for f in flags]
    timeMarkData = {'epoch': epoch, 'timeTag': timeTag, 'timeMarkSent': timeMarkSent, 'timeMarkEdge': timeMarkSent}
    data = [[subpacket['Data'] for subpacket in packet[1:]] for packet in measInfo]
    calibTimeTag = []
    gyroData = {'epoch': [], 'timeTag': [], 'calibTimeTag': []}
    accelData = {'epoch': [], 'timeTag': [], 'calibTimeTag': []}
    tickData = {'epoch': [], 'timeTag': [], 'calibTimeTag': []}
    for ep, tTag, dSet, valid in zip(epoch, timeTag, data, calibTagValid):
        d, cTag = parseMeasData(dSet, valid)

        if 'Acceleration' in d.keys()[0]:
            dataDict = accelData
        elif 'Angular' in d.keys()[0] or 'gyro' in d.keys()[0]:
            dataDict = gyroData
        else:
            dataDict = tickData

        dataDict['epoch'].append(ep)
        dataDict['timeTag'].append(cTag)
        dataDict['calibTimeTag'].append(cTag)
        for dataTypeName, value in d.items():
            if dataTypeName not in dataDict:
                dataDict[dataTypeName] = []
            dataDict[dataTypeName].append(value)

    return accelData, gyroData, tickData, timeMarkData

def parseMeasData(dSet, timeTagPresent=True):
    dataDict = {}
    if timeTagPresent:
        timeTag = dSet[-1]/1e3
        dSet = dSet[:-1]
    else:
        timeTag = None
    for d in dSet:
        dataType, dataTypeName, value = parseEsfData(d)
        dataDict[dataTypeName] = value

    return dataDict, timeTag

def parseRawInfo(rawInfo, sssToEpochPoly, offset):
    # Each message contains 10 sets of 7 measurements (3 axis accel, 3 axis gyro, gyro temp)
    # The time for each set of 7 measurements appear to be the same
    timeTag = [packet[0]['Reserved']/1e3 for packet in rawInfo]
    epoch = sssToEpochPoly(timeTag) + offset
    data = [[subpacket['Data'] for subpacket in packet[1:]] for packet in rawInfo]
    sensorTimeTag = [[subpacket['STimeTag'] for subpacket in packet[1:]] for packet in rawInfo]
    sensorTimeTag = np.array(sensorTimeTag)

    # Unwrap sensorTimeTag (roll over every 2^24)
    sensorTimeTag = sensorTimeTag.flatten()
    deltaTimeTag = np.diff(sensorTimeTag)
    for i in np.where(deltaTimeTag < 0)[0]:
        sensorTimeTag[i+1:] = sensorTimeTag[i+1:] + 2**24
    # sensorTimeTag = sensorTimeTag.reshape(-1, 70)

    # Perform a piecewise linear fit of the sensor time tags to the epoch times
    deltaEpoch = epoch[-1] - epoch[0]
    deltaTimeTag = sensorTimeTag[-1] - sensorTimeTag[0]
    scale = deltaEpoch / deltaTimeTag# * 1.002
    print('scale: {}'.format(scale))
    sensorEpoch = (sensorTimeTag - sensorTimeTag[0]) * scale + epoch[0]

    # Reshape to the number of measurements
    sensorEpoch = sensorEpoch.reshape(-1, 7)
    sensorTimeTag = sensorTimeTag.reshape(-1, 7)

    # plt.plot(np.diff(sensorEpoch.flatten()))
    # plt.show()
    data = np.array(data).reshape(-1, 7)
    dataDict = {'sensorTimeTag': [], 'epoch': []}
    for timeSet, epochSet, dataSet in zip(sensorTimeTag, sensorEpoch, data):
        if not np.all(timeSet == timeSet[0]):
            raise Exception('Not all time values in set are the same! Expected to be the same in one measurement set!')
        tag = timeSet[0]
        curEpoch = epochSet[0]
        dataDict['sensorTimeTag'].append(tag)
        dataDict['epoch'].append(curEpoch)

        for d in dataSet:
            dataType, dataTypeName, value = parseEsfData(d)
            if dataTypeName not in dataDict:
                dataDict[dataTypeName] = []
            dataDict[dataTypeName].append(value)

    return dataDict

def parseEsfData(data):
    dataTypeToName = {0: 'noData', 1: 'reserved', 2: 'reserved', 3: 'reserved', 4: 'reserved',
                      5: 'zAngularRate',
                      6: 'frontLeftWheelTicks',
                      7: 'frontRightWheelTicks',
                      8: 'rearLeftWheelTicks',
                      9: 'rearRightWheelTicks',
                      10: 'singleTick',
                      11: 'speed', 
                      12: 'gyroTemp',
                      13: 'yAngularRate',
                      14: 'xAngularRate',
                      16: 'xAcceleration',
                      17: 'yAcceleration',
                      18: 'zAcceleration'}
    scalingDict = {0: None, 1: None, 2: None, 3: None, 4: None,
                   5: 2**-12,
                   6: None, 7: None, 8: None, 9: None, 10: None,
                   11: 1e-3,
                   12: 1e-2,
                   13: 2**-12,
                   14: 2**-12,
                   16: 2**-10,
                   17: 2**-10,
                   18: 2**-10}
    signedDict = {0: None, 1: None, 2: None, 3: None, 4: None,
                   5: True,
                   6: None, 7: None, 8: None, 9: None, 10: None,
                   11: True,
                   12: True,
                   13: True,
                   14: True,
                   16: True,
                   17: True,
                   18: True}

    dataType = data >> 24
    dataTypeName = dataTypeToName[dataType]
    dataField = data & 0xFFFFFF
    if signedDict[dataType]:
        dataBytes = struct.pack('<I', dataField)
        signedBytes = dataBytes[:-1] + ('\x00' if dataBytes[2] < '\x80' else '\xff')
        dataField = struct.unpack('<i', signedBytes)[0]

    if scalingDict[dataType] is not None:
        value = dataField * scalingDict[dataType]
    else:
        # Tick data: unsigned value is in bits 0-22
        # bit 23 indicates direction - 0 forward, 1 backward
        sign = bool(dataField >> 23)
        sign = -1 if sign else 1
        value = sign * (dataField & 0x7FFFFF)

    return dataType, dataTypeName, value

def parseNavStatus(status):
    epoch = [packet[0]['ITOW']/1e3 for packet in status] 
    fixType = [packet[0]['GPSfix'] for packet in status]
    flags = [packet[0]['Flags'] for packet in status]
    fixStatus = [packet[0]['DiffS'] for packet in status]
    ttff = [packet[0]['TTFF'] for packet in status]
    msss = [packet[0]['MSSS'] for packet in status]
    return epoch, fixType, flags, fixStatus, ttff, msss

def piecewiseAccumulation(pose, delta, offsetTime=0):
    rate = len(delta) / len(pose)
    if offsetTime > 0:
        offset = offsetTime * rate
        deltaOffset = np.hstack([np.zeros(offset), np.array(delta)[:-offset]])
    elif offsetTime < 0:
        offset = -offsetTime * rate
        deltaOffset = np.hstack([np.array(delta)[offset:], np.zeros(offset)])
    else:
        deltaOffset = delta
    deltaReshaped = np.array(deltaOffset)[:len(pose)*rate].reshape(-1, rate) / float(rate)
    accumulatedDeltas = np.cumsum(deltaReshaped, 1)
    accumulatedDeltas = np.hstack([np.zeros([accumulatedDeltas.shape[0], 1]), accumulatedDeltas[:,:-1]])
    interpolated = np.array(pose).reshape(len(pose), 1) + accumulatedDeltas
    
    return interpolated.flatten()

def piecewiseAccumulation2(poseTimes, poses, rateTimes, rates):
    rateTimes = np.array(rateTimes)
    rates = np.array(rates)
    poseTimes = np.vstack([poseTimes[:-1], poseTimes[1:]]).transpose()
    poses = np.vstack([poses[:-1], poses[1:]]).transpose()
    output = []
    outputTimes = []
    for (startTime, endTime), (startPose, endPose) in zip(poseTimes, poses):
        idx = (rateTimes >= startTime) & (rateTimes < endTime)
        curRates = rates[idx]
        curRateTimes = rateTimes[idx]
        relRateTimes = curRateTimes - startTime
        relRateTimes[0] = 0
        relRateTimes = np.hstack([relRateTimes, endTime-startTime])
        newPoses = startPose + np.cumsum(np.diff(relRateTimes) * curRates)
        newTimes = (relRateTimes + startTime)[:-1]
        output.extend(newPoses)
        outputTimes.extend(newTimes)
    return outputTimes, output


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    args = parser.parse_args()

    f = open(args.input, 'rb')
    data = pickle.load(f)

    measOffset = -0.5
    insOffset = -0.5

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
        print('Length of HNR-PVT data (s): {:.3f}'.format(epochPvt[-1] - epochPvt[0]))
        print('--> First timestamp: {}'.format(epochPvt[0]))
    except KeyError:
        print('*** NO HNR-PVT messages!')
        epochPvt = lat = lon = alt = heading = speed = hAcc = vAcc = sAcc = headAcc = []
    try:
        attInfo = data['NAV-ATT']
        epochAtt, roll, pitch, headingAtt, rollAcc, pitchAcc, headingAcc = parseAttInfo(attInfo)
    except KeyError:
        print('*** NO NAV-ATT messages!')
        epochAtt = roll = pitch = headingAtt = rollAcc = pitchAcc = headingAcc = []
    try:
        statusInfo = data['NAV-STATUS']
        epochStatus, fixType, flags, fixStatus, ttff, msss = parseNavStatus(statusInfo)
        coeff = np.polyfit(np.array(msss)/1e3, epochStatus, 1)
        sssToEpochPoly = np.poly1d(coeff)
    except KeyError:
        print('*** NO NAV-STATUS messages!')
        epochStatus = fixType = flags = fixStatus = ttff = msss = []

    try:
        insInfo = data['ESF-INS']
        epochIns, xAngRate, yAngRate, zAngRate, xAccel, yAccel, zAccel, version, angRateValid, accelValid, reservedIns = parseInsInfo(insInfo, insOffset)
    except KeyError:
        print('*** NO ESF-INS messages!')
        epochIns = xAngRate = yAngRate = zAngRate = xAccel = yAccel = zAccel = version = angRateValid = accelValid = reservedIns = []
    try:
        measInfo = data['ESF-MEAS']
        accelDataMeas, gyroDataMeas, tickDataMeas, timeMarkData = parseMeasInfo(measInfo, sssToEpochPoly, measOffset)
        print('Length of ESF-MEAS data (s): {:.3f}'.format(accelDataMeas['timeTag'][-1] - accelDataMeas['timeTag'][0]))
        print('--> First timestamp: {}'.format(accelDataMeas['timeTag'][0]))

    except KeyError:
        print('*** NO ESF-MEAS messages!')
        accelDataMeas = gyroDataMeas = tickDataMeas = {}
    try:
        rawInfo = data['ESF-RAW']
        rawData = parseRawInfo(rawInfo, sssToEpochPoly, measOffset)
        print('Length of ESF-RAW data (s): {:.3f}'.format(rawData['epoch'][-1] - rawData['epoch'][0]))
        print('--> First timestamp: {}'.format(rawData['epoch'][0]))
    except KeyError:
        print('*** NO ESF-RAW messages!')
        rawData = {}

    numMessages = len(data['HNR-PVT']) if 'HNR-PVT' in data else 0
    print('# HNR-PVT messages: {}'.format(numMessages))
    numMessages = len(data['NAV-ATT']) if 'NAV-ATT' in data else 0
    print('# NAV-ATT messages: {}'.format(numMessages))
    if numSats is not None:
        print('# sats - mean: {:.3f}, std: {:.3f}, min: {:.3f}, max: {:.3f}'.format(np.mean(numSats), np.std(numSats), np.min(numSats), np.max(numSats)))
    if avgCNO is not None:
        print('Average C/No - mean: {:.3f}, std: {:.3f}, min: {:.3f}, max: {:.3f}'.format(np.mean(avgCNO), np.std(avgCNO), np.min(avgCNO), np.max(avgCNO)))

    outputData = {'epochAtt': epochAtt, 'roll': roll, 'pitch': pitch, 'headingAtt': headingAtt, 
                  'accelDataMeas': accelDataMeas, 'gyroDataMeas': gyroDataMeas, 
                  'rawData': rawData}

    import pdb; pdb.set_trace()

    import cPickle as pickle
    with open('outputData.pickle', 'w') as f:
        pickle.dump(outputData, f, -1)
    
    # fig, ax = plt.subplots(7, sharex=True)
    # ax[0].plot(epoch, numSats, color='r')
    # ax[0].set_ylim([0, None])
    # ax[0].set_ylabel('# Sats')
    # ax[0].grid(True)
    
    # ax[1].plot(epoch, avgCNO, color='g')
    # ax[1].set_ylim([0, 50])
    # ax[1].set_ylabel('Average C/No')
    # ax[1].grid(True)

    # ax[2].plot(epochDop, hdop, color='b')
    # ax[2].set_ylim([0, 5])
    # ax[2].set_ylabel('HDOP')
    # ax[2].grid(True)

    # ax[3].plot(epochPvt, hAcc, color='b')
    # # ax[3].set_ylim([0, 5])
    # ax[3].set_ylabel('HAcc (m)')
    # ax[3].grid(True)

    # ax[4].plot(epochPvt, vAcc, color='b')
    # # ax[4].set_ylim([0, 5])
    # ax[4].set_ylabel('VAcc (m)')
    # ax[4].grid(True)

    # ax[5].plot(epochPvt, np.array(sAcc)  / 0.44704, color='b')
    # # ax[5].set_ylim([0, 5])
    # ax[5].set_ylabel('SAcc (MPH)')
    # ax[5].grid(True)

    # ax[6].plot(epochPvt, headAcc, color='b')
    # # ax[6].set_ylim([0, 5])
    # ax[6].set_ylabel('HeadAcc (deg)')
    # ax[6].grid(True)

    # ax[-1].set_xlabel('GPS Epoch (sec)')

    # fig, ax = plt.subplots(6, sharex=True)
    # ax[0].plot(epochPvt, lat, color='r')
    # # ax[0].set_ylim([0, None])
    # ax[0].set_ylabel('Latitude (deg)')
    # ax[0].grid(True)

    # ax[1].plot(epochPvt, lon, color='g')
    # # ax[1].set_ylim([0, None])
    # ax[1].set_ylabel('Longitude (deg)')
    # ax[1].grid(True)

    # ax[2].plot(epochPvt, alt, color='b')
    # # ax[2].set_ylim([0, None])
    # ax[2].set_ylabel('Height (m)')
    # ax[2].grid(True)

    # majorLocator = MultipleLocator(90)
    # ax[3].plot(epochPvt, heading, color='c')
    # ax[3].yaxis.set_major_locator(majorLocator)
    # ax[3].set_ylim([0, 360])
    # ax[3].set_ylabel('Heading (deg)')
    # ax[3].grid(True)

    # ax[4].plot(epochPvt, hAcc, color='b')
    # # ax[4].set_ylim([0, 5])
    # ax[4].set_ylabel('HAcc (m)')
    # ax[4].grid(True)

    # ax[5].plot(epochPvt, np.array(speed) / 0.44704, color='m')
    # # ax[5].set_ylim([0, None])
    # ax[5].set_ylabel('Speed (MPH)')
    # ax[5].grid(True)

    # ax[-1].set_xlabel('GPS Epoch (sec)')

    fig, ax = plt.subplots(6, sharex=True)
    ax[0].plot(epochAtt, roll, color='r')
    ax[0].set_ylabel('Roll (deg)')
    ax[0].grid(True)

    ax[1].plot(epochAtt, pitch, color='g')
    ax[1].set_ylabel('Pitch (deg)')
    ax[1].grid(True)

    ax[2].plot(epochAtt, headingAtt, color='b')
    ax[2].set_ylabel('Heading (deg)')
    ax[2].grid(True)

    ax[3].plot(epochAtt, rollAcc, color='m')
    ax[3].set_ylabel('Roll Acc(deg)')
    ax[3].grid(True)

    ax[4].plot(epochAtt, pitchAcc, color='c')
    ax[4].set_ylabel('Pitch Acc(deg)')
    ax[4].grid(True)

    ax[5].plot(epochAtt, headingAcc, color='c')
    ax[5].set_ylabel('Heading Acc(deg)')
    ax[5].grid(True)

    fig, axes = plt.subplots(7, sharex=True)
    plotOrder = 'xAcceleration', 'yAcceleration', 'zAcceleration', 'xAngularRate', 'yAngularRate', 'zAngularRate', 'gyroTemp'
    for key, ax in zip(plotOrder, axes):
        if 'Acceleration' in key:
            if 'timeTag' in accelDataMeas:
                ax.plot(np.array(accelDataMeas['timeTag']), accelDataMeas[key], 'b', label='MEAS', zorder=10)
            if 'sensorTimeTag' in rawData:
                ax.plot(np.array(rawData['epoch']), rawData[key], 'r', label='RAW')
        elif 'Angular' in key or 'gyro' in key:
            if 'timeTag' in gyroDataMeas:
                ax.plot(np.array(gyroDataMeas['timeTag']), gyroDataMeas[key], 'b', label='MEAS', zorder=10)
            if 'sensorTimeTag' in rawData:
                ax.plot(np.array(rawData['epoch']), rawData[key], 'r', label='RAW')
        ax.set_ylabel(key)
        ax.legend()
    axes[-1].set_xlabel('Time Tag (sec)')

    # rollTimes, rollMeas = piecewiseAccumulation2(epochAtt, roll, gyroDataMeas['epoch'], np.array(gyroDataMeas['xAngularRate']))
    # rollRaw = piecewiseAccumulation(roll, -np.array(rawData['yAngularRate']))
    # # pitchMeas = piecewiseAccumulation(pitch, np.array(gyroDataMeas['xAngularRate']))
    # pitchTimes, pitchMeas = piecewiseAccumulation2(np.array(epochAtt)-epochAtt[0], pitch, np.array(gyroDataMeas['timeTag']) - rawData['epoch'][0], np.array(gyroDataMeas['xAngularRate']))
    # pitchRaw = piecewiseAccumulation(pitch, np.array(rawData['xAngularRate']))
    # headingMeas = piecewiseAccumulation(headingAtt, np.array(gyroDataMeas['zAngularRate']))
    # headingRaw = piecewiseAccumulation(headingAtt, np.array(rawData['zAngularRate']))

    headingTimes, headingMeas = piecewiseAccumulation2(epochAtt, headingAtt, gyroDataMeas['epoch'], np.array(gyroDataMeas['zAngularRate']))

    fig, ax = plt.subplots(3, sharex=True)
    ax[0].plot(np.array(epochAtt)[:-1], np.diff(roll), color='r', zorder=20, label='dRoll')
    ax[0].plot(np.array(epochIns), xAngRate, color='c', zorder=15, label='INS angular rate')
    ax[0].plot(np.array(gyroDataMeas['epoch']), -np.array(gyroDataMeas['yAngularRate']), color='b', zorder=10, label='MEAS angular rate')
    ax[0].legend()
    ax[1].plot(np.array(epochAtt)[:-1], np.diff(pitch), color='r', zorder=20, label='dPitch')
    ax[1].plot(np.array(epochIns), yAngRate, color='c', zorder=15, label='INS angular rate')
    ax[1].plot(np.array(gyroDataMeas['epoch']), np.array(gyroDataMeas['xAngularRate']), color='b', zorder=10, label='MEAS angular rate')
    ax[1].legend()
    ax[2].plot(np.array(epochAtt)[:-1], np.diff(headingAtt), color='r', zorder=20, label='dHeading')
    ax[2].plot(np.array(epochIns), zAngRate, color='c', zorder=15, label='INS angular rate')
    ax[2].plot(np.array(gyroDataMeas['epoch']), np.array(gyroDataMeas['zAngularRate']), color='b', zorder=10, label='MEAS angular rate')
    ax[2].legend()
    ax[-1].set_xlabel('GPS time (sec)')

    fig, ax = plt.subplots(3, sharex=True)
    ax[0].plot(np.array(epochAtt), roll, color='r', zorder=20, label='Roll')
    ax[0].plot(np.array(epochIns), np.cumsum(xAngRate), color='c', zorder=15, label='INS angular rate - cumsum')
    ax[0].plot(np.array(gyroDataMeas['epoch']), np.cumsum(-np.array(gyroDataMeas['yAngularRate']))/10, color='b', zorder=10, label='MEAS angular rate - cumsum')
    ax[0].legend()
    ax[1].plot(np.array(epochAtt), pitch, color='r', zorder=20, label='Pitch')
    ax[1].plot(np.array(epochIns), np.cumsum(yAngRate), color='c', zorder=15, label='INS angular rate - cumsum')
    ax[1].plot(np.array(gyroDataMeas['epoch']), np.cumsum(np.array(gyroDataMeas['xAngularRate']))/10, color='b', zorder=10, label='MEAS angular rate - cumsum')
    ax[1].legend()
    ax[2].plot(np.array(epochAtt), headingAtt, color='r', zorder=20, label='Heading')
    ax[2].plot(np.array(epochIns), np.cumsum(zAngRate), color='c', zorder=15, label='INS angular rate - cumsum')
    ax[2].plot(np.array(gyroDataMeas['epoch']), np.cumsum(np.array(gyroDataMeas['zAngularRate']))/10, color='b', zorder=10, label='MEAS angular rate - cumsum')
    ax[2].legend()
    ax[-1].set_xlabel('GPS time (sec)')

    rot = np.vstack([np.cumsum(-np.array(gyroDataMeas['yAngularRate']))/10, np.cumsum(np.array(gyroDataMeas['xAngularRate']))/10, np.cumsum(np.array(gyroDataMeas['zAngularRate']))/10])


    fig, ax = plt.subplots(1, sharex=True)
    ax.plot(np.array(epochAtt), headingAtt, color='r', zorder=20, label='Heading')
    ax.plot(np.array(epochIns), np.cumsum(zAngRate), color='g', zorder=15, label='INS angular rate')
    ax.plot(np.array(gyroDataMeas['epoch']), np.cumsum(np.array(gyroDataMeas['zAngularRate']))/10, color='c', zorder=10, label='MEAS angular rate - cumsum')
    ax.plot(headingTimes, headingMeas, color='b', zorder=10, label='MEAS angular rate2 - accumulated')
    ax.legend()
    ax.set_xlabel('GPS time (sec)')

    plt.show()
    import sys; sys.exit()

    fig, ax = plt.subplots(3, sharex=True)
    ax[0].plot(np.array(epochAtt)[:-1], np.diff(roll), color='g', zorder=20, label='Roll')
    ax[0].plot(np.array(epochIns), yAngRate, color='c', zorder=15, label='INS angular rate')
    ax[0].plot(np.array(gyroDataMeas['epoch']), -np.array(gyroDataMeas['yAngularRate']), color='b', zorder=10, label='MEAS angular rate')
    # ax[0].plot(np.array(rawData['epoch'])-rawData['epoch'][0], -np.array(rawData['yAngularRate']), color='r', label='RAW angular rate')
    ax[0].set_xlabel('GPS time (sec)')
    ax[0].legend()
    ax[1].plot(np.array(epochAtt), roll, color='g', zorder=20, label='Roll')
    ax[1].plot(np.array(rollTimes), rollMeas, color='b', zorder=10, label='Roll MEAS')
    # ax[1].plot(np.array(rawData['epoch'][:len(rollRaw)])-rawData['epoch'][0], rollRaw, color='r', zorder=5, label='Roll RAW')
    ax[1].legend()

    plt.show()

    fig, ax = plt.subplots(3, sharex=True)
    ax[0].plot((np.array(epochAtt)-epochAtt[0])[:-1], np.diff(roll), color='g', zorder=20, label='Roll')
    ax[0].plot((np.array(epochIns)-epochIns[0]), yAngRate, color='c', zorder=15, label='INS angular rate')
    ax[0].plot(np.array(gyroDataMeas['timeTag'])-rawData['epoch'][0], -np.array(gyroDataMeas['yAngularRate']), color='b', zorder=10, label='MEAS angular rate')
    ax[0].plot(np.array(rawData['epoch'])-rawData['epoch'][0], -np.array(rawData['yAngularRate']), color='r', label='RAW angular rate')
    ax[0].set_xlabel('Relative time (sec)')
    ax[0].legend()
    ax[1].plot((np.array(epochAtt)-epochAtt[0])[:-1], np.diff(pitch), color='g', zorder=20, label='Pitch')
    ax[1].plot((np.array(epochIns)-epochIns[0]), xAngRate, color='c', zorder=15, label='INS angular rate')
    ax[1].plot(np.array(gyroDataMeas['timeTag'])-rawData['epoch'][0], gyroDataMeas['xAngularRate'], color='b', zorder=10, label='MEAS angular rate')
    ax[1].plot(np.array(rawData['epoch'])-rawData['epoch'][0], rawData['xAngularRate'], color='r', label='RAW angular rate')
    ax[1].set_xlabel('Relative time (sec)')
    ax[1].legend()
    ax[2].plot((np.array(epochAtt)-epochAtt[0])[:-1], np.diff(headingAtt), color='g', zorder=20, label='Heading')
    ax[2].plot((np.array(epochIns)-epochIns[0]), zAngRate, color='c', zorder=15, label='INS angular rate')
    ax[2].plot(np.array(gyroDataMeas['timeTag'])-rawData['epoch'][0], gyroDataMeas['zAngularRate'], color='b', zorder=10, label='MEAS angular rate')
    ax[2].plot(np.array(rawData['epoch'])-rawData['epoch'][0], rawData['zAngularRate'], color='r', label='RAW angular rate')
    ax[2].set_xlabel('Relative time (sec)')
    ax[2].legend()

    fig, ax = plt.subplots(3, sharex=True)
    ax[0].plot((np.array(epochAtt)-epochAtt[0]), roll, color='g', zorder=20, label='Roll')
    ax[0].plot(np.array(rollTimes), rollMeas, color='b', zorder=10, label='Roll MEAS')
    ax[0].plot(np.array(rawData['epoch'][:len(rollRaw)])-rawData['epoch'][0], rollRaw, color='r', zorder=5, label='Roll RAW')
    # ax[0].plot(np.array(gyroDataMeas['timeTag'])-rawData['epoch'][0], np.cumsum(-np.array(gyroDataMeas['yAngularRate']))/10., color='b', zorder=10, label='MEAS angular rate')
    # ax[0].plot(np.array(rawData['epoch'])-rawData['epoch'][0], np.cumsum(-np.array(rawData['yAngularRate']))/100., color='r', label='RAW angular rate')
    ax[0].set_xlabel('Relative time (sec)')
    ax[0].legend()
    ax[1].plot((np.array(epochAtt)-epochAtt[0]), pitch, color='g', zorder=20, label='Pitch')
    ax[1].plot(np.array(pitchTimes), pitchMeas, color='b', zorder=10, label='Pitch MEAS')
    ax[1].plot(np.array(rawData['epoch'][:len(pitchRaw)])-rawData['epoch'][0], pitchRaw, color='r', zorder=5, label='Pitch RAW')
    # ax[1].plot(np.array(gyroDataMeas['timeTag'])-rawData['epoch'][0], np.cumsum(gyroDataMeas['xAngularRate'])/10., color='b', zorder=10, label='MEAS angular rate')
    # ax[1].plot(np.array(rawData['epoch'])-rawData['epoch'][0], np.cumsum(rawData['xAngularRate'])/100., color='r', label='RAW angular rate')
    ax[1].set_xlabel('Relative time (sec)')
    ax[1].legend()
    ax[2].plot((np.array(epochAtt)-epochAtt[0]), headingAtt, color='g', zorder=20, label='Heading')
    ax[2].plot(np.array(gyroDataMeas['timeTag'][:len(headingMeas)])-rawData['epoch'][0], headingMeas, color='b', zorder=10, label='Heading MEAS')
    ax[2].plot(np.array(rawData['epoch'][:len(headingRaw)])-rawData['epoch'][0], headingRaw, color='r', zorder=5, label='Heading RAW')
    # ax[2].plot(np.array(gyroDataMeas['timeTag'])-rawData['epoch'][0], np.cumsum(gyroDataMeas['zAngularRate'])/10., color='b', zorder=10, label='MEAS angular rate')
    # ax[2].plot(np.array(rawData['epoch'])-rawData['epoch'][0], np.cumsum(rawData['zAngularRate'])/100., color='r', label='RAW angular rate')
    ax[2].set_xlabel('Relative time (sec)')
    ax[2].legend()

    plt.show()
