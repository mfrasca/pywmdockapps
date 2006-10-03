#!/usr/bin/env python

"""pywmdatetime.py

WindowMaker dockapp that displays time, date, weekday and week number.

Copyright (C) 2003 Kristoffer Erlandsson

Licensed under the GNU General Public License.


Changes:
2003-09-01 Kristoffer Erlandsson
Fixed a bug where the week didn't update if we used %q style week numbering.

2003-06-28 Kristoffer Erlandsson
Fixed a bug where a mouse click caused an infinite loop

2003-06-26 Kristoffer Erlandsson
Fixed bug when longer strings didn't get cleared when shorter ones where
painted. Now only repaint the strings when they have changed.

2003-06-24 Kristoffer Erlandsson
Added event handling for graceful shutdown

2003-06-16 Kristoffer Erlandsson
First workingish version
"""
usage = """pywmdatetime.py [options]
Available options are:
-h, --help                      print this help
-f, --foreground <color>        set the foreground color
-b, --background <color>        set the background color
-t, --timeformat <format>       set the time format
-d, --dateformat <format>       set the date format
-y, --weekdayformat <format>    set the weekday format
-e, --weekformat <format>       set the week format
-r, --rgbfile <file>            set the rgb file to get color codes from
-c, --configfile <file>         set the config file to use

The formats are the same as Python's strftime() accept. See the sample
rc-file for more information about this.
"""

import sys
import time
import getopt
import os

from pywmgeneral import pywmhelpers

width = 64
height = 64

lettersStartX = 0
lettersStartY = 74
letterWidth = 6
letterHeight = 8

digitsStartX = 0
digitsStartY = 64
digitWidth = 6
digitHeight = 8

xOffset = 4
yOffset = 4

letters = 'abcdefghijklmnopqrstuvwxyz'
digits = '0123456789:/- '

timeDefaultFormat = '%H:%M:%S'
dateDefaultFormat = '%d-%m-%y'
dayDefaultFormat = '%A'
weekDefaultFormat = 'wk %q'  # %q added by me for different week calculation.

defaultConfigFile = '~/.pywmdatetimerc'
defaultRGBFiles = ['/usr/lib/X11/rgb.txt', '/usr/X11R6/lib/X11/rgb.txt']
maxCharsPerLine = 9

def addString(s, x, y):
    try:
        pywmhelpers.addString(s, x, y, letterWidth, letterHeight, lettersStartX,
                          lettersStartY, letters, digitWidth, digitHeight,
                          digitsStartX, digitsStartY, digits, xOffset, yOffset,
                          width, height)
    except ValueError, e:
        sys.stderr.write('Error when painting string:\n' + str(e) + '\n')
        sys.exit(3)

def clearLine(y):
    '''Clear a line of text at position y.'''
    pywmhelpers.copyXPMArea(73, yOffset, width - 2 * xOffset, letterHeight,
                            xOffset, y + yOffset)

def getCenterStartPos(s):
    return pywmhelpers.getCenterStartPos(s, letterWidth, width, xOffset)

def getVertSpacing(numLines, margin):
    return pywmhelpers.getVertSpacing(numLines, margin, height, letterHeight, 
                                      yOffset)

def calculateWeek(localTime):
    '''Calculate the week number as we do, for example in Sweden.
    
    That is, add one to the %W format if the year didn't start on a monday.'''
    day = int(time.strftime('%j', localTime))
    weekDay = int(time.strftime('%w')) - 1
    if weekDay == -1:
        weekDay = 6
    lastMonday = day - weekDay
    if lastMonday % 7 == 0:
        return int(time.strftime('%W'))
    return int(time.strftime('%W')) + 1

def parseCommandLine(argv):
    '''Parse the commandline. Return a dictionary with options and values.'''
    shorts = 'hf:b:t:d:e:y:r:c:'
    longs = ['help', 'foreground=', 'background=', 'timeformat=', 'dateformat=',
             'weekdayformat=', 'weekformat=', 'rgbfile=', 'configfile=']
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
        if o in ('-f', '--foreground'):
            d['foreground'] = a
        if o in ('-b', '--background'):
            d['background'] = a
        if o in ('-t', '--timeformat'):
            d['timeformat'] = a
        if o in ('-d', '--dateformat'):
            d['dateformat'] = a
        if o in ('-y', '--weekdayformat'):
            d['weekdayformat'] = a
        if o in ('-e', '--weekformat'):
            d['weekformat'] = a
        if o in ('-r', '--rgbfile'):
            d['rgbfile'] = a
        if o in ('-c', '--configfile'):
            d['configfile'] = a
    return d

def checkForEvents():
    event = pywmhelpers.getEvent()
    while not event is None:
        if event['type'] == 'destroynotify':
            sys.exit(0)
        event = pywmhelpers.getEvent()

