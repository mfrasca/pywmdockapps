#!/usr/bin/env python

'''pywmhdmon.py

WindowMaker dockapp to monitor the free space on your partitions and
the disk activity.

Copyright (C) 2003 Kristoffer Erlandsson

Licensed under the GNU General Public License.


Changes
2003-09-01 Kristoffer Erlandsson
Fixed a bug where the numbers wouldn't show if they were between 1000 and 1024.

2003-06-25 Kristoffer Erlandsson
Fixed a bug where a mouse click caused the app to enter an infinite loop

2003-06-24 Kristoffer Erlandsson
Additional fine tuning

2003-06-23 Kristoffer Erlandsson
First working version

'''
usage = '''pywmhdmon.py [options]
Available options are:
-h, --help                      print this help
-t, --textcolor <color>         set the text color
-f, --barfgcolor <color>        set the foregroundcolor of the act. bar
-g, --barbgcolor <color>        set the background color of the act. bar
-b, --background <color>        set the background color
-r, --rgbfile <file>            set the rgb file to get color codes from
-c, --configfile <file>         set the config file to use
-p, --procstat <file>           set the location of /proc/stat
'''


import sys
import time
import getopt
import os

import pywmhelpers

width = 64
height = 64

xOffset = 4
yOffset = 4

lettersStartX = 0
lettersStartY = 74
letterWidth = 6
letterHeight = 8

digitsStartX = 0
digitsStartY = 64
digitWidth = 6
digitHeight = 8

graphStartX = 7
graphStartY = 53
graphHeight = 4

graphBgStartX = 72
graphBgStartY = 53

graphLineStartX = 66
graphLineStartY = 58

letters = 'abcdefghijklmnopqrstuvwxyz'
digits = '0123456789:/-%. '

defaultConfigFile = '~/.pywmhdmonrc'
defaultRGBFiles = ('/usr/lib/X11/rgb.txt', '/usr/X11R6/lib/X11/rgb.txt')
defaultProcStat = '/proc/stat'
displayModes = ('bar', 'percent', 'free')
defaultMode = 'bar'

