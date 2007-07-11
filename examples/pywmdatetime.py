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

import sys
import time
import os

from wmdocklib import wmoo, readConfigFile

width = 64
height = 64

xOffset = 4
yOffset = 4

patterns = [
".+@@+.....#@...#@@#...#@@#....$@%...@@@@+..+=@%..+@@@@@..%@@+...&@@#.....",
"$@==@$...+@@..&@--@&.*@--@&...#@%..*@-%%*.$==-@&.*%%%@=.#@-=@*.*@=-@&....",
"&@**@&..#@@@..&@$.@%.&-..@%..*@@%..+@+....+@*.%*....+@*.%@.+@+.%@$.-%.*+.",
"%@..@%..#+%@.....$@%....+@#..--@%..&@=@#..%@$+$.....--..&@&%@$.%@..%@.%@.",
"%@..@%....%@.....%@*...%@-..*@$@%..%@%=@*.%@=@@*...*@&...=@@#..&@%&@@.*+.",
"%@..@%....%@....+@%....&-@+.=#.@%...*.$@%.%@%&@-...#@...#@&%@*..=@@@@....",
"%@..@%....%@...+@=$......-@.@-%@=&.....@%.%@..%@...=-...@%..@%...+*%@.&%.",
"&@**@&....%@..$@=$...&-..-@.@@@@@%.--.*@#.+@$.-@...@%...@-.$@%.$#*.=%.%@.",
"$@==@$....%@..#@-%%&.+@--@#....@%..%@-=@$.$@=-@#..+@+...#@-=@*.$@=-@+....",
".+@@+.....%@..@@@@@%..#@@#.....@%..$-@=+...+=@%$..+@+...$#@@&...+@@#.....",
]
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

timeDefaultFormat = '%H:%M:%S'
dateDefaultFormat = '%d-%m-%y'
dayDefaultFormat = '%A'
weekDefaultFormat = 'wk %q'  # %q added by Kristoffer for different week calculation.

defaultConfigFile = '~/.pywmdatetimerc'

class Application(wmoo.Application):

    def __init__(self):

        from optparse import OptionParser

        parser = OptionParser()
        parser.add_option('-a', '--antialiased', dest='antialiased',
                          action="store_true", default=False)
        parser.add_option('-f', '--foreground', type='string', default='cyan3')
        parser.add_option('-F', '--font', type='string', default='6x8orig')
        parser.add_option('-b', '--background', type='string', default='black')
        parser.add_option('-t', '--timeformat', type='string', default=timeDefaultFormat)
        parser.add_option('-d', '--dateformat', default=dateDefaultFormat)
        parser.add_option('-y', '--weekdayformat', default=dayDefaultFormat)
        parser.add_option('-e', '--weekformat', default=weekDefaultFormat)
        parser.add_option('-r', '--rgbfile')
        #parser.add_option('-c', '--configfile', default=defaultConfigFile)
        parser.add_option('--debug', action='store_true', default=False)

        configFile = os.path.expanduser("~/.pywmdatetimerc")
        # Merge the two configs, let the commandline options overwrite those in the
        # configuration file.
        config = readConfigFile(configFile, sys.stderr)
        parser.set_defaults(**config)

        (options, args) = parser.parse_args()

        palette[0] = options.background
        palette[2] = options.foreground

        if options.antialiased:
            background = [((6,3),(57,19)),
                          ((3,22),(60,60))]
        else:
            background = [((3,3),(59,60))]

        wmoo.Application.__init__(self,
                                  patterns=patterns,
                                  font_name=options.font,
                                  bg=0, fg=2, palette=palette,
                                  background=background,
                                  debug=options.debug)
        

        if options.antialiased:
            self.addWidget('date', wmoo.Label, orig=(4,24), size=(54,10), align=wmoo.CENTRE)
            self.addWidget('day', wmoo.Label, orig=(4,36), size=(54,10), align=wmoo.CENTRE)
            self.addWidget('week', wmoo.Label, orig=(4,48), size=(54,10), align=wmoo.CENTRE)
        else:
            self.addWidget('time', wmoo.Label, orig=(4, 5), size=(54,10), align=wmoo.CENTRE)
            self.addWidget('time2', wmoo.Label, orig=(4,16), size=(54,10), align=wmoo.CENTRE)
            self.addWidget('date', wmoo.Label, orig=(4,27), size=(54,10), align=wmoo.CENTRE)
            self.addWidget('day', wmoo.Label, orig=(4,38), size=(54,10), align=wmoo.CENTRE)
            self.addWidget('week', wmoo.Label, orig=(4,49), size=(54,10), align=wmoo.CENTRE)

        self.timeFmt = options.timeformat
        self.dateFmt = options.dateformat
        self.dayFmt = options.weekdayformat
        self.weekFmt = options.weekformat
        self.antialiased = options.antialiased
        self.debug = options.debug

        self.recalcWeek = self.weekFmt.find('%q') + 1  # True if we found %q.
        self.counter = -1
        self.lastStrs = [''] * 4

        pass

    def calculateWeek(self, localTime):
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

    def updateTimeString(self, s):
        if self.antialiased:
            x, y = 8, 6
            for c in s:
                charW = 7
                charX = (ord(c) - ord('0')) * 7
                if not c.isdigit():
                    charX = 70
                    charW = 3
                self.putPattern(charX, 0, charW, 10, x, y)
                x += charW
        else:
            self['time'].setText(s)

    def update(self):
        self.counter += 1
        lt = time.localtime()
        timeStr = time.strftime(self.timeFmt, lt)
        self.updateTimeString(timeStr)
        self.lastStrs[0] = timeStr
        if self.counter % 100 == 0:
            # We only perform the date/week checks/updates once every 100th
            # iteration. We will maybe lag behind a couple of seconds when
            # switching, but switching occurs seldom and it will be alot of
            # unnecessary checks :).
            dateStr = time.strftime(self.dateFmt, lt)
            newWeekFmt = self.weekFmt
            if self.recalcWeek:
                week = calculateWeek(lt)
                newWeekFmt = self.weekFmt.replace('%q', str(week))
            weekStr = time.strftime(newWeekFmt, lt)
            dayStr = time.strftime(self.dayFmt, lt)
            if self.lastStrs[1] != dateStr:
                self['date'].setText(dateStr)
            self.lastStrs[1] = dateStr
            if self.lastStrs[2] != dayStr:
                self['day'].setText(dayStr)
            self.lastStrs[2] = dayStr
            if self.lastStrs[3] != weekStr:
                self['week'].setText(weekStr)
            self.lastStrs[3] = weekStr

if __name__ == '__main__':
    app = Application()
    app.run()
