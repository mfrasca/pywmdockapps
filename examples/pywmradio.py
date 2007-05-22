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
        if 'pause' in self._buttons:
            self.setButtonPattern('pause', (11, 10))
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
                self.radioList.append( (radioname, radiodef[1], radiodef[2]) )
        

    def handler(self, num, frame):
        if self._expectdying:
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
            self.child.stdin.write('q')
            self._expectdying += 1
            self.child = None

    def printevent(self, event):
        print event

    def previousRadio(self, event):
        #print 'in previousRadio'
        if self.currentRadio == 0: self.currentRadio = len(self.radioList)
        self.currentRadio -= 1
        self.setLabelText('name', self.radioList[self.currentRadio][0])
        if self.child:
            self.stopPlayer()
            self.startPlayer()

    def nextRadio(self, event):
        #print 'in nextRadio'
        self.currentRadio += 1
        if self.currentRadio == len(self.radioList): self.currentRadio = 0
        self.setLabelText('name', self.radioList[self.currentRadio][0])
        if self.child:
            self.stopPlayer()
            self.startPlayer()

    def playStream(self, event):
        #print 'in playStream'
        self.startPlayer()

    def stopStream(self, event):
        #print 'in stopStream'
        self.stopPlayer()
        self.reset()

    def pauseStream(self, event):
        #print 'in pauseStream'
        if self.child and not self._buffering:
            self.child.stdin.write(' ')
            self._paused = not self._paused
            if self._paused:
                self._colour = 1
            return True
        return False

    def muteStream(self, event):
        #print 'in muteStream'
        if self.child and self._buffering == 0:
            self.child.stdin.write('m')
            self.setButtonPattern('mute', (33-11*self._muting, 0))
            self._muting = 1 - self._muting

    def showCacheLevel(self):
        if self._buffering:
            self._cacheLevel += 1
            if self._cacheLevel >= 25:
                self._cacheLevel -= 25
            for i in range(-1, 25):
                if abs(i - self._cacheLevel) <= 1:
                    self.putPattern(54, self._buffering, 5, 1, 54, 58-i)
                else:
                    self.putPattern(54, 0, 5, 1, 54, 58-i)
        else:
            if self._flash:
                colour = self._colour = 3 - self._colour
                self._flash = max(0, self._flash - 1)
            else:
                colour = 2
            for i in range(-1, 25):
                if (i*4 < self._cacheLevel) or self._flash:
                    self.putPattern(54, colour, 5, 1, 54, 58-i)
                else:
                    self.putPattern(54, 0, 5, 1, 54, 58-i)

    def update(self):
        wmoo.Application.update(self)
        self._count += 1
        if self._count <= 3:
            return
        if self._paused:
            colour = self._colour = 4 - self._colour
            self.setButtonPattern('pause', (self._colour*11, 10))
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
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  X----------------------------------------------------------X  ",
    "  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "      .........      .........      .........        XXXXXX.    ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "                                                     X-----     ",
    "                                                     X-----     ",
    "                                                     X-----     ",
    "                                                     X-----     ",
    "                                                    X.-----..   ",
    "                                                     X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "      .........      .........      .........        X-----     ",
    "                                                     X-----     ",
    "                                                     .-----     ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    "                                                                ",
    ]

patterns = [
    "XXXXXXXXX  XXXXXXXXX  XXXXXXXXX  XXXXXXXXX            -----     ",
    "X--------  X--------  X--------  X--------            rrrrr     ",
    "X-o------  X-----o--  X-----o--  X----rr--            iiiii     ",
    "X-o--oo--  X-oo--o--  X----oo--  X----rr--                      ",
    "X-o-ooo--  X-ooo-o--  X-ooXoo--  X-oorro--                      ",
    "X-ooooo--  X-ooooo--  X-ooXoo--  X-ooroo--                      ",
    "X-o-ooo--  X-ooo-o--  X-ooXoo--  X-orroo--                      ",
    "X-o--oo--  X-oo--o--  X----oo--  X-rr-oo--                      ",
    "X-o------  X-----o--  X-----o--  X-rr--o--                      ",
    "X--------  X--------  X--------  X--------                      ",
    "XXXXXXXXX  XXXXXXXXX  XXXXXXXXX  XXXXXXXXX                      ",
    "X--------  X--------  X--------  X--------                      ",
    "X--------  X--------  X--------  X--------                      ",
    "X-oo-----  X-oo-oo--  X-ooooo--  X-rr-rr--                      ",
    "X-oooo---  X-oo-oo--  X-ooooo--  X-rr-rr--                      ",
    "X-ooooo--  X-oo-oo--  X-ooooo--  X-rr-rr--                      ",
    "X-oooo---  X-oo-oo--  X-ooooo--  X-rr-rr--                      ",
    "X-oo-----  X-oo-oo--  X-ooooo--  X-rr-rr--                      ",
    "X--------  X--------  X--------  X--------                      ",
    "X--------  X--------  X--------  X--------                      ",
    ]


def main():

    global char_width, char_height, maxCharsPerLine, antialiased
    app = Application(font_name='5x8',
                      margin = 3,
                      bg=0, fg=2, palette = palette,
                      background = background,
                      patterns = patterns)
    # maxCharsPerLine = (width-2*xOffset) / char width
    app.addLabel('name',   (5, 16), (54, 10), app.radioList[app.currentRadio][0])

    app.addButton('prev',  ( 6,31), (9, 10), app.previousRadio, pattern=(0,0))
    app.addButton('next',  (21,31), (9, 10), app.nextRadio, pattern=(11,0))
    app.addButton('mute',  (36,31), (9, 10), app.muteStream, pattern=(22,0))

    app.addButton('play',  ( 6,47), (9, 10), app.playStream, pattern=(0,10))
    app.addButton('pause', (21,47), (9, 10), app.pauseStream, pattern=(11,10))
    app.addButton('stop',  (36,47), (9, 10), app.stopStream, pattern=(22,10))

    app.addCallback(app.previousRadio, 'keypress', key='k')
    app.addCallback(app.nextRadio, 'keypress', key='j')
    app.addCallback(app.muteStream, 'keypress', key='m')
    app.addCallback(app.playStream, 'keypress', key='p')
    app.addCallback(app.pauseStream, 'keypress', key=' ')
    app.addCallback(app.stopStream, 'keypress', key='q')
    
    app.run()

if __name__ == '__main__':
    main()