class PywmHDMon:
    def __init__(self, pathsToMonitor, procStat='/proc/stat', actMonEnabled=1):
        self._pathsToMonitor = pathsToMonitor
        self._actMonEnabled = actMonEnabled

        self._statFile = procStat
        self._maxIODiff = 0
        self._lastIO = -1

    def addString(self, s, x, y):
        try:
            pywmhelpers.addString(s, x, y, letterWidth, letterHeight,
                        lettersStartX, lettersStartY, letters, digitWidth,
                        digitHeight, digitsStartX, digitsStartY, digits,
                        xOffset, yOffset, width, height)
        except ValueError, e:
            sys.stderr.write('Error when painting string:\n' + str(e) + '\n')
            sys.exit(3)

    def getHdInfo(self, path):
        '''Get the free and total space of the filesystem which path is on.

        Return a tuple with (<total space>, <free space>) in bytes. Raise
        OSError if we can't stat the path.
        These operations are quite costly, not adviced to perform these checks
        more than once every 10 seconds.
        '''
        stat = os.statvfs(path)
        blockSize = stat.f_bsize
        availableBlocks = stat.f_bavail
        totalBlocks = stat.f_blocks
        free = blockSize * availableBlocks
        total = blockSize * totalBlocks
        return (total, free)

    def paintGraph(self, percentFilled, x, y, w):
        '''Paint a graph with percentFilled percent filled.

        Paint at position x, y and with width w.
        '''
        paintWidth = int(round(percentFilled/100.0 * w))
        if paintWidth > 0:
            pywmhelpers.copyXPMArea(
                graphLineStartX, graphLineStartY, paintWidth, graphHeight,
                x + xOffset, y + yOffset)
        if w - paintWidth > 0:
            pywmhelpers.copyXPMArea(
                graphBgStartX, graphBgStartY, w - paintWidth, graphHeight,
                x + paintWidth + xOffset, y + yOffset)

    def getY(self, line):
        return 2 + (line - 1) * (letterHeight + 3)

    def paintLabel(self, line, label):
        self.addString(label, 1, self.getY(line))

    def paintHdData(self, line, data, mode):
        total, free = data
        xStart = width - xOffset - 6 * letterWidth - 1
        if mode == 'percent':
            percent = (float(free) / float(total)) * 100.0
            percentStr = (str(int(round(percent))) + '%').rjust(5)
            self.addString(percentStr, xStart, self.getY(line))
        elif mode == 'free':
            freeStr = bytesToStr(free).rjust(5)
            self.addString(freeStr, xStart, self.getY(line))
        elif mode == 'bar':
            percentUsed = (float(total - free) / float(total)) * 100.0
            self.paintGraph(percentUsed, xStart, self.getY(line) + 2, 
                            width - xOffset*2 - xStart - 2)
        else:
            sys.stderr.write('Unknown display mode: %s, ignoring data.\n'
                              % mode)
    def getHdActivity(self):
        '''Return the current hd activity in percent.
        
        Return how many percent of the max achieved activity during the
        program's lifetime the current activity is. However, every time
        this method is called we decrease the max achieved activity a
        little bit to get a bit less affected by spikes. I think the
        interesting thing is to see if the hard drive is active, not
        really exactly how active.
        '''
        statFile = file(self._statFile, 'r')
        diskIoStartTag = 'disk_io: '
        ioLine = None
        for line in statFile:
            if line.startswith(diskIoStartTag):
                ioLine = line
        statFile.close()
        if ioLine is None:
            # Can't get HD activity
            sys.stderr.write("Can't get hd activity from %s\n" %
                self._statFile)
            return 0.0
        ioLine = ioLine[len(diskIoStartTag):]
        disks = ioLine.split()
        currIO = 0
        for disk in disks:
            dataPart = disk.split(':')[1].strip(')(')
            infos = dataPart.split(',')
            blocksRead = long(infos[2])
            blocksWritten = long(infos[4])
            currIO += blocksRead + blocksWritten
        if self._lastIO == -1:
            self._lastIO = currIO
        currDiff = currIO - self._lastIO
        self._lastIO = currIO
        if currDiff > self._maxIODiff:
            self._maxIODiff = currDiff
        if self._maxIODiff <= 0:
            self._maxIODiff = 0
            return 0.0
        currAct = (float(currDiff) / float(self._maxIODiff)) * 100.0
        self._maxIODiff -= 1  # So spikes won't affect us too much.
        return currAct

    def updateHdActivity(self):
        currentAct = self.getHdActivity()
        self.paintGraph(currentAct, 3, height - yOffset*2 - 3 - graphHeight, 
                        width - 2 * xOffset - 6)

    def _checkEvents(self):
        event = pywmhelpers.getEvent()
        while not event is None:
            if event['type'] == 'destroynotify':
                sys.exit(0)
            event = pywmhelpers.getEvent()

    def mainLoop(self):
        counter = -1
        while 1:
            counter += 1
            self._checkEvents()
            if self._actMonEnabled:
                self.updateHdActivity()
            if counter % 100 == 0:
                index = 0
                for i in self._pathsToMonitor:
                    if not i is None:
                        label, path, mode = i
                        self.paintLabel(index + 1, label)
                        try:
                            hdData = self.getHdInfo(path)
                        except OSError, e:
                            sys.stderr.write(
                            "Can't get hd data from %s: %s\n" % (path, str(e)))
                            hdData = (0, 0)
                        self.paintHdData(index + 1, hdData, mode)
                    index += 1
            if counter == 9999999:
                counter = -1
            pywmhelpers.redraw()
            time.sleep(0.1)




