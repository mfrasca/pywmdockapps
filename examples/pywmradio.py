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
        self.cache = '320'
        self.radioList = []
        self.currentRadio = 0
        self._count = 0
        self._cacheLevel = -50
        self._buffering = 0

        self._buffered = ''
        import re
        self._feedback = re.compile(r'.+ \(.+?\) .+? .+? .+? .+? ([0-9\.]+)%')

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
                                      stdin =devnull,
                                      stdout=subprocess.PIPE,
                                      stderr=devnull)
        self._buffered = ''
        self._buffering = 1
        self._cacheLevel = 0
        import fcntl
	flags = fcntl.fcntl(self.child.stdout, fcntl.F_GETFL)
    	fcntl.fcntl(self.child.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)

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
        self._cacheLevel = -50
        self.showCacheLevel()

    def showCacheLevel(self):
        if self._buffering:
            self._cacheLevel += 2
            if self._cacheLevel >= 25:
                self._cacheLevel -= 25
            for i in range(-1, 25):
                if i == self._cacheLevel:
                    self.putPattern(54, self._buffering, 3, 1, 52, 54-i)
                else:
                    self.putPattern(54, 0, 3, 1, 52, 54-i)
        else:
            for i in range(-1, 25):
                if i*4 < self._cacheLevel:
                    self.putPattern(54, 2, 3, 1, 52, 54-i)
                else:
                    self.putPattern(54, 0, 3, 1, 52, 54-i)

    def update(self):
        self._count += 1
        if self._count <= 3:
            return
        self._count = 0
        if self.child:
            import select
            [i, o, e] = select.select([self.child.stdout], [], [], 0)
            if i:
                line = self.child.stdout.read(102400)
                self._buffered += line
                npos = self._buffered.rfind('\n')+1
                rpos = self._buffered.rfind('\r')+1
                if npos != 0:
                    self._buffered = self._buffered[npos:]
                if rpos != 0:
                    if self._buffered.startswith('Cache fill:'):
                        self._buffering = 2
                    else:
                        match = self._feedback.match(self._buffered[rpos-90:rpos])
                        if match:
                            self._buffering = 0
                            self._cacheLevel = float(match.group(1))

                    self._buffered = self._buffered[rpos:]
            self.showCacheLevel()

palette = {
    '-': "#000000",
    ".": "#868682",
    "X": "#AEAEAA",
    "o": "#F7F7F3",
    "r": "#F7A0A0",
    "i": "#00F700",
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
    "      XXXXXXXX.   XXXXXXXX.   XXXXXXXX.          .. --- ..      ",#100
    "      X--------   X--------   X--------             ---         ",#96
    "      X--------   X--------   X--------             ---         ",#92
    "      X--o--o--   X--o--o--   X-o.-.o--             ---         ",#88
    "      X--o-oo--   X--oo-o--   X-.o.o.--             ---         ",#84
    "      X--oooo--   X--oooo--   X--.o. --             ---         ",#80
    "      X--o-oo--   X--oo-o--   X-.o.o.--             ---         ",#76
    "      X--o--o--   X--o--o--   X-o.-.o--             ---         ",#72
    "      X--------   X--------   X--------             ---         ",#68
    "      X--------   X--------   X--------             ---         ",#64
    "      .--------   .--------   .--------             ---         ",#60
    "                                                    ---         ",#56
    "                                                    ---         ",#52
    "                                                 .. --- ..      ",#48
    "      XXXXXXXX.   XXXXXXXX.   XXXXXXXX.             ---         ",#44
    "      X--------   X--------   X--------             ---         ",#40
    "      X--------   X--------   X--------             ---         ",#36
    "      X--o-----   X-oo-oo--   X-ooooo--             ---         ",#32
    "      X--oo----   X-oo-oo--   X-ooooo--             ---         ",#28
    "      X--ooo---   X-oo-oo--   X-ooooo--             ---         ",#24
    "      X--oo----   X-oo-oo--   X-ooooo--             ---         ",#20
    "      X--o-----   X-oo-oo--   X-ooooo--             ---         ",#16
    "      X--------   X--------   X--------             ---         ",#12
    "      X--------   X--------   X--------             ---         ",#08
    "      .--------   .--------   .--------             ---         ",#04
    "                                                    ---         ",#00
    "                                                 .. --- ..      ",
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
    "XXXXXXXX.XXXXXXXX.XXXXXXXX.XXXXXXXX.XXXXXXXX.XXXXXXXX.---       ",
    "X--------X--------X--------X--------X--------X--------rrr       ",
    "X--------X--------X--------X--------X--------X--------iii       ",
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
 
    app.addCallback(app.previousRadio, 'buttonrelease', area=( 6,29,15,38))
    app.addCallback(app.nextRadio,     'buttonrelease', area=(18,29,27,38))
    app.addCallback(app.quitProgram,   'buttonrelease', area=(30,29,39,38), key=1)

    app.addCallback(app.playStream, 'buttonrelease', area=( 6,43,15,52))
    app.addCallback(app.stopStream, 'buttonrelease', area=(18,43,27,52))
    app.addCallback(app.stopStream, 'buttonrelease', area=(30,43,39,52))
    
    app.run()

if __name__ == '__main__':
    main()