def mainLoop(timeFmt, dateFmt, dayFmt, weekFmt):
    recalcWeek = weekFmt.find('%q') + 1  # True if we found %q.
    counter = -1
    lastStrs = [''] * 4
    while 1:
        counter += 1
        checkForEvents()
        lt = time.localtime()
        timeStr = time.strftime(timeFmt, lt)[:maxCharsPerLine]
        margin = 3
        spacing = getVertSpacing(4, margin)
        timeX = getCenterStartPos(timeStr)
        if lastStrs[0] != timeStr:
            clearLine(margin) 
            addString(timeStr, timeX, margin)
        lastStrs[0] = timeStr
        if counter % 100 == 0:
            # We only perform the date/week checks/updates once every 100th
            # iteration. We will maybe lag behind a couple of seconds when
            # switching, but switching occurs seldom and it will be alot of
            # unnecessary checks :).
            dateStr = time.strftime(dateFmt, lt)[:maxCharsPerLine]
            if recalcWeek:
                week = calculateWeek(lt)
                newWeekFmt = weekFmt.replace('%q', str(week))
            weekStr = time.strftime(newWeekFmt, lt)[:maxCharsPerLine]
            dayStr = time.strftime(dayFmt, lt)[:maxCharsPerLine]
            dateX = getCenterStartPos(dateStr)
            weekX = getCenterStartPos(weekStr)
            dayX = getCenterStartPos(dayStr)
            if lastStrs[1] != dateStr:
                clearLine(margin + spacing + letterWidth)
                addString(dateStr, dateX, margin + spacing + letterWidth)
            lastStrs[1] = dateStr
            if lastStrs[2] != dayStr:
                clearLine(margin + 2 * (spacing + letterWidth))
                addString(dayStr, dayX, margin + 2 * (spacing + letterWidth))
            lastStrs[2] = dayStr
            if lastStrs[3] != weekStr:
                clearLine(margin + 3 * (spacing + letterWidth))
                addString(weekStr, weekX, margin + 3 * (spacing + letterWidth))
            lastStrs[3] = weekStr
        if counter == 999999:
            counter = -1
        pywmhelpers.redraw()
        time.sleep(0.1)

def parseColors(defaultRGBFileNames, config, xpm):
    rgbFileName = ''
    for fn in defaultRGBFileNames:
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
        colors = (('foreground', 'text'),
                  ('background', 'background'))
        for key, value in colors:
            col = config.get(key)
            if not col is None:
                code = pywmhelpers.getColorCode(col, rgbFileName)
                if code is None:
                    sys.stderr.write('Bad colorcode for %s, ignoring.\n' % key)
                else:
                    pywmhelpers.setColor(xpm, value, code)

def main():
    clConfig = parseCommandLine(sys.argv)
    configFile = clConfig.get('configfile', defaultConfigFile)
    configFile = os.path.expanduser(configFile)
    fileConfig = pywmhelpers.readConfigFile(configFile, sys.stderr)
    # Merge the two configs, let the commandline options overwrite those in the
    # configuration file.
    config = fileConfig
    for i in clConfig.iteritems():
        config[i[0]] = i[1]

    parseColors(defaultRGBFiles, config, xpm)
    pywmhelpers.setDefaultPixmap(xpm)
    timeFmt = config.get('timeformat', timeDefaultFormat)
    dateFmt = config.get('dateformat', dateDefaultFormat)
    dayFmt = config.get('weekdayformat', dayDefaultFormat)
    weekFmt = config.get('weekformat', weekDefaultFormat)
    # openXwindow sets the window title to the program name. If we get the
    # program name with a path, split it so we only name the window with the
    # filename.
    try:
        programName = sys.argv[0].split(os.sep)[-1]
    except IndexError:  # Should only happen when using the interpreter.
        programName = ''
    sys.argv[0] = programName
    pywmhelpers.openXwindow(sys.argv, width, height)
    mainLoop(timeFmt, dateFmt, dayFmt, weekFmt)

xpm = \
['160 100 11 1',
 ' \tc #208120812081',
 '.\tc #00000000FFFF',
 'o\tc #C71BC30BC71B',
 'O\tc #861782078E38',
 '+\tc #EFBEF3CEEFBE',
 '@\tc #618561856185',
 '#\tc #9E79A2899E79',
 '$\tc #410341034103',
 '/\tc #2020b2b2aaaa s graph',
 'X\tc #000000000000 s background',
 '%\tc #2081B2CAAEBA s text',
 '                                                                ................................................................................................',
 '                                                                ..///...........................................................................................',
 '                                                                ..///...........................................................................................',
 '                                                                ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///....XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...............................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///...........................................................................................',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///////////////////////////////////////////////////////////////////////////////////////////...',
 '    XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX    ..///////////////////////////////////////////////////////////////////////////////////////////...',
 '                                                                ..///////////////////////////////////////////////////////////////////////////////////////////...',
 '                                                                ................................................................................................',
 '                                                                ................................................................................................',
 '                                                                ................................................................................................',
 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%%%%%XXX%XXX%%%%%X%%%%%X%XXX%X%%%%%X%%%%%X%%%%%X%%%%%X%%%%%XXXXXXXXXX%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XX%%XXXXXXX%XXXXX%X%XXX%X%XXXXX%XXXXXXXXX%X%XXX%X%XXX%XX%%XXXXXX%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXXXXXX%XXXXX%X%XXX%X%XXXXX%XXXXXXXXX%X%XXX%X%XXX%XX%%XXXXX%%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXX%%%%%XX%%%%X%%%%%X%%%%%X%%%%%XXXXX%X%%%%%X%%%%%XXXXXXXXX%XXX%%%%%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXX%XXXXXXXXX%XXXXX%XXXXX%X%XXX%XXXXX%X%XXX%XXXXX%XXXXXXXX%%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%XXX%XXX%XXX%XXXXXXXXX%XXXXX%XXXXX%X%XXX%XXXXX%X%XXX%XXXXX%XX%%XXXX%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
 'X%%%%%XX%%%XX%%%%%X%%%%%XXXXX%X%%%%%X%%%%%XXXXX%X%%%%%X%%%%%XX%%XXXX%XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX............................',
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