def parseCommandLine(argv):
    '''Parse the commandline. Return a dictionary with options and values.'''
    shorts = 'ht:f:g:b:r:c:p:'
    longs = ['help', 'textcolor=', 'background=', 'barfgcolor=',
             'rgbfile=', 'configfile=', 'barbgcolor=', 'procstat=']
    try:
        opts, nonOptArgs = getopt.getopt(argv[1:], shorts, longs)
    except getopt.GetoptError, e:
        sys.stderr.write('Error when parsing commandline: ' + str(e) + '\n')
        sys.stderr.write(usage)
        sys.exit(2)
    d = {}
    for o, a in opts:
        if o in ('-h', '--help'):
            sys.stdout.write(usage)
            sys.exit(0)
        if o in ('-t', '--textcolor'):
            d['textcolor'] = a
        if o in ('-b', '--background'):
            d['background'] = a
        if o in ('-r', '--rgbfile'):
            d['rgbfile'] = a
        if o in ('-c', '--configfile'):
            d['configfile'] = a
        if o in ('-g', '--barbgcolor'):
            d['barbgcolor'] = a
        if o in ('-f', '--barfgcolor'):
            d['barfgcolor'] = a
        if o in ('-p', '--procstat'):
            d['procstat'] = a
    return d

def parseColors(defaultRGBFileList, config, xpm):
    rgbFileName = ''
    for fn in defaultRGBFileList:
        if os.access(fn, os.R_OK):
            rgbFileName = fn
            break
    rgbFileName = config.get('rgbfile', rgbFileName)
    useColors = 1
    if not os.access(rgbFileName, os.R_OK):
        sys.stderr.write(
            "Can't read the RGB file, try setting it differently using -r,\n")
        sys.stderr.write(
            "Ignoring your color settings, using the defaults.\n")
        useColors = 0
    if useColors:
        # Colors is a list with (<config_key>, <xpm-key>) pairs.
        colors =  (('barfgcolor', 'graph'),
                  ('barbgcolor', 'graphbg'),
                  ('textcolor', 'text'),
                  ('background', 'background'))
        for key, value in colors:
            col = config.get(key)
            if not col is None:
                code = pywmhelpers.getColorCode(col, rgbFileName)
                if code is None:
                    sys.stderr.write('Bad colorcode for %s, ignoring.\n' % key)
                else:
                    pywmhelpers.setColor(xpm, value, code)

def makeNumDigits(num, numDigits):
    '''Make a floating point number a certain number of digits, including
    decimal. Return a string containing it.
    '''
    lenOfIntPart = len(str(int(num)))
    if lenOfIntPart > numDigits:
        # Can't convert a number to less digits then it's integer part...
        return ''
    decimalsNeeded = numDigits - lenOfIntPart
    s = '%' + str(lenOfIntPart) + '.' + str(decimalsNeeded) + 'f'
    s = s % round(num, decimalsNeeded)
    return s

def bytesToStr(bytes):
    '''Convert a number of bytes to a nice printable string.
    
    May raise ValueError if bytes can't be seen as an float.
    '''
    bytes = float(bytes)
    kb = 1024 
    mb = 1024 * 1024
    gb = 1024 * mb
    tb = 1024 * gb
    pb = 1024 * tb
    if bytes < kb:
        size = bytes
        letter = 'B'
        #return makeNumDigits(bytes, numDigits) + 'B'
    elif bytes < mb:
        size = bytes / kb
        letter = 'k'
        #return makeNumDigits(bytes/kb, numDigits) + 'k'
    elif bytes < gb:
        size = bytes / mb
        letter = 'M'
        #return makeNumDigits(bytes/mb, numDigits) + 'M'
    elif bytes < tb:
        size = bytes / gb
        letter = 'G'
        #return makeNumDigits(bytes/gb, numDigits) + 'G'
    elif bytes < pb:
        size = bytes / tb
        letter = 'T'
        #return makeNumDigits(bytes/tb, numDigits) + 'T'
    else:
        size = bytes / pb
        letter = 'p'
        #return makeNumDigits(bytes/pb, numDigits) + 'P'
    if size >= 1000:
        res = makeNumDigits(size, 4)
    else:
        res = makeNumDigits(size, 3)
    res += letter
    return res


