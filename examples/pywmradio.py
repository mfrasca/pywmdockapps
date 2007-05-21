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

    def reset(self):
        self._cacheLevel = -50
        self.child = None
        self._paused = None
        self._buffering = 0
        self._flash = 0
        self._muting = 0
        self.showCacheLevel()

    def __init__(self, *args, **kwargs):
        wmoo.Application.__init__(self, *args, **kwargs)
        self.radioList = []
        self.currentRadio = 0
        self._count = 0
        self._expectdying = 0

        self.reset()

        self._buffered = ''
        import re
        self._feedback = re.compile(r'.+A:.*?% ([0-9\.]+)%')

        import fileinput, os
        configfile = os.sep.join([os.environ['HOME'], '.pyradiorc'])

        import codecs
        f = codecs.open(configfile, 'r', 'utf-8')
        t = f.read()
        f.close()
        for i in t.split(u'\n'):
            radiodef = i.split('\t')
            radioname = radiodef[0].lower()
            if len(radiodef) != 3 or i[0] == '#':
                continue
            if radioname == '':
                globals()[radiodef[1]] = radiodef[2]
                pass
            else:
                self.radioList.append( (radioname+' '*24, radiodef[1], radiodef[2]) )
        

    def handler(self, num, frame):
        if self._expectdying:
            print self._expectdying
            self._expectdying -= 1
        else:
            self.reset()
            self._flash = 4
            self._colour = 1

    def startPlayer(self):
        import os, subprocess, signal
        commandline = [mplayer,
                       '-cache', self.radioList[self.currentRadio][2],
                       self.radioList[self.currentRadio][1]
                       ]
        self.child = subprocess.Popen(commandline,
                                      stdin =subprocess.PIPE,
                                      stdout=subprocess.PIPE,
                                      stderr=devnull)
        signal.signal(signal.SIGCHLD, self.handler)
        self._flash = 0
        self._paused = False
        self._buffered = ''
        self._buffering = 1
        self._cacheLevel = 0
        import fcntl
	flags = fcntl.fcntl(self.child.stdout, fcntl.F_GETFL)
    	fcntl.fcntl(self.child.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
	flags = fcntl.fcntl(self.child.stdin, fcntl.F_GETFL)
    	fcntl.fcntl(self.child.stdin, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def stopPlayer(self):
        if self.child:
            print self._expectdying
            self.child.stdin.write('q')
            self._expectdying += 1
            self.child = None

    def muteStream(self, event):
        if self.child and self._buffering == 0:
            self.child.stdin.write('m')
            self.putPattern(9*self._muting, 0, 9, 11, 30, 29)
            self._muting = 1 - self._muting

    def printevent(self, event):
        print event

    def previousRadio(self, event):
        if self.currentRadio == 0: self.currentRadio = len(self.radioList)
        self.currentRadio -= 1
        self.putString(0, 10, self.radioList[self.currentRadio][0])
        if self.child:
            self.stopPlayer()
            self.startPlayer()

    def nextRadio(self, event):
        self.currentRadio += 1
        if self.currentRadio == len(self.radioList): self.currentRadio = 0
        self.putString(0, 10, self.radioList[self.currentRadio][0])
        if self.child:
            self.stopPlayer()
            self.startPlayer()

    def playStream(self, event):
        self.startPlayer()

    def stopStream(self, event):
        self.stopPlayer()
        self.reset()

    def pauseStream(self, event):
        if self.child and not self._buffering:
            self.child.stdin.write(' ')
            self._paused = not self._paused
            if self._paused:
                self._colour = 1
            return True
        return False

    def showCacheLevel(self):
        if self._buffering:
            self._cacheLevel += 1
            if self._cacheLevel >= 25:
                self._cacheLevel -= 25
            for i in range(-1, 25):
                if abs(i - self._cacheLevel) <= 1:
                    self.putPattern(54, self._buffering, 3, 1, 52, 54-i)
                else:
                    self.putPattern(54, 0, 3, 1, 52, 54-i)
        else:
            if self._paused or self._flash:
                colour = self._colour = 3 - self._colour
                self._flash = max(0, self._flash - 1)
            else:
                colour = 2
            for i in range(-1, 25):
                if (i*4 < self._cacheLevel) or self._flash:
                    self.putPattern(54, colour, 3, 1, 52, 54-i)
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
        if self.child or self._flash:
            self.showCacheLevel()

palette = {
    '-': "#000000",
    ".": "#868682",
    "X": "#AEAEAA",
    "o": "#F7F7F3",
    "r": "#F73020",
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
    "                                                   XXXX.        ",
    "      XXXXXXXX.   XXXXXXXX.   XXXXXXXX.            X---         ",
    "      X--------   X--------   X--------            X---         ",
    "      X--------   X--------   X-----o--            X---         ",
    "      X--o--o--   X--o--o--   X----oo--            X---         ",
    "      X--o-oo--   X--oo-o--   X-ooooo--            X---         ",
    "      X--oooo--   X--oooo--   X-ooooo--            X---         ",
    "      X--o-oo--   X--oo-o--   X----oo--            X---         ",
    "      X--o--o--   X--o--o--   X-----o--            X---         ",
    "      X--------   X--------   X--------            X---         ",
    "      X--------   X--------   X--------            X---         ",
    "      .--------   .--------   .--------            X---         ",
    "                                                   X---         ",
    "                                                   X---         ",
    "                                                  X.---..       ",
    "      XXXXXXXX.   XXXXXXXX.   XXXXXXXX.            X---         ",
    "      X--------   X--------   X--------            X---         ",
    "      X--------   X--------   X--------            X---         ",
    "      X--o-----   X-oo-oo--   X-ooooo--            X---         ",
    "      X--oo----   X-oo-oo--   X-ooooo--            X---         ",
    "      X--ooo---   X-oo-oo--   X-ooooo--            X---         ",
    "      X--oo----   X-oo-oo--   X-ooooo--            X---         ",
    "      X--o-----   X-oo-oo--   X-ooooo--            X---         ",
    "      X--------   X--------   X--------            X---         ",
    "      X--------   X--------   X--------            X---         ",
    "      .--------   .--------   .--------            X---         ",
    "                                                   X---         ",
    "                                                   .---         ",
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
    "X-----rr-X-----o--X-----o--X--------X--------X--------iii       ",
    "X----rr--X----oo--X----oo--X-oo-oo--X--o-----X--r-----          ",
    "X-oorro--X-ooooo--X-ooooo--X-oo-oo--X--oo----X--rr----          ",
    "X-ooroo--X-ooooo--X-ooooo--X-oo-oo--X--ooo---X--rrr---          ",
    "X--rroo--X----oo--X----oo--X-oo-oo--X--oo----X--rr----          ",
    "X-rr--o--X-----o--X-----o--X-oo-oo--X--o-----X--r-----          ",
    "X- ------X--------X--------X--------X--------X--------          ",
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
    app.addCallback(app.muteStream,    'buttonrelease', area=(30,29,39,38))

    app.addCallback(app.playStream, 'buttonrelease', area=( 6,43,15,52))
    app.addCallback(app.pauseStream, 'buttonrelease', area=(18,43,27,52))
    app.addCallback(app.stopStream, 'buttonrelease', area=(30,43,39,52))
    
    app.run()

if __name__ == '__main__':
    main()
