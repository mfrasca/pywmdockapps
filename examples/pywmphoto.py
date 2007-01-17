#!/usr/bin/env python

"""pywmphoto.py

WindowMaker dockapp that displays a static xpm

Copyright (C) 2006 Mario Frasca

Licensed under the GNU General Public License.


Changes:
2006-10-27 Mario Frasca
First workingish version
"""
usage = """pywmphoto.py [options]
Available options are:
-h, --help                      print this help
-f, --file <file>               set the xpm name
--debug                         shows the pixmap
"""

import sys, os, time
import getopt

import wmdocklib

def parseCommandLine(argv):
    """Parse the commandline. Return a dictionary with options and values."""
    shorts = 'hf:'
    longs = ['help', 'file=', 'debug',
             ]
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
        if o in ('-f', '--file'):
            d['file'] = a
        if o in ('--debug'):
            d['debug'] = True
    return d

def checkForEvents():
    event = wmdocklib.getEvent()
    while not event is None:
        if event['type'] == 'destroynotify':
            sys.exit(0)
        event = wmdocklib.getEvent()

def mainLoop():
    while 1:
        checkForEvents()
        wmdocklib.redraw()
        time.sleep(0.5)

def main():
    clConfig = parseCommandLine(sys.argv)

    # openXwindow sets the window title to the program name. If we get the
    # program name with a path, split it so we only name the window with the
    # filename.
    try:
        programName = sys.argv[0].split(os.sep)[-1]
    except IndexError:  # Should only happen when using the interpreter.
        programName = ''
    sys.argv[0] = programName

    xpmName = clConfig.get('file')

    palette, patterns = wmdocklib.readXPM(xpmName)

    debug = clConfig.get('debug')
    
    global char_width, char_height, maxCharsPerLine, antialiased
    wmdocklib.initPixmap(palette=palette,
                         patterns=patterns,
                         margin=3,
                         debug=debug)

    wmdocklib.openXwindow(sys.argv, 64, 64)
    wmdocklib.copyXPMArea(0, 64, 58, 58, 3, 3)

    mainLoop()

if __name__ == '__main__':
    main()

