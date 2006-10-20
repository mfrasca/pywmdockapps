#!/usr/bin/env python

"""pywmhdmon.py

WindowMaker dockapp to monitor the free space on your partitions and
the disk activity.

Copyright (C) 2003 Kristoffer Erlandsson

Licensed under the GNU General Public License.


Changes

2005-09-02 Mario Frasca
  added -s option for skipping an amount of configuration items.
  changed some single quotes to double quotes for use in emacs.
  updated the rc sample file 

2004-07-16 Mario Frasca
  recognizes unmounted partitions.
  configurable mouse actions.
  'used' information for read-only media.
  recognizes #-started numerical-coded colors.

2003-09-01 Kristoffer Erlandsson
Fixed a bug where the numbers wouldn't show if they were between 1000 and 1024.

2003-06-25 Kristoffer Erlandsson
Fixed a bug where a mouse click caused the app to enter an infinite loop

2003-06-24 Kristoffer Erlandsson
Additional fine tuning

2003-06-23 Kristoffer Erlandsson
First working version

"""

usage = """pywmhdmon.py [options]
Available options are:
-h, --help                      print this help
-t, --textcolor <color>         set the text color
-f, --barfgcolor <color>        set the foregroundcolor of the act. bar
-g, --barbgcolor <color>        set the background color of the act. bar
-b, --background <color>        set the background color
-F, --font <file>               set the font name
-r, --rgbfile <file>            set the rgb file to get color codes from
-c, --configfile <file>         set the config file to use
-p, --procstat <file>           set the location of /proc/stat
-s, --skipconf <num>            determines how many configuration items to skip
"""

import sys
import time
import getopt
import os

import wmdocklib

width = 64
height = 64

xOffset = 4
yOffset = 4

graphStartX = 7
graphStartY = 53
graphHeight = 4

graphBgStartX = 72-64
graphBgStartY = 53+64

graphLineStartX = 2
graphLineStartY = 58+64

defaultConfigFile = os.environ['HOME']+'/.pywmhdmonrc'
defaultProcStat = '/proc/stat'
displayModes = ('bar', 'percent', 'free', 'used')
defaultMode = 'bar'

hdmon = None

class NotMounted(OSError):
    pass

