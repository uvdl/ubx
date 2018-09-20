#!/usr/bin/env python3
import time
import datetime
import calendar

def posixToGps(posixTimestamp, leapSeconds=18):
    gpsOffset = (datetime.datetime(1980, 1, 6) - datetime.datetime(1970, 1, 1)).total_seconds()
    gpsTimestamp = posixTimestamp - gpsOffset + leapSeconds
    return gpsTimestamp

def gpsToPosix(gpsTimestamp, leapSeconds=18):
    gpsOffset = (datetime.datetime(1980, 1, 6) - datetime.datetime(1970, 1, 1)).total_seconds()
    posixTimestamp = gpsTimestamp + gpsOffset - leapSeconds
    return posixTimestamp

def gpsWeekAndTow(gpsTimestamp):
    gpsWeekNumber = int(gpsTimestamp) // (3600 * 24 * 7)
    gpsWeekNumberRollover = gpsWeekNumber % 1024
    gpsTow = gpsTimestamp % (3600 * 24 * 7)
    return gpsWeekNumber, gpsWeekNumberRollover, gpsTow        

curDateTime = datetime.datetime(2018, 9, 1, 0, 0)
posixTimestamp = calendar.timegm(curDateTime.timetuple())
gpsTimestamp = posixToGps(posixTimestamp)
gpsWeekNumber, gpsWeekNumberRollover, gpsTow = gpsWeekAndTow(gpsTimestamp)
posixTimestamp2 = gpsToPosix(gpsTimestamp)

print('UTC:      {}'.format(curDateTime.strftime('%Y-%m-%d %H:%M:%S')))
print('POSIX:    {:.3f}'.format(posixTimestamp))
print('GPS:      {:.3f}'.format(gpsTimestamp))
print('GPS Week: {} ({})'.format(gpsWeekNumber, gpsWeekNumberRollover))
print('GPS TOW:  {:.3f}'.format(gpsTow))
print('POSIX 2:  {:.3f}'.format(posixTimestamp2))
assert posixTimestamp == posixTimestamp2, 'POSIX->GPS->POSIX conversion failed! Results do not match!'
