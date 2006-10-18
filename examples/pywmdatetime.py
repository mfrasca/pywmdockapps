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
-F, --font <file>               set the font name
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

import wmdocklib

width = 64
height = 64

xOffset = 4
yOffset = 4

timeDefaultFormat = '%H:%M:%S'
dateDefaultFormat = '%d-%m-%y'
dayDefaultFormat = '%A'
weekDefaultFormat = 'wk %q'  # %q added by Kristoffer for different week calculation.

defaultConfigFile = '~/.pywmdatetimerc'
maxCharsPerLine = None

def addString(s, x, y):
    try:
        wmdocklib.addString(s, x, y, xOffset, yOffset,
                          width, height)
    except ValueError, e:
        sys.stderr.write('Error when painting string:\n' + str(e) + '\n')
        sys.stderr.write('test %s' % ((s, x, y, xOffset, yOffset,
                                      width, height),))
        raise
        sys.exit(3)

def addTimeString(s, x, y):
    for c in s:
        charW = 7
        charX = 64 + (ord(c) - ord('0')) % 5 * 7
        if c <='4': charY = 44
        else: charY = 54
        if not c.isdigit():
            charX = 64 + 35
            charW = 3
        wmdocklib.copyXPMArea(charX, charY, charW, 10, x+xOffset, y+yOffset)
        x += charW

def clearLine(y):
    '''Clear a line of text at position y.'''
    wmdocklib.copyXPMArea(73, yOffset, width - 2 * xOffset, char_height,
                            xOffset, y + yOffset)

def getCenterStartPos(s):
    return wmdocklib.getCenterStartPos(s, width, xOffset)

def getVertSpacing(numLines, margin):
    return wmdocklib.getVertSpacing(numLines, margin-1, height, yOffset) + 1

def calculateWeek(localTime):
    """Calculate the week number as we do, for example in Sweden.
    
    That is, add one to the %W format if the year didn't start on a monday."""
    day = int(time.strftime('%j', localTime))
    weekDay = int(time.strftime('%w')) - 1
    if weekDay == -1:
        weekDay = 6
    lastMonday = day - weekDay
    if lastMonday % 7 == 0:
        return int(time.strftime('%W'))
    return int(time.strftime('%W')) + 1

def parseCommandLine(argv):
    """Parse the commandline. Return a dictionary with options and values."""
    shorts = 'hf:b:t:d:e:y:r:c:F:a'
    longs = ['antialiased', 'help', 'foreground=', 'background=', 'timeformat=', 'dateformat=',
             'weekdayformat=', 'weekformat=', 'rgbfile=', 'configfile=', 'font=']
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
        if o in ('-a', '--antialiased'):
            d['antialiased'] = True
        if o in ('-f', '--foreground'):
            d['foreground'] = a
        if o in ('-F', '--font'):
            d['font'] = a
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
    event = wmdocklib.getEvent()
    while not event is None:
        if event['type'] == 'destroynotify':
            sys.exit(0)
        event = wmdocklib.getEvent()

def mainLoop(timeFmt, dateFmt, dayFmt, weekFmt):
    recalcWeek = weekFmt.find('%q') + 1  # True if we found %q.
    newWeekFmt = weekFmt
    counter = -1
    lastStrs = [''] * 4
    while 1:
        counter += 1
        checkForEvents()
        lt = time.localtime()
        timeStr = time.strftime(timeFmt, lt)[:maxCharsPerLine]
        timeX = 3
        if antialiased:
            margin = 6
            spacing = getVertSpacing(4, margin)
            if lastStrs[0] != timeStr:
                addTimeString(timeStr, timeX, margin-4)
            margin += 1
        else:
            margin = 4
            spacing = getVertSpacing(4, margin)
            if lastStrs[0] != timeStr:
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
                clearLine(margin + spacing + char_width)
                addString(dateStr, dateX, margin + spacing + char_width)
            lastStrs[1] = dateStr
            if lastStrs[2] != dayStr:
                clearLine(margin + 2 * (spacing + char_width))
                addString(dayStr, dayX, margin + 2 * (spacing + char_width))
            lastStrs[2] = dayStr
            if lastStrs[3] != weekStr:
                clearLine(margin + 3 * (spacing + char_width))
                addString(weekStr, weekX, margin + 3 * (spacing + char_width))
            lastStrs[3] = weekStr
        if counter == 999999:
            counter = -1
        wmdocklib.redraw()
        time.sleep(0.1)

