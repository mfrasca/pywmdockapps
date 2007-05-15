#!/usr/bin/env python

"""pywmnop.py

WindowMaker dockapp doing nothing

Copyright (C) 2006 Mario Frasca

Licensed under the GNU General Public License.
"""

import sys, time
from wmdocklib import wmoo
devnull = file('/dev/null')

class Application(wmoo.Application):

    def __init__(self, *args, **kwargs):
        wmoo.Application.__init__(self, *args, **kwargs)
        self.child = None
        self.cache = '64'
        self.radioList = []
        self.currentRadio = 0
        self._blink = 0

        import fileinput, os
        configfile = os.sep.join([os.environ['HOME'], '.pyradiorc'])

        for i in fileinput.input(configfile):
            i = i.split('\n')[0]
            radiodef = i.split('\t')
            radioname = radiodef[0].lower()
            if len(radiodef) == 1:
                continue
            if radioname == '':
                globals()[radiodef[1]] = radiodef[2]
                pass
            else:
                self.radioList.append( (radioname+' '*24, radiodef[1]) )

    def startPlayer(self):
        import os, subprocess
        commandline = [mplayer,
                       '-cache', self.cache,
                       self.radioList[self.currentRadio][1]
                       ]
        self.child = subprocess.Popen(commandline,
                                      stdout=devnull,
                                      stderr=devnull)

    def stopPlayer(self):
        if self.child:
            import os, subprocess, signal
            os.kill(self.child.pid, signal.SIGKILL)
            self.child = None
            return True
        return False

    def quitProgram(self, event):
        self.stopPlayer()
        sys.exit(0)

    def printevent(self, event):
        print event

    def previousRadio(self, event):
        if self.currentRadio == 0: self.currentRadio = len(self.radioList)
        self.currentRadio -= 1
        self.putString(0, 10, self.radioList[self.currentRadio][0])
        if self.stopPlayer(): 
            self.startPlayer()

    def nextRadio(self, event):
        self.currentRadio += 1
        if self.currentRadio == len(self.radioList): self.currentRadio = 0
        self.putString(0, 10, self.radioList[self.currentRadio][0])
        if self.stopPlayer(): 
            self.startPlayer()

    def playStream(self, event):
        self.startPlayer()

    def stopStream(self, event):
        self.stopPlayer()
        self.putPattern(9, 0, 9, 11, 38, 43)

    def blink(self):
        self._blink += 1
        if self._blink == 10:
            self.putPattern(0, 0, 9, 11, 38, 43)
        elif self._blink == 20:
            self._blink = 0
            self.putPattern(9, 0, 9, 11, 38, 43)
        pass

    def update(self):
        if self.child:
            self.blink()

palette = {
    '-': "#000000",
    ".": "#868682",
    "X": "#AEAEAA",
    "o": "#F7F7F3",
    "r": "#F70000",
    }

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
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
    "----------------------------------------------------------------",
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

patterns = [
    "XXXXXXXX.XXXXXXXX.XXXXXXXX.XXXXXXXX.XXXXXXXX.XXXXXXXX.          ",
    "X--------X--------X--------X--------X--------X--------          ",
    "X--------X--------X--------X--------X--------X--------          ",
    "X-rrrrr--X-ooooo--X-rr-rr--X-oo-oo--X--o-----X--r-----          ",
    "X-rrrrr--X-ooooo--X-rr-rr--X-oo-oo--X--oo----X--rr----          ",
    "X-rrrrr--X-ooooo--X-rr-rr--X-oo-oo--X--ooo---X--rrr---          ",
    "X-rrrrr--X-ooooo--X-rr-rr--X-oo-oo--X--oo----X--rr----          ",
    "X-rrrrr--X-ooooo--X-rr-rr--X-oo-oo--X--o-----X--r-----          ",
    "X--------X--------X--------X--------X--------X--------          ",
    "X--------X--------X--------X--------X--------X--------          ",
    ".--------.--------.--------.--------.--------.--------          ",
    ]


def main():

    global char_width, char_height, maxCharsPerLine, antialiased
    app = Application(font_name='5x8',
                      margin = 3,
                      bg=0, fg=2, palette = palette,
                      background = background,
                      patterns = patterns)
    # maxCharsPerLine = (width-2*xOffset) / char width
    app.putString(0, 10, app.radioList[app.currentRadio][0])

    # app.addCallback(printevent)
 
    app.addCallback(app.previousRadio, 'buttonrelease', area=(14,29,23,38))
    app.addCallback(app.nextRadio,     'buttonrelease', area=(26,29,35,38))
    app.addCallback(app.quitProgram,   'buttonrelease', area=(38,29,47,38), key=1)

    app.addCallback(app.playStream, 'buttonrelease', area=(14,43,23,52))
    app.addCallback(app.stopStream, 'buttonrelease', area=(26,43,35,52))
    app.addCallback(app.stopStream, 'buttonrelease', area=(38,43,47,52))
    
    app.run()

if __name__ == '__main__':
    main()
