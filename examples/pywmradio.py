#!/usr/bin/env python

"""pywmnop.py

WindowMaker dockapp doing nothing

Copyright (C) 2006 Mario Frasca

Licensed under the GNU General Public License.
"""

import sys, time
import wmdocklib

debug = 0

class Application:
    def __init__(self, *args, **kwargs):
        """initializes the object

        _events is a list of tuples (type, key, area, callback)
          'type' <- ['buttonpress', 'buttonrelease', 'keypress'],
          'callback': the function to which the event should be passed.
          'key': the utf-8 character or the mouse button number,
          'area': if the pointer is here, the event is considered,
        
        """
        self._events = []

        wmdocklib.initPixmap(*args, **kwargs)
        wmdocklib.openXwindow(sys.argv, 64, 64)
        pass

    def addHandler(self, callback, type=None, key=None, area=None ):
        if area is not None and len(area) is not 4:
            area = None
        self._events.append( (type, key, area, callback,) )
        pass
    
    def run(self):
        while 1:
            event = wmdocklib.getEvent()
            while not event is None:
                if event['type'] == 'destroynotify':
                    sys.exit(0)

                for evtype, key, area, callback in self._events:
                    if evtype is not None and evtype != event['type']: continue
                    if key is not None and key != event['key']: continue
                    if area is not None:
                        if not area[0] <= event['x'] <= area[2]: continue
                        if not area[1] <= event['y'] <= area[3]: continue

                    callback(event)
                    
                event = wmdocklib.getEvent()
            wmdocklib.redraw()
            time.sleep(0.5)
            
    pass

def printevent(event):
    print event

def previousRadio(event):
    print 'previousRadio', event

def nextRadio(event):
    print 'nextRadio', event

def quitProgram(event):
    print 'quitProgram', event
    sys.exit(0)

def playStream(event):
    print 'playStream', event

def stopStream(event):
    print 'stopStream', event

palette = {
    '-': "#000000",
    ".": "#868682",
    "X": "#AEAEAA",
    "o": "#F7F7F3",
    }

patterns = [
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
    "        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX           ",
    "        X-------------------------------------------X           ",
    "        X-------------------------------------------X           ",
    "        X-------------------------------------------X           ",
    "        X-------------------------------------------X           ",
    "        X-------------------------------------------X           ",
    "        X-------------------------------------------X           ",
    "        X-------------------------------------------X           ",
    "        XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX           ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "              XXXXXXXX.   XXXXXXXX.   XXXXXXXX.                 ",
    "              X--------   X--------   X--------                 ",
    "              X--------   X--------   X--------                 ",
    "              X--o--o--   X--o--o--   X-o.-.o--                 ",
    "              X--o-oo--   X--oo-o--   X-.o.o.--                 ",
    "              X--oooo--   X--oooo--   X--.o. --                 ",
    "              X--o-oo--   X--oo-o--   X-.o.o.--                 ",
    "              X--o--o--   X--o--o--   X-o.-.o--                 ",
    "              X--------   X--------   X--------                 ",
    "              X--------   X--------   X--------                 ",
    "              .--------   .--------   .--------                 ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "              XXXXXXXX.   XXXXXXXX.   XXXXXXXX.                 ",
    "              X--------   X--------   X--------                 ",
    "              X--------   X--------   X--------                 ",
    "              X--o-----   X-oo-oo--   X-ooooo--                 ",
    "              X--oo----   X-oo-oo--   X-ooooo--                 ",
    "              X--ooo---   X-oo-oo--   X-ooooo--                 ",
    "              X--oo----   X-oo-oo--   X-ooooo--                 ",
    "              X--o-----   X-oo-oo--   X-ooooo--                 ",
    "              X--------   X--------   X--------                 ",
    "              X--------   X--------   X--------                 ",
    "              .--------   .--------   .--------                 ",
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
    ]



def main():

    global char_width, char_height, maxCharsPerLine, antialiased
    app = Application(font_name='5x8',
                      margin = 3,
                      bg=0, fg=2, palette=palette,
                      background=patterns,
                      debug=debug)
    # maxCharsPerLine = (width-2*xOffset) / char width
 
    app.addHandler(previousRadio, 'buttonrelease', area=(14,29,23,38))
    app.addHandler(nextRadio,     'buttonrelease', area=(26,29,35,38))
    app.addHandler(quitProgram,   'buttonrelease', area=(38,29,47,38))

    app.addHandler(playStream, 'buttonrelease', area=(14,43,23,52))
    app.addHandler(stopStream, 'buttonrelease', area=(26,43,35,52))
    app.addHandler(stopStream, 'buttonrelease', area=(38,43,47,52))
    
    app.run()

if __name__ == '__main__':
    main()