background = [
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                                ",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"                                                               7",
"7777777777777777777777777777777777777777777777777777777777777777",
"                                                                ",
"                                                                ",
".+@@+.....#@...#@@#...#@@#....$@%..                             ",
"$@==@$...+@@..&@--@&.*@--@&...#@%..                             ",
"&@**@&..#@@@..&@$.@%.&-..@%..*@@%..                             ",
"%@..@%..#+%@.....$@%....+@#..--@%..                             ",
"%@..@%....%@.....%@*...%@-..*@$@%..                             ",
"%@..@%....%@....+@%....&-@+.=#.@%..                             ",
"%@..@%....%@...+@=$......-@.@-%@=&.                             ",
"&@**@&....%@..$@=$...&-..-@.@@@@@%.                             ",
"$@==@$....%@..#@-%%&.+@--@#....@%..                             ",
".+@@+.....%@..@@@@@%..#@@#.....@%..                             ",
".@@@@+..+=@%..+@@@@@..%@@+...&@@#......                         ",
"*@-%%*.$==-@&.*%%%@=.#@-=@*.*@=-@&.....                         ",
"+@+....+@*.%*....+@*.%@.+@+.%@$.-%.*+..                         ",
"&@=@#..%@$+$.....--..&@&%@$.%@..%@.%@..                         ",
"%@%=@*.%@=@@*...*@&...=@@#..&@%&@@.*+..                         ",
".*.$@%.%@%&@-...#@...#@&%@*..=@@@@.....                         ",
"....@%.%@..%@...=-...@%..@%...+*%@.&%..                         ",
"--.*@#.+@$.-@...@%...@-.$@%.$#*.=%.%@..                         ",
"%@-=@$.$@=-@#..+@+...#@-=@*.$@=-@+.....                         ",
"$-@=+...+=@%$..+@+...$#@@&...+@@#......                         ",
]

def main():
    clConfig = parseCommandLine(sys.argv)
    configFile = clConfig.get('configfile', defaultConfigFile)
    configFile = os.path.expanduser(configFile)
    fileConfig = wmdocklib.readConfigFile(configFile, sys.stderr)
    # Merge the two configs, let the commandline options overwrite those in the
    # configuration file.
    config = fileConfig
    for i in clConfig.iteritems():
        config[i[0]] = i[1]

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

    palette = {
        ".":"#181818",
        "+":"#6E6E0F",
        "@":"#FFFF00",
        "#":"#A0A009",
        "$":"#3B3B14",
        "%":"#B9B907",
        "&":"#87870C",
        "*":"#545411",
        "=":"#E6E602",
        "-":"#CFCF04",
        }
    palette[0] = clConfig.get('background', 'black')
    palette[2] = clConfig.get('foreground', 'cyan3')
    
    font = clConfig.get('font', '6x8orig')
    
    global char_width, char_height, maxCharsPerLine, antialiased
    char_width, char_height = wmdocklib.initPixmap(background,
                                                   font_name=font,
                                                   bg=0, fg=2, palette=palette)
    maxCharsPerLine = (width-2*xOffset) / char_width
    antialiased = clConfig.get('antialiased', False)

    wmdocklib.openXwindow(sys.argv, width, height)
    if antialiased:
        wmdocklib.copyXPMArea(64+2*xOffset+1, 27, width - 2*xOffset, 17, xOffset, yOffset)
    mainLoop(timeFmt, dateFmt, dayFmt, weekFmt)

if __name__ == '__main__':
    main()

