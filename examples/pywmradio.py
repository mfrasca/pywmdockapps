#!/usr/bin/env python

"""pywmnop.py

WindowMaker dockapp doing nothing

Copyright (C) 2006 Mario Frasca

Licensed under the GNU General Public License.
"""

import sys, time
from wmdocklib import wmoo

debug = 0

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
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
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
    app = wmoo.Application(font_name='5x8',
                           margin = 3,
                           bg=0, fg=2, palette=palette,
                           background=patterns,
                           debug=debug)
    # maxCharsPerLine = (width-2*xOffset) / char width

    app.addCallback(printevent)
 
    app.addCallback(previousRadio, 'buttonrelease', area=(14,29,23,38))
    app.addCallback(nextRadio,     'buttonrelease', area=(26,29,35,38))
    app.addCallback(quitProgram,   'buttonrelease', area=(38,29,47,38), key=1)

    app.addCallback(playStream, 'buttonrelease', area=(14,43,23,52))
    app.addCallback(stopStream, 'buttonrelease', area=(26,43,35,52))
    app.addCallback(stopStream, 'buttonrelease', area=(38,43,47,52))
    
    app.run()

if __name__ == '__main__':
    main()
