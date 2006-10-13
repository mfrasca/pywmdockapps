#! /usr/bin/env python

"""pywmsysmon.py

WindowMaker system monitor dockapp written in Python. It displays your CPU
usage and your available/used memory.

Copyright (C) 2003 Kristoffer Erlandsson

Licensed under the GNU General Public License.

Changes
2003-06-28 Kristoffer Erlandsson
Fixed a bug which caused infinite loop if the mouse was clicked

2003-06-24 Kristoffer Erlandsson
First working version
"""
usage="""pywmsysmon.py [options]
Available options are:
-h, --help                      print this help
-f, --barfgcolor <color>        set the foreground color of the memory bar
-g, --barbgcolor <color>        set the background color of the memory bar
-b, --background <color>        set the background color
-p, --graphforeground <color>   set the cpu graph foreground color
-a, --graphbackground <color>   set the cpu graph background color
-r, --rgbfile <file>            set the rgb file to get color codes from
-s, --procstat <file>           set the location of /proc/stat
-m, --procmeminfo <file>        set the location of /proc/meminfo
-i, --ignorenice                ignore nice valued cpu usage
-u, --updatedelay <value>       delay (in seconds) between cpu graph updates
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

hGraphStartX = 7
hGraphStartY = 53
hGraphHeight = 4
hGraphWidth = width - xOffset * 2 - 6

hGraphBgStartX = 72
hGraphBgStartY = 53

hGraphLineStartX = 66
hGraphLineStartY = 58

vGraphStartX = 7
vGraphStartY = 7
vGraphHeight = 43
vGraphWidth = 50

vGraphLineStartX = 95
vGraphLineStartY = 1

vGraphBgStartX = 97
vGraphBgStartY = 1

defaultConfigFile = '~/.pywmhdmonrc'
defaultRGBFiles = ('/usr/lib/X11/rgb.txt', '/usr/X11R6/lib/X11/rgb.txt')
defaultProcStat = '/proc/stat'
defaultProcMeminfo = '/proc/meminfo'

class PywmSysMon:
    def __init__(self, procMeminfo, procStat, ignoreNice=0, updateDelay=10):
        self._procStat = procStat
        self._procMeminfo = procMeminfo
        self._ignoreNice = ignoreNice

        self._lastUsed = 0
        self._lastTotal = 0

        self._usageHistory = [0.0] * vGraphWidth

        self._cpuUpdateDelay = updateDelay
        self._memUpdateDelay = 30

    def addUsageToHist(self, cpuUsage):
        self._usageHistory = self._usageHistory[1:]
        self._usageHistory.append(cpuUsage)

    def getMemInfo(self):
        """Get memory information.
         
        Return a tuple with (total_mem, used_mem, buffered_mem, cached_mem).
        """
        try:
            meminfoFile = file(self._procMeminfo, 'r')
        except IOError, e:
            sys.stderr.write("Can't open meminfo file: %s.\n" % str(e))
            sys.exit(2)
        total = used = free = shared = buffers = cached = theLine = None
        for line in meminfoFile:
            if line.startswith('Mem:'):
                theLine = line
                break
            if line.startswith('MemTotal:'):
                total = long(line.split()[1])
            if line.startswith('MemFree:'):
                free = long(line.split()[1])
            if line.startswith('Buffers:'):
                buffers = long(line.split()[1])
            if line.startswith('Cached:'):
                cached = long(line.split()[1])
        if free and total:
            used = total - free
        if theLine is not None:
            parts = [long(x) for x in theLine.split()[1]]
            total, used, free, shared, buffers, cached = parts[:6]
        if None in [total, used, buffers, cached]:
            sys.stderr.write("Can't find memory information in %s.\n" % 
                self._procMeminfo)
            sys.exit(4)
        return (total, used, buffers, cached)

    def freeMem(self, memData):
        """Take a tuple as returned from getMemInfo and return the free mem.
        """
        total, used, buffers, cached = memData
        reallyUsed = used - buffers - cached
        free = total - reallyUsed
        return free

    def getCPUUsage(self):
        """Get the current CPU usage.

        Only works for systems where this can be found in a /proc/stat like
        file. Return the usage in percent.
        """
        try:
            statFile = file(self._procStat, 'r')
        except IOError, e:
            sys.stderr.write("Can't open statfile: %s.\n" % str(e))
            sys.exit(2)
        line = statFile.readline()
        statFile.close()
        cpu, nice, system, idle = [long(x) for x in line.split()[1:]][:4]
        used = cpu + system
        if not self._ignoreNice:
            used += nice
        total = cpu + nice + system + idle
        if total - self._lastTotal <= 0 or self._lastTotal == 0:
            cpuUsage = 0.0
        else:
            cpuUsage = 100.0 * (float(used - self._lastUsed) / float(total -
                             self._lastTotal))
        self._lastUsed = used
        self._lastTotal = total
        return cpuUsage

    def addString(self, s, x, y):
        try:
            wmdocklib.addString(s, x, y, digits, xOffset, yOffset, width, height)
        except ValueError, e:
            sys.stderr.write('Error when painting string:\n' + str(e) + '\n')
            sys.exit(3)

    def paintGraph(self, percentFilled, x, y, w):
        """Paint a graph with percentFilled percent filled.

        Paint at position x, y and with width w.
        """
        paintWidth = int(round(percentFilled/100.0 * w))
        if paintWidth > 0:
            wmdocklib.copyXPMArea(
                hGraphLineStartX, hGraphLineStartY, paintWidth, hGraphHeight,
                x, y)
        if w - paintWidth > 0:
            wmdocklib.copyXPMArea(
                hGraphBgStartX, hGraphBgStartY, w - paintWidth, hGraphHeight,
                x + paintWidth, y)

    def drawVertLine(self, sourceX, sourceY, targX, targY, length):
        """Draw a vertical line.
        """
        if length > 0:
            wmdocklib.copyXPMArea(sourceX, sourceY, 1, length, targX, targY)

    def drawCPUUsageHistory(self):
        """Draw the complete CPU usage graph according to what's in the history.
        """
        count = 0
        for histItem in self._usageHistory:
            lengthFilled = int(round(vGraphHeight * (histItem/100.0)))
            lengthNotFilled = vGraphHeight - lengthFilled
            self.drawVertLine(vGraphBgStartX, vGraphBgStartY,
                              vGraphStartX + count, vGraphStartY,
                              lengthNotFilled)
            self.drawVertLine(vGraphLineStartX, vGraphLineStartY,
                              vGraphStartX + count,
                              vGraphStartY + lengthNotFilled, lengthFilled)
            count += 1

    def updateCPUInfo(self):
        """Update the current cpu usage graph."""
        currentUsage = self.getCPUUsage()
        self.addUsageToHist(currentUsage)
        self.drawCPUUsageHistory()

    def updateMemInfo(self):
        """Update the current memory usage graph."""
        memInfo = self.getMemInfo()
        total = memInfo[0]
        free = self.freeMem(memInfo)
        percentUsed = 100.0 * (float(total - free) / float(total))
        self.paintGraph(percentUsed, hGraphStartX, hGraphStartY, hGraphWidth)

    def _checkForEvents(self):
        event = wmdocklib.getEvent()
        while not event is None:
            if event['type'] == 'destroynotify':
                sys.exit(0)
            event = wmdocklib.getEvent()

    def mainLoop(self):
        counter = -1
        while 1:
            counter += 1
            self._checkForEvents()
            if counter % self._cpuUpdateDelay == 0:
                self.updateCPUInfo()
            if counter % self._memUpdateDelay == 0:
                self.updateMemInfo()
            if counter == 999999:
                counter = -1
            wmdocklib.redraw()
            time.sleep(0.1)

def parseCommandLine(argv):
    """Parse the commandline. Return a dictionary with options and values."""
    shorts = 'hf:g:b:p:a:r:s:m:iu:'
    longs = ['help=', 'barbgcolor=', 'barfgcolor=', 'background=',
             'graphforeground=', 'graphbackground=', 'rgbfile=', 'procstat=',
             'procmeminfo=', 'ignorenice', 'updatedelay=']
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
        if o in ('-b', '--background'):
            d['background'] = a
        if o in ('-r', '--rgbfile'):
            d['rgbfile'] = a
        if o in ('-g', '--barbgcolor'):
            d['barbgcolor'] = a
        if o in ('-f', '--barfgcolor'):
            d['barfgcolor'] = a
        if o in ('-s', '--procstat'):
            d['procstat'] = a
        if o in ('-p', '--graphforeground'):
            d['graphforeground'] = a
        if o in ('-a', '--graphbackground'):
            d['graphbackground'] = a
        if o in ('-m', '--procmeminfo'):
            d['procmeminfo'] = a
        if o in ('-i', '--ignorenice'):
            d['ignorenice'] = 1
        if o in ('-u', '--updatedelay'):
            try:
                d['updatedelay'] = int(a) * 10
            except ValueError:
                sys.stderr.write(
                    "Value for updatedelay has to be an integer.\n")
                sys.exit(2)
    return d



palette = {
    ' ': '#208120812081',
    '.': '#00000000FFFF',
    'o': '#C71BC30BC71B',
    'O': '#861782078E38',
    '+': '#EFBEF3CEEFBE',
    '@': '#618561856185',
    '#': '#9E79A2899E79',
    '$': '#410341034103',
    'o': '#2020b2b2aaaa',
    '/': '#2020b2b2aaaa',
    '-': '#707070707070',
    '|': '#2020b2b2aaaa',
    'I': '#707070707070',
    '_': '#000000000000',
    '%': '#2081B2CAAEBA',
    }
background = \
[' ...............................................................................................',
 ' .///..___..ooo..___..___......|.I..............................................................',
 ' .///..___..ooo..___..___......|.I..............................................................',
 ' .///..___..ooo..___..___......|.I..............................................................',
 ' .///..___..___..___..___......|.I..............................................................',
 ' .///..___..___..___..___......|.I..............................................................',
 ' .///..___..___..___..___......|.I..............................................................',
 ' .///..___..___..ooo..___......|.I..............................................................',
 ' .///..___..___..ooo..___......|.I..............................................................',
 ' .///..___..___..ooo..___......|.I..............................................................',
 ' .///..___..___..___..___......|.I..............................................................',
 ' .///..___..___..___..___......|.I..............................................................',
 ' .///..___..___..___..___......|.I..............................................................',
 ' .///..___..___..___..ooo......|.I..............................................................',
 ' .///..___..___..___..ooo......|.I..............................................................',
 ' .///..___..___..___..ooo......|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///..........................|.I..............................................................',
 ' .///...........................................................................................',
 ' .///...-------------------------------------------------------------------------------------...',
 ' .///...-------------------------------------------------------------------------------------...',
 ' .///...-------------------------------------------------------------------------------------...',
 ' .///...-------------------------------------------------------------------------------------...',
 ' .///...........................................................................................',
 ' .///////////////////////////////////////////////////////////////////////////////////////////...',
 ' .///////////////////////////////////////////////////////////////////////////////////////////...',
 ' .///////////////////////////////////////////////////////////////////////////////////////////...',
 ' .///////////////////////////////////////////////////////////////////////////////////////////...',
 ' ...............................................................................................',
 ' ...............................................................................................',
 ]

def main():
    global char_width, char_height
    char_width, char_height = wmdocklib.initPixmap(background,
                                                   font_name='6x8',
                                                   palette=palette)
    config = parseCommandLine(sys.argv)
    procStat = config.get('procstat', defaultProcStat)
    if not os.access(procStat, os.R_OK):
        sys.stderr.write(
            "Can't read your procstat file, try setting it with -s.\n")
        sys.exit(4)
    procMeminfo = config.get('procmeminfo', defaultProcMeminfo)
    if not os.access(procMeminfo, os.R_OK):
        sys.stderr.write(
            "Can't read your procmeminfo file, try setting it with -m.\n")
        sys.exit(4)
    ignoreNice = config.get('ignorenice', 0)
    updateDelay = config.get('updatedelay', 30)
    try:
        programName = sys.argv[0].split(os.sep)[-1]
    except IndexError:
        programName = ''
    sys.argv[0] = programName
    wmdocklib.openXwindow(sys.argv, width, height)
    pywmsysmon = PywmSysMon(procMeminfo, procStat, ignoreNice, updateDelay)
    pywmsysmon.mainLoop()



if __name__ == '__main__':
    main()