def main():
    clConfig = parseCommandLine(sys.argv)
    configFile = clConfig.get('configfile', defaultConfigFile)
    configFile = os.path.expanduser(configFile)
    fileConfig = pywmhelpers.readConfigFile(configFile, sys.stderr)
    config = fileConfig
    for i in clConfig.iteritems():
        config[i[0]] = i[1]
    parseColors(defaultRGBFiles, config, xpm)

    pathsToMonitor = []
    for i in range(1,5):
        labelStr = str(i) + '.label'
        pathStr = str(i) + '.path'
        modeStr = str(i) + '.displaymode'
        label = config.get(labelStr)
        path = config.get(pathStr)
        displayMode = config.get(modeStr, defaultMode)
        if not displayMode in displayModes:
            sys.stderr.write(
                'Unknown display mode: %s, using default.\n' % displayMode)
            displayMode = defaultMode
        if label is None or path is None:
            pathsToMonitor.append(None)
        else:
            pathsToMonitor.append((label[:3], path, displayMode))
    procStat = config.get('procstat', defaultProcStat)
    actMonEnabled = 1
    if not os.access(procStat, os.R_OK):
        sys.stderr.write(
            "Can't read your procstat file, try setting it with -p. ")
        sys.stderr.write("Disabling the HD activity bar.\n")
        actMonEnabled = 0
    try:
        programName = sys.argv[0].split(os.sep)[-1]
    except IndexError:
        programName = ''
    sys.argv[0] = programName
    pywmhelpers.setDefaultPixmap(xpm)
    pywmhelpers.openXwindow(sys.argv, width, height)
    # XXX Add commands for clicking different areas?
    hdmon = PywmHDMon(pathsToMonitor, procStat, actMonEnabled)
    hdmon.mainLoop()


