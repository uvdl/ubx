sensorDataTypeToString =  {0: 'NO DATA',
                           1: 'RESERVED',
                           2: 'RESERVED',
                           3: 'RESERVED',
                           4: 'RESERVED',
                           5: 'Gyro Z',
                           6: 'Front-left wheel ticks',
                           7: 'Front-right wheel ticks',
                           8: 'Rear-left wheel ticks',
                           9: 'Rear-right wheel ticks',
                           10: 'Speed tick',
                           11: 'Speed',
                           12: 'Gyro temp',
                           13: 'Gyro Y',
                           14: 'Gyro X',
                           15: 'RESERVED',
                           16: 'Accel X',
                           17: 'Accel Y',
                           18: 'Accel Z'
                           }

def parseEsfStatus(statusInfo):
    epoch = []
    fusionMode = [packet[0]['FusionMode'] for packet in statusInfo]
    sensorInfo = {}
    for packet in statusInfo:
        curEpoch = packet[0]['ITOW']/1e3
        epoch.append(curEpoch)
        for sensorStatus in packet[1:]:
            sensorDataType = sensorStatus['SensStatus1'] & 0x3f
            sensorDataTypeString = sensorDataTypeToString[sensorDataType]
            calibStatus = sensorStatus['SensStatus2'] & 0x3
            timeStatus = sensorStatus['SensStatus2'] & 0xc
            faults = sensorStatus['Faults']
            if sensorDataTypeString not in sensorInfo:
                sensorInfo[sensorDataTypeString] = {'epoch': [], 'calibStatus': [], 'timeStatus': [], 'faults': []}
            sensorInfo[sensorDataTypeString]['epoch'].append(curEpoch)
            sensorInfo[sensorDataTypeString]['calibStatus'].append(calibStatus)
            sensorInfo[sensorDataTypeString]['timeStatus'].append(timeStatus)
            sensorInfo[sensorDataTypeString]['faults'].append(faults)
    return epoch, fusionMode, sensorInfo

if __name__=='__main__':
    import numpy as np
    import matplotlib.pyplot as plt
    import cPickle as pickle
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    args = parser.parse_args()

    f = open(args.input, 'r')
    data = pickle.load(f)

    esfStatusInfo = data['ESF-STATUS']
    epoch, fusionMode, sensorInfo = parseEsfStatus(esfStatusInfo)

    sensorFaults = {}
    for key, value in sensorInfo.iteritems():
        faults = np.array(value['faults'])
        sensorFaults[key] = {}
        sensorFaults[key]['None'] = np.sum(faults == 0)
        sensorFaults[key]['badMeas'] = np.sum((faults & 0x1) == 0x1)
        sensorFaults[key]['badTTag'] = np.sum((faults & 0x2) == 0x2)
        sensorFaults[key]['missingMeas'] = np.sum((faults & 0x4) == 0x4)
        sensorFaults[key]['noisyMeas'] = np.sum((faults & 0x8) == 0x8)

    print('\n*** FAULTS ***')
    for key in sorted(sensorFaults.keys()):
        print(key)
        numMessages = len(sensorInfo[key]['faults'])
        for faultName in sorted(sensorFaults[key].keys()):
            numFaults = sensorFaults[key][faultName]
            percentage = float(numFaults)/numMessages*100.
            if faultName is not 'None' and numFaults == 0:
                continue
            print('    {} - {}/{} ({:.3f}%)'.format(faultName, numFaults, numMessages, percentage))

    fig, ax = plt.subplots(len(sensorInfo)+1, sharex=True)
    ax[0].plot(epoch, fusionMode, color='r')
    ax[0].set_ylim([0, 3.5])
    ax[0].set_ylabel('Fusion Mode')
    ax[0].grid(True)
    ax[0].set_title('Calibration Status')

    for i, key in enumerate(sorted(sensorInfo.keys()), 1):
        info = sensorInfo[key]
        ax[i].plot(info['epoch'], info['calibStatus'], color='g')
        ax[i].set_ylim([-0.5, 3.5])
        ax[i].set_ylabel(key)
        ax[i].grid(True)

    fig, ax = plt.subplots(len(sensorInfo), sharex=True)
    ax[0].set_title('Faults')
    
    for i, key in enumerate(sorted(sensorInfo.keys())):
        info = sensorInfo[key]
        ax[i].plot(info['epoch'], info['faults'], color='b')
        ax[i].set_ylim([-0.5, 10])
        ax[i].set_ylabel(key)
        ax[i].grid(True)  

    plt.show()