class PywmHDMon:
    def __init__(self, pathsToMonitor, procStat='/proc/stat', actMonEnabled=1, skipping=0):
        self._pathsToMonitor = pathsToMonitor
        self._actMonEnabled = actMonEnabled
        self._skipping = skipping

        self._statFile = procStat
        self._maxIODiff = 0
        self._lastIO = -1
        for i in range(len(self._pathsToMonitor)):
            wmdocklib.addMouseRegion(i+1, 8, self.getY(i+1)+yOffset,
                                     58, self.getY(i+1)+char_height+yOffset)


    def addString(self, s, x, y):
        try:
            wmdocklib.addString(s, x, y, xOffset, yOffset, width, height)
        except ValueError, e:
            sys.stderr.write('Error when painting string:\n' + str(e) + '\n')
            sys.exit(3)

    def getHdInfo(self, path):
        """Get the free and total space of the filesystem which path is on.

        Return a tuple with (<total space>, <free space>) in bytes. Raise
        OSError if we can't stat the path.  Raise NotMounted if not mounted.
        These operations are quite costly, not adviced to perform these checks
        more than once every 10 seconds.
        """
        
        # check if is mounted <- st_dev(/mount/point) == st_dev(/mount)
        if path is not '/':
            statOwn = os.stat(path)

            # the following is a bit ugly: it removes the trailing
            # dirname from the mount point.  split by '/', leave the
            # last string, join back, check for empty string.
            statCnt = os.stat('/'.join(path.split('/')[:-1]) or '/')
            if statOwn[2] == statCnt[2]:
                raise NotMounted
        stat = os.statvfs(path)
        blockSize = stat.f_bsize
        availableBlocks = stat.f_bavail
        totalBlocks = stat.f_blocks
        free = blockSize * availableBlocks
        total = blockSize * totalBlocks
        return (total, free)

    def paintGraph(self, percentFilled, x, y, w, thin=None):
        """Paint a graph with percentFilled percent filled.

        Paint at position x, y and with width w.  
        if thin == 1, make it a thin line instead of a block.
        """
        paintWidth = int(round(percentFilled/100.0 * w))
        if paintWidth > 0:
            wmdocklib.copyXPMArea(
                graphLineStartX, graphLineStartY, paintWidth, thin or graphHeight,
                x + xOffset, y + yOffset)
        if w - paintWidth > 0:
            wmdocklib.copyXPMArea(
                graphBgStartX, graphBgStartY, w - paintWidth, thin or graphHeight,
                x + paintWidth + xOffset, y + yOffset)

    def getY(self, line):
        "returns the y coordinate of the top line for the box"
        lineCount = (height - yOffset*2) / (char_height+2)
        interlinea = (height - yOffset*2) / lineCount
        lastBaseline = yOffset + lineCount * interlinea
        extraYOffset = (height - yOffset - lastBaseline) / 2
        return extraYOffset + (line - 1) * interlinea

    def paintLabel(self, line, label):
        self.addString(label, 1, self.getY(line))

    def paintHdData(self, line, data, mode):
        total, free = data
        xStart = (width*2)/5
        if total==0:
            self.addString('     ', xStart, self.getY(line))
            self.paintGraph(0, xStart, self.getY(line) + 4, 
                            width - xOffset*2 - xStart - 2,
                            thin=1)
            pass
        elif mode == 'percent':
            percent = (float(free) / float(total)) * 100.0
            percentStr = (str(int(round(percent))) + '%').rjust(5)
            self.addString(percentStr, xStart, self.getY(line))
        elif mode == 'used':
            totalStr = bytesToStr(total).rjust(5)
            self.addString(totalStr, width-yOffset*2-5*char_width-1, self.getY(line))
        elif mode == 'free':
            freeStr = bytesToStr(free).rjust(5)
            self.addString(freeStr, width-yOffset*2-5*char_width, self.getY(line))
        elif mode == 'bar':
            percentUsed = (float(total - free) / float(total)) * 100.0
            self.paintGraph(percentUsed, xStart, self.getY(line) + 2, 
                            width - xOffset*2 - xStart - 2)
        else:
            sys.stderr.write('Unknown display mode: %s, ignoring data.\n'
                              % mode)
    def getHdActivity(self):
        """Return the current hd activity in percent.
        
        Return how many percent of the max achieved activity during the
        program's lifetime the current activity is. However, every time
        this method is called we decrease the max achieved activity a
        little bit to get a bit less affected by spikes. I think the
        interesting thing is to see if the hard drive is active, not
        really exactly how active.
        """
        
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
        event = wmdocklib.getEvent()
        while event is not None:
            if event['type'] == 'destroynotify':
                sys.exit(0)
            elif event['type'] == 'buttonrelease':
                area = wmdocklib.checkMouseRegion(event['x'],event['y'])
                if area is not -1:
                    self.toggleMount(area-1+self._skipping)
            event = wmdocklib.getEvent()

    def toggleMount(self, line):
        label, path, mode, action = self._pathsToMonitor[line]
        if action is None:
            return
        try:
            self.getHdInfo(path)
            mounted = True
        except NotMounted:
            mounted = False
        except OSError, e:
            return
        if mounted:
            if action == 'mount':
                os.spawnvp(os.P_NOWAIT, 'umount', ['umount', path])
            elif action == 'eject':
                os.spawnvp(os.P_WAIT, 'umount', ['umount', path])
                os.spawnvp(os.P_NOWAIT, 'eject', ['eject', path])
        else:
            os.spawnvp(os.P_NOWAIT, 'mount', ['mount', path])

    def updateMonitoredPaths(self):
        index = 0
        pageoffset = self._skipping
        for i in self._pathsToMonitor:
            index += 1
            if index < pageoffset+1:
                continue
            if i is not None:
                label, path, mode, action = i
                self.paintLabel(index-pageoffset, label)
                try:
                    hdData = self.getHdInfo(path)
                except NotMounted:
                    hdData = (0, 0)
                except OSError, e:
                    sys.stderr.write(
                    "Can't get hd data from %s: %s\n" % (path, str(e)))
                    hdData = (0, 0)
                self.paintHdData(index-pageoffset, hdData, mode)
            if index - pageoffset == 5:
                break

    def mainLoop(self):
        self.updateMonitoredPaths()
        while 1:
            self._checkEvents()
            if self._actMonEnabled:
                self.updateHdActivity()
            wmdocklib.redraw()
            time.sleep(0.1)


import signal
def handler(num, frame):
    hdmon.updateMonitoredPaths()
    signal.alarm(10)

def parseCommandLine(argv):
    """Parse the commandline. Return a dictionary with options and values."""
    shorts = 'ht:f:g:b:r:c:p:s:F:'
    longs = ['help', 'textcolor=', 'background=', 'barfgcolor=',
             'rgbfile=', 'configfile=', 'barbgcolor=', 'procstat=',
             'skipconf=','font=']
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
        if o in ('-F', '--font'):
            d['font'] = a
        if o in ('-f', '--barfgcolor'):
            d['barfgcolor'] = a
        if o in ('-p', '--procstat'):
            d['procstat'] = a
        if o in ('-s', '--skipconf'):
            d['skipconf'] = a
    return d

