#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pywmgeneric.py

WindowMaker dockapp to display the output from an external program, or the
string returned from a python function. Mouse actions can be associated with
the displayed text.

Copyright (C) 2003 Kristoffer Erlandsson

Licensed under the GNU General Public License.


Changes
2003-07-02 Kristoffer Erlandsson
Added support for up to 10 mouse buttons.
The char translation now handles both upper and lower case.

2003-06-29 Kristoffer Erlandsson
Additional error checking around string interpolations from cfg file.

2003-06-27 Kristoffer Erlandsson
First working version
"""

usage = """pywmgeneric.py [options]
Available options are:
    -h, --help                  print this help
    -t, --text <color>          set the text color
    -b, --background <color>    set the background color
    -F, --font <file>           set the font name
    -r, --rgbfile <file>        set the rgb file to get color codes from
    -c, --configfile <file>     set the config file to use
"""

import sys
import os
import time
import string
import ConfigParser
import getopt
import popen2

import wmdocklib

prevStat = {'user':0,
            'nice':0,
            'sys':0,
            'idle':0,
            'total':0,
            }
import re
cpuinfo = re.compile(r'^cpu[^ ]* +(?P<user>[0-9]+) +(?P<nice>[0-9]+)'
                     r'+(?P<sys>[0-9]+) +(?P<idle>[0-9]+)')

class UserMethods:
    """Put methods that should be called when the action is method=... here.

    The action methods should return a function, which in turn returns
    the string to be displayed (if no 'display =' exists) and stored
    for later retreival.

    The mouse action methods gets the entry instance as an argument. Return
    value doesn't matter.

    An instance of this class is created at initialization and passed to all
    entries, so keep in mind that they share the same object.

    THE METHODS ALREADY HERE ARE JUST SAMPLES AND WILL PROBABLY NOT WORK
    WITH YOUR SYSTEM.
    """

    userTicks = sysTicks = niceTicks = idleTicks = 0
    
    def getCpuTemp(self):
        def result():
            global prevStat
            try:
                f = file('/proc/stat', 'r')
            except IOError:
                return 'error'

            currStat = dict(
                [(k, int(v))
                 for (k,v) in cpuinfo.match(f.readline()).groupdict().items()]
                )
            f.close()

            total = 0
            for k,v in currStat.items():
                total += v
            currStat['total'] = total
            totalTicks = (currStat['total'] - prevStat['total'])

            result = {}
            if (totalTicks <= 0):
                return '00/00/00'

            for k in prevStat:
                result[k] = (100. * (currStat[k] - prevStat[k])) / totalTicks
            prevStat = currStat

            return '%(user)02.f/%(sys)02.f/%(idle)02.f' % result
        return result

    def getSysTemp(self):
        try:
            f = file('/proc/sys/dev/sensors/w83697hf-isa-0290/temp1', 'r')
        except IOError:
            return lambda: 'error'
        temp = f.readline().split()[2]
        f.close()
        return lambda: 'sys: %s' % temp

    def ls(self):
        return lambda: 'boh'

    def showDnWithoutDescs(self, entry):
        """Strip descriptions from some text where the descs are indented.

        Display it in an xmessage.
        """
        text = entry.getAllText()
        s = '\n'.join([x for x in text.split('\n') if not x.startswith('   ')])
        os.system('xmessage "' + s.replace('"', r'\"') + '" &')
        
    def showTvWithoutDescs(self, entry):
        """Strip descriptions from some text where the descs are indented.

        Display it in an xmessage.
        """
        text = entry.getAllText()
        s='\n'.join([x for x in
            text.split('\n')[1:] if not x.startswith('   ')])
        s = s.replace('\n\n', '\n')
        os.system('xmessage "' + s.replace('"', r'\"') + '" &')

width = 64
height = 64

xOffset = 4
yOffset = 4

maxChars = 13

defaultConfigFile = '~/.pywmgenericrc'
defaultRGBFiles = ('/usr/share/X11/rgb.txt', '/usr/X11R6/lib/X11/rgb.txt')

err = sys.stderr.write

def addString(s, x, y):
    """Convenience function around pwymhelpers.addString."""
    try:
        wmdocklib.addString(s, x, y, xOffset, yOffset,
                            width, height)
    except ValueError, e:
        sys.stderr.write('Error when painting string:\n' + str(e) + '\n')
        sys.exit(3)

def clearLine(y):
    """Clear a line of text at position y."""
    wmdocklib.copyXPMArea(0, 64+yOffset,
                          width - 2 * xOffset, char_height,
                          xOffset, y + yOffset)

def getXY(line):
    """Return the x and y positions to be used at line line."""
    return 0, line * (char_height + 3) + 1

def isTrue(s):
    """Return true if the string s can be interpreted as a true value.

    Raises ValueError if we get a string we don't like.
    """
    trueThings = ['on', 'yes', '1', 'true']
    falseThings = ['off', 'no', '0', 'false']
    if s in trueThings:
        return 1
    elif s in falseThings:
        return 0
    raise ValueError


class Entry:
    def __init__(self, line, updateDelay, action, mouseActions,
                 userMethods, display=None, scrollText=1):
        self._updateDelay = updateDelay
        self._line = line
        self._action = self._parseAction(action)
        self._mouseActions = [self._parseAction(a) for a in mouseActions]
        self._userMethods = userMethods
        self._display = display
        self._scrollText = scrollText

        self._glue = ' ... '
        self._scrollPos = 0
        self._tickCount = 0L

        self._runningProcs = []
        self._actionProc = None
        self._getTextMethod = None
        self._allText = ''
        self._displayLine = ''
        # Do one action when we start, so we are sure that one gets done even
        # if we do not want any other updates.
        self._doAction()
        self._lastActionAt = time.time()

    def _parseAction(self, action):
        """Parse an action string, return (<action>, <argument string>).
        
        Or none if we get an empty action."""
        if action:
            whatToDo = action.split()[0]
            argStr = action[len(whatToDo):].lstrip()
            return (whatToDo, argStr)
        return None

    def _execExternal(self, command):
        """Exec an external command in the background.
        
        Return the running process as created by Popen3()."""
        proc = popen2.Popen3(command)
        self._runningProcs.append(proc)
        return proc

    def _doMouseAction(self, button):
        """Perform the mouse action associated with a button."""
        if len(self._mouseActions) < button:
            return  # Just for safety, shouldn't happen.
        item = self._mouseActions[button - 1]
        if item:
            # We have an action associated with the button.
            action, arg = item
        else:
            # No action associated with the button.
            return
        if action == 'exec':
            self._execExternal(self._expandStr(arg))
        elif action == 'method':
            try:
                method = getattr(self._userMethods, arg)
            except AttributeError:
                method = None
            if method:
                method(self)
            else:
                err("Warning: Method %s does not exist." % arg)
        elif action == 'update':
            self._doAction()
        else:
            err("Warning: Unknown mouse action: %s, ignoring.\n" % action)

    def _doAction(self):
        """Perform the action associated with this entry."""
        if self._action is None:
            return
        action, arg = self._action
        if action == 'exec':
            if self._actionProc is None :
                self._actionProc = self._execExternal(arg)
            else:
                if not self._actionProc in self._runningProcs:
                    # The action process since the last time is finished, we
                    # can start another one without risking that we get
                    # flooded by processes.
                    self._actionProc = self._execExternal(arg)
            self._getTextMethod = self._readFromActionProc
        elif action == 'method':
            try:
                method = getattr(self._userMethods, arg)
            except AttributeError:
                method = None
            if method:
                self._getTextMethod = method()
            else:
                err('Warning: method %s does not exist. Ignoring.\n' % arg)
        else:
            err("Warning: Unknown action: %s, ignoring.\n" % action)
            
    def _readFromActionProc(self):
        """If our action process is ready, return the output. Otherwise None.
        """
        if self._actionProc.poll() == -1:
            # Wait until the process is ready before we really read the text.
            return None
        # fromchild.read() will return '' if we allready have read the output
        # so there will be no harm in calling this method more times.
        return self._actionProc.fromchild.read()

    def _reapZombies(self):
        """Poll all running childs. This will reap all zombies."""
        i = 0
        for p in self._runningProcs:
            val = p.poll()
            if val != -1:
                self._runningProcs.pop(i)
            i += 1

    def _updateText(self):
        """Get the text, update the display if it has changed.
        """
        text = ''
        if self._getTextMethod:
            text = self._getTextMethod()
            # Only change the text if we get anything from the getTextMethod()
            if text:
                self._allText = text
        if self._display is None:
            # We have no display = in the config file, we want to
            # display the first line of the output of the action.
            if text:
                displayLine = text.split(os.linesep)[0]
            else:
                displayLine = self._displayLine
        else:
            displayLine = self._display
        if displayLine != self._displayLine:
            # Line to display has changed, display the new one.
            self._displayLine = displayLine
            self._scrollPos = 0
            self.displayText(displayLine)
        elif len(self._displayLine) > maxChars and self._scrollText:
            # Line is the same and is longer than the display and we
            # want to scroll it.
            if self._tickCount % 2 == 0:
                # Only scroll every third tick.
                self._scrollAndDisplay()

    def _scrollAndDisplay(self):
        """Scroll the text one step to the left and redisplay it.

        When reaching the end, paint number of spaces before scrolling in the
        same line again from the right.
        """

        # increase the amount of scrolled chars by one, modulo the lenght.
        # take the line, append to it some glue and a copy of the line
        # again, drop as many characters as the updated scrollPos, display
        # the resulting text.
        self._scrollPos += 1
        self._scrollPos %= len(self._displayLine) + len(self._glue)
        disp = self._displayLine + self._glue + self._displayLine
        disp = disp[self._scrollPos:]
        self.displayText(disp)

    def tick1(self):
        """Do things that should be done often.
        """
        self._tickCount += 1
        self._reapZombies()
        self._updateText()
        currTime = time.time()
        if not self._updateDelay is None and \
                currTime - self._lastActionAt > self._updateDelay:
            # We want to do this last in the tick so the command gets the time
            # to finish before the next tick (if it's a fast one).
            self._lastActionAt = currTime
            self._doAction()

    def tick2(self):
        """Do things that should be done a bit less often.
        """
        pass

    def translateText(self, text):
        """Translate chars that can't be painted in the app to something nicer.
        
        Or nothing if we can't come up with something good. Could be nice to
        extend this function with chars more fitting for your language.
        """
        fromChars = u'ñźńśćżłáéíóúàèìòùâêîôûäëïöüãẽĩõũ'
        toChars = u'nznsczlaeiouaeiouaeiouaeiouaeiou'
        for frm, to in zip(fromChars, toChars):
            text = text.replace(frm, to)
            text = text.replace(frm.upper(), to.upper())
        text = ''.join([i for i in text if 32 <= ord(i) < 128])
        return text

    def getAllText(self):
        return self._allText

    def getDisplayedLine(self):
        return self._displayLine

    def _expandStr(self, s):
        """Expand s, which now should be a line from an on_mouseX field.
        """
        try:
            res = s % {'allText' : self._allText,
                        'displayedLine' : self._displayLine,
                        'allTextEscaped' : self._allText.replace('"', r'\"'),
                        'allTextButFirstLine' :
                            '\n'.join(self._allText.split('\n')[1:]),
                        'allTextButFirstLineEscaped' :
                            '\n'.join(self._allText.replace('"', '\"').
                                    split('\n')[1:])}
        except (KeyError, TypeError, ValueError):
            err(
              "Warning: %s doesn't expand correctly. Ignoring interpolations.\n"
              % s)
            res = s
        return res

    def displayText(self, text):
        """Display text on the entry's line.
        
        Remove or translate characters that aren't supported. Truncate the text
        to fit in the app.
        """
        x, y = getXY(self._line)
        clearLine(y)
        addString(self.translateText(text)[:maxChars], x, y)

    def mouseClicked(self, button):
        """A mouse button has been clicked, do things."""
        if 0 < button < 11:
            self._doMouseAction(button)

class PywmGeneric:
    def __init__(self, config):
        self._entrys = []
        line = 0
        um = UserMethods()
        for c in config:
            # Create our 5 entrys.
            if not c:
                self._entrys.append(None)
                line += 1
                continue
            delay = c.get('update_delay')
            if not delay is None:
                try:
                    delay = self.parseTimeStr(delay)
                except ValueError:
                    err("Malformed update_delay in section %s. "
                        % str(i))
                    err("Ignoring this section.\n")
                    self._entrys.append(None)
                    line += 1
                    continue
            action = c.get('action')
            display = c.get('display')
            if action is None and display is None:
                err(
                  "Warning: No action or display in section %d, ignoring it.\n"
                   % i)
                self._entrys.append(None)
            else:
                scroll = isTrue(c.get('scroll', '1'))
                # Get the mouse actions.
                mouseActions = []
                for i in range(10):
                    but = str(i + 1)
                    opt = 'on_mouse' + but
                    mouseActions.append(c.get(opt))
                self._entrys.append(Entry(line, delay, action,
                        mouseActions, um, display, scroll))
            line += 1
        self._setupMouseRegions()

    def _setupMouseRegions(self):
        for i in range(5):
            x, y = getXY(i)
            if not self._entrys[i] is None:
                wmdocklib.addMouseRegion(i, x + xOffset, y + yOffset,
                    width - 2 * xOffset, y + yOffset + char_height)

    def parseTimeStr(self, timeStr):
        """Take a string on a form like 10h and return the number of seconds.

        Raise ValueError if timeStr is on a bad format.
        """
        multipliers = {'s' : 1, 'm' : 60, 'h' : 3600}
        timeStr = timeStr.strip()
        if timeStr:
            timeLetter = timeStr[-1]
            multiplier = multipliers.get(timeLetter)
            if not multiplier is None:
                timeNum = float(timeStr[:-1].strip())
                numSecs = timeNum * multiplier
                return numSecs
        raise ValueError, 'Invalid literal'

    def _checkForEvents(self):
        event = wmdocklib.getEvent()
        while not event is None:
            if event['type'] == 'destroynotify':
                sys.exit(0)
            elif event['type'] == 'buttonrelease':
                region = wmdocklib.checkMouseRegion(event['x'], event['y'])
                button = event['button']
                if region != -1:
                    if not self._entrys[region] is None:
                        self._entrys[region].mouseClicked(button)
            event = wmdocklib.getEvent()

    def mainLoop(self):
        counter = -1
        while 1:
            counter += 1
            self._checkForEvents()
            if counter % 2 == 0:
                [e.tick1() for e in self._entrys if not e is None]
            if counter % 20 == 0:
                [e.tick2() for e in self._entrys if not e is None]

            if counter == 999999:
                counter = -1
            wmdocklib.redraw()
            time.sleep(0.5)

def parseCommandLine(argv):
    """Parse the commandline. Return a dictionary with options and values."""
    shorts = 'ht:b:r:c:F:'
    longs = ['help', 'text=', 'background=', 'rgbfile=', 'configfile=',
             'font=', 'debug']
    try:
        opts, nonOptArgs = getopt.getopt(argv[1:], shorts, longs)
    except getopt.GetoptError, e:
        err('Error when parsing commandline: ' + str(e) + '\n')
        err(usage)
        sys.exit(2)
    d = {} 
    for o, a in opts:
        if o in ('-h', '--help'):
            sys.stdout.write(usage)
            sys.exit(0)
        if o in ('-t', '--text'):
            d['text'] = a
        if o in ('-b', '--background'):
            d['background'] = a
        if o in ('-F', '--font'):
            d['font'] = a
        if o in ('-r', '--rgbfile'):
            d['rgbfile'] = a
        if o in ('-c', '--configfile'):
            d['configfile'] = a
        if o in ('--debug'):
            d['debug'] = True
    return d

def readConfigFile(fileName):
    """Read the config file.
    
    Return a list with dictionaries with the options and values in sections
    [0]-[4].
    """
    fileName = os.path.expanduser(fileName)
    if not os.access(fileName, os.R_OK):
        err("Can't read the configuration file %s.\n" % fileName)
        # We can't do much without a configuration file
        sys.exit(3)
    cp = ConfigParser.ConfigParser()
    try:
        cp.read(fileName)
    except ConfigParser.Error, e:
        err("Error when reading configuration file:\n%s\n" % str(e))
        sys.exit(3)
    l = [{}, {}, {}, {}, {}]
    for i in range(5):
        strI = str(i)
        if cp.has_section(strI):
            for o in cp.options(strI):
                l[i][o] = cp.get(strI, o, raw=1)
    return l

background = \
[
 ' ...............................................................................................',
 ' .///..___..ooo..___..___.......................................................................',
 ' .///..___..ooo..___..___.......................................................................',
 ' .///..___..ooo..___..___.......................................................................',
 ' .///.._________________________________________________________________________________________',
 ' .///.._________________________________________________________________________________________',
 ' .///.._________________________________________________________________________________________',
 ' .///.._________________________________________________________________________________________',
 ' .///.._________________________________________________________________________________________',
 ' .///.._________________________________________________________________________________________',
 ' .///.._________________________________________________________________________________________',
 ' .///.._________________________________________________________________________________________',
 ' .///..___..___..___..___.......................................................................',
 ' .///..___..___..___..ooo.......................................................................',
 ' .///..___..___..___..ooo.......................................................................',
 ' .///..___..___..___..ooo.......................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
 ' .///...........................................................................................',
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
    clConfig = parseCommandLine(sys.argv)

    palette = {
        '.': '#0000FF',
        'o': '#C7C3C7',
        'O': '#86828E',
        '+': '#EFF3EF',
        '@': '#616161',
        '#': '#9EA29E',
        '$': '#414141',
        }

    palette['o'] = clConfig.get('indicator', '#20b2aa')
    palette['/'] = clConfig.get('graph', '#20b2aa')
    palette['-'] = clConfig.get('graphbg', '#707070')
    palette['_'] = clConfig.get('background', '#FFFFFF')
    palette['%'] = clConfig.get('text', '#20B2AE')

    font = clConfig.get('font', '6x8')

    configFile = clConfig.get('configfile', defaultConfigFile)
    if not configFile.count(os.sep):
        configFile = os.sep.join(sys.argv[0].split(os.sep)[:-1]) + os.sep + configFile
    configFile = os.path.expanduser(configFile)
    config = readConfigFile(configFile)
    try:
        programName = sys.argv[0].split(os.sep)[-1]
    except IndexError:
        programName = ''
    sys.argv[0] = programName

    global char_width, char_height
    char_width, char_height = wmdocklib.initPixmap(patterns=background,
                                                   font_name=font,
                                                   bg='_', fg='%',
                                                   palette=palette)

    wmdocklib.openXwindow(sys.argv, width, height)
    pywmgeneric = PywmGeneric(config)
    pywmgeneric.mainLoop()

if __name__ == '__main__':
    main()
