#!/usr/bin/env python

"""pywmnop.py

WindowMaker dockapp doing nothing

Copyright (C) 2006 Mario Frasca

Licensed under the GNU General Public License.
"""

import sys, time
import wmdocklib

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
    wmdocklib.initPixmap()
    wmdocklib.openXwindow(sys.argv, 64, 64)

    mainLoop()

if __name__ == '__main__':
    main()