def makeNumDigits(num, numDigits):
    """Make a floating point number a certain number of digits, including
    decimal. Return a string containing it.
    """
    lenOfIntPart = len(str(int(num)))
    if lenOfIntPart > numDigits:
        # Can't convert a number to less digits then it's integer part...
        return ''
    decimalsNeeded = numDigits - lenOfIntPart
    s = '%' + str(lenOfIntPart) + '.' + str(decimalsNeeded) + 'f'
    s = s % round(num, decimalsNeeded)
    return s

def bytesToStr(bytes):
    """Convert a number of bytes to a nice printable string.
    
    May raise ValueError if bytes can't be seen as an float.
    """
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
    fileConfig = wmdocklib.readConfigFile(configFile, sys.stderr)
    config = fileConfig
    for i in clConfig.iteritems():
        config[i[0]] = i[1]

    palette = {}
    palette[0] = clConfig.get('background', 'black')
    palette[2] = clConfig.get('textcolor', 'cyan3')
    palette[9] = clConfig.get('barfgcolor', 'cyan')
    palette[8] = clConfig.get('barbgcolor', 'cyan4')
    palette[5] = clConfig.get('activitycolor', 'cyan2')

    font = clConfig.get('font', '6x8')

    global char_width, char_height
    char_width, char_height = wmdocklib.initPixmap(patterns=patterns,
                                                   font_name=font,
                                                   palette=palette,
                                                   bg=0, fg=2)

    pathsToMonitor = []
    for i in range(1,1000):
        labelStr = str(i) + '.label'
        pathStr = str(i) + '.path'
        modeStr = str(i) + '.displaymode'
        actionStr = str(i) + '.action'
        label = config.get(labelStr)
        if not label: break
        path = config.get(pathStr)
        action = config.get(actionStr, 'fixed').lower().strip()
        if action not in ['mount', 'eject']:
            action = None
        displayMode = config.get(modeStr, defaultMode)
        if not displayMode in displayModes:
            sys.stderr.write(
                'Unknown display mode: %s, using default.\n' % displayMode)
            displayMode = defaultMode
        takeChars = 3
        if char_width <= 5:
            takeChars = 4
        pathsToMonitor.append((label[:takeChars], path, displayMode, action))
    procStat = config.get('procstat', defaultProcStat)
    skipping = int(config.get('skipconf', 0))
    actMonEnabled = int(config.get('monitoring',0))
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
    wmdocklib.openXwindow(sys.argv, width, height)

    signal.signal(signal.SIGCHLD, handler)
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(10)

    global hdmon
    hdmon = PywmHDMon(pathsToMonitor, procStat, actMonEnabled, skipping)
    hdmon.mainLoop()

patterns = \
['0000000000000000000000000000000000000000000000000000000000000000',
 '0000000000000000000000000000000000000000000000000000000000000000',
 '0099900555002220055500555000000000000000000000000000000000000000',
 '0099900555002220055500555000000000000000000000000000000000000000',
 '0099900555002220055500555000000000000000000000000000000000000000',
 '0099900555005550055500555000000000000000000000000000000000000000',
 '0099900555005550055500555000000000000000000000000000000000000000',
 '0099900555005550055500555000000000000000000000000000000000000000',
 '0099900555005550022200555000000000000000000000000000000000000000',
 '0099900555005550022200555000000000000000000000000000000000000000',
 '0099900555005550022200555000000000000000000000000000000000000000',
 '0099900555005550055500555000000000000000000000000000000000000000',
 '0099900555005550055500555000000000000000000000000000000000000000',
 '0099900555005550055500555000000000000000000000000000000000000000',
 '0099900555005550055500222000000000000000000000000000000000000000',
 '0099900555005550055500222000000000000000000000000000000000000000',
 '0099900555005550055500222000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099900088888888888888888888888888888888888888888888888888888888',
 '0099900088888888888888888888888888888888888888888888888888888888',
 '0099900088888888888888888888888888888888888888888888888888888888',
 '0099900088888888888888888888888888888888888888888888888888888888',
 '0099900000000000000000000000000000000000000000000000000000000000',
 '0099999999999999999999999999999999999999999999999999999999999999',
 '0099999999999999999999999999999999999999999999999999999999999999',
 '0099999999999999999999999999999999999999999999999999999999999999',
 '0099999999999999999999999999999999999999999999999999999999999999',
 '0000000000000000000000000000000000000000000000000000000000000000',
 '0000000000000000000000000000000000000000000000000000000000000000',
 ]

if __name__ == '__main__':
    main()