xpm = \
['160 100 13 1',
 ' \tc #208120812081',
 '.\tc #00000000FFFF',
 'o\tc #C71BC30BC71B',
 'O\tc #861782078E38',
 '+\tc #EFBEF3CEEFBE',
 '@\tc #618561856185',
 '#\tc #9E79A2899E79',
 '$\tc #410341034103',
 'o\tc #2020b2b2aaaa s indicator',
 '/\tc #2020b2b2aaaa s graph',
 '-\tc #707070707070 s graphbg',
 'X\tc #000000000000 s background',
 '%\tc #2081B2CAAEBA s text',
 '                                                                 ...............................................................................................',
 '                                                                 .///..XXX..ooo..XXX..XXX.......................................................................',
 '                                                                 .///..XXX..ooo..XXX..XXX.......................................................................',
 '                                                                 .///..XXX..ooo..XXX..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..ooo..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..ooo..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..ooo..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..XXX.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..ooo.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..ooo.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///..XXX..XXX..XXX..ooo.......................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...-------------------------------------------------------------------------------------...',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...-------------------------------------------------------------------------------------...',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...-------------------------------------------------------------------------------------...',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...-------------------------------------------------------------------------------------...',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///////////////////////////////////////////////////////////////////////////////////////////...',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX     .///////////////////////////////////////////////////////////////////////////////////////////...',
 '                                                                 .///////////////////////////////////////////////////////////////////////////////////////////...',
 '                                                                 .///////////////////////////////////////////////////////////////////////////////////////////...',
 '                                                                 ...............................................................................................',
 '                                                                 ...............................................................................................',
 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%%%%%XXX%XXX%%%%%X%%%%%X%XXX%X%%%%%X%%%%%X%%%%%X%%%%%X%%%%%XXXXXXXXXX%XXXXXXXXXX%X%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XX%%XXXXXXX%XXXXX%X%XXX%X%XXXXX%XXXXXXXXX%X%XXX%X%XXX%XX%%XXXXXX%XXXXXXXXXXXX%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXXXXXX%XXXXX%X%XXX%X%XXXXX%XXXXXXXXX%X%XXX%X%XXX%XX%%XXXXX%%XXXXXXXXXXX%%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXX%%%%%XX%%%%X%%%%%X%%%%%X%%%%%XXXXX%X%%%%%X%%%%%XXXXXXXXX%XXX%%%%%XXXX%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXX%XXXXXXXXX%XXXXX%XXXXX%X%XXX%XXXXX%X%XXX%XXXXX%XXXXXXXX%%XXXXXXXXXXX%%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXX%XXXXXXXXX%XXXXX%XXXXX%X%XXX%XXXXX%X%XXX%XXXXX%XX%%XXXX%XXXXXXXXXXXX%XXXXX%%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%%%%%XX%%%XX%%%%%X%%%%%XXXXX%X%%%%%X%%%%%XXXXX%X%%%%%X%%%%%XX%%XXXX%XXXXXXXXXXXX%X%XXX%%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 '................................................................................................................................................................',
 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
 'XX%%%XX%%%%XXX%%%%X%%%%XX%%%%XX%%%%%X%%%%%X%XXX%XXX%XXXXXXX%X%XXX%X%XXXXX%XXX%X%%%%XX%%%%%X%%%%%X%%%%%X%%%%%X%%%%%X%%%%%X%XXX%X%XXX%X%XXX%X%XXX%X%XXX%X%%%%%XXXX',
 'X%XXX%X%XXX%X%XXXXX%XXX%X%XXXXX%XXXXX%XXXXX%XXX%XXX%XXXXXXX%X%XXX%X%XXXXX%%X%%X%XXX%X%XXX%X%XXX%X%XXX%X%XXX%X%XXXXXXX%XXX%XXX%X%XXX%X%XXX%X%XXX%X%XXX%XXXXX%XXXX',
 'X%XXX%X%XXX%X%XXXXX%XXX%X%XXXXX%XXXXX%XXXXX%XXX%XXX%XXXXXXX%X%XX%XX%XXXXX%X%X%X%XXX%X%XXX%X%XXX%X%XXX%X%XXX%X%XXXXXXX%XXX%XXX%X%XXX%X%XXX%XX%X%XX%XXX%XXXX%XXXXX',
 'X%%%%%X%%%%XX%XXXXX%XXX%X%%%%XX%%%%XX%X%%%X%%%%%XXX%XXXXXXX%X%%%XXX%XXXXX%XXX%X%XXX%X%XXX%X%%%%%X%%XX%X%%%%XX%%%%%XXX%XXX%XXX%X%XXX%X%XXX%XXX%XXX%%%%%XXX%XXXXXX',
 'X%XXX%X%XXX%X%XXXXX%XXX%X%XXXXX%XXXXX%XXX%X%XXX%XXX%XXXXXXX%X%XX%XX%XXXXX%XXX%X%XXX%X%XXX%X%XXXXX%X%X%X%XXX%XXXXX%XXX%XXX%XXX%X%XXX%X%X%X%XX%X%XXXXXX%XX%XXXXXXX',
 'X%XXX%X%XXX%X%XXXXX%XXX%X%XXXXX%XXXXX%XXX%X%XXX%XXX%XXX%XXX%X%XXX%X%XXXXX%XXX%X%XXX%X%XXX%X%XXXXX%XX%%X%XXX%XXXXX%XXX%XXX%XXX%X%XXX%X%%X%%X%XXX%XXXXX%X%XXXXXXXX',
 'X%XXX%X%%%%XXX%%%%X%%%%XX%%%%XX%XXXXX%%%%%X%XXX%XXX%XXXX%%%XX%XXX%X%%%%XX%XXX%X%XXX%X%%%%%X%XXXXX%%%%%X%XXX%X%%%%%XXX%XXXX%%%%XX%%%XX%XXX%X%XXX%X%%%%%X%%%%%XXXX',
 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................',
 '................................................................................................................................................................']


if __name__ == '__main__':
    main()

