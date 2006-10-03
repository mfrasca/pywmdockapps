"""pywmhelpers.py

Various helper functions when writing wm dockapps in Python. This module
is way better commented than the pywmgeneral one. This is the one
intented for use in applications. Many functions are just wrappers
around the ones in pywmgeneral but with nicer interfaces and better
documentation.

Copyright (C) 2003 Kristoffer Erlandsson

Licensed under the GNU General Public License


Changes:
2003-06-25 Kristoffer Erlandsson
Updated documentation

2003-06-24 Kristoffer Erlandsson
Some changes to handle the additional event handling in pywmgeneral

2003-06-16 Kristoffer Erlandsson
First workingish version
"""

import os
import re
import ConfigParser

import pywmgeneral

def readConfigFile(fileName, errOut):
    """Read the config file fileName.

    Return a dictionary with the options and values in the DEFAULT
    section. Ignore everything else. The configuration file should not
    get so complicated so that sections are needed. errOut is the
    file-like object to which error messages will be printed.
    """
    if not os.access(fileName, os.R_OK):
        if errOut:
            errOut.write(
                'Configuration file is not readable. Using defaults.\n')
        return {}
    cp = ConfigParser.ConfigParser()
    try:
        cp.read(fileName)
    except ConfigParser.Error, e:
        if errOut:
            errOut.write('Error in configuration file:\n')
            errOut.write(str(e) + '\nUsing defaults.')
        return {}
    defaults = cp.defaults()
    if defaults == {}:
        if errOut:
            errOut.write(
                'Missing or empty DEFAULT section in the config file.\n')
            errOut.write('Using defaults.\n')
    return defaults

def getCenterStartPos(s, letterWidth, areaWidth, offset):
    """Get the x starting position if we want to paint s centred."""
    w = len(s) * letterWidth
    textArea = areaWidth - offset * 2 - 1
    return (textArea - w) / 2

def addChar(ch, x, y, letterWidth, letterHeight, lettersStartX, lettersStartY,
            letters, digitWidth, digitHeight, digitsStartX, digitsStartY,
            digits, xOffset, yOffset, width, height):
    """Paint the character ch at position x, y in the window.
    
    Return the (width, height) of the character painted. Raise
    ValueError if we try to paint a char not in letters or digits
    or if we get out of bounds during painting. digits is really
    just another line of chars, it's unlucky called digits everywhere
    I used it since it contained only digits in the start. However,
    now it contains various special chars too everywhere I use it. But
    the name remains in too many places so I haven't gotten to change
    it.
    """
    chIndex = letters.find(ch.lower())
    if chIndex != -1:
        chX = lettersStartX + chIndex * letterWidth
        chY = lettersStartY
        w = letterWidth
        h = letterHeight
    else:
        chIndex = digits.find(ch)
        if chIndex != -1:
            chX = digitsStartX + chIndex * digitWidth
            chY = digitsStartY
            w = digitWidth
            h = digitHeight
        else:
            raise ValueError, "Unsupported char: '%s'" % ch
    targX = x + xOffset
    targY = y + yOffset
    if targX + w > width - xOffset or targY + h > height - yOffset\
            or targX < 0 or targY < 0:
        raise ValueError, "Out of bounds."
    pywmgeneral.copyXPMArea(chX, chY, w, h, targX, targY)
    return (w, h)

def addString(s, x, y, letterWidth, letterHeight, lettersStartX, lettersStartY,
              letters, digitWidth, digitHeight, digitsStartX, digitsStartY,
              digits, xOffset, yOffset, width, height):
    """Add a string at the given x and y positions.
    
    Call addChar repeatedely, so the same exception rules apply."""
    lastW = 0
    for letter in s:
        w, h = addChar(letter, x + lastW, y, letterWidth, letterHeight,
                       lettersStartX, lettersStartY, letters, digitWidth,
                       digitHeight, digitsStartX, digitsStartY, digits,
                       xOffset, yOffset, width, height)
        lastW += w

def getVertSpacing(numLines, margin, height, letterHeight, yOffset):
    """Return the optimal spacing between a number of lines.
    
    margin is the space we want between the first line and the top."""
    h = height - numLines * letterHeight - yOffset * 2 - margin
    return h / (numLines - 1)


def readXPM(fileName):
    """Read the xpm in filename.

    Return a list of strings containing the xpm. Raise IOError if we run
    into trouble when trying to read the file. This function surely
    doesn't handle all XPMs, but it handles the ones I use, so that'll
    do.
    """
    f = file(fileName, 'r')
    lines = [l.rstrip('\n') for l in f.readlines()]
    s = ''.join(lines)
    res = []
    while 1:
        nextStrStart = s.find('"')
        if nextStrStart != -1:
            nextStrEnd = s.find('"', nextStrStart + 1)
            if nextStrEnd != -1:
                res.append(s[nextStrStart+1:nextStrEnd])
                s = s[nextStrEnd+1:]
                continue
        break
    return res

def setColor(xpm, name, newColor):
    """Find the color with comment name and set this color to newColor.
    
    Change the source code of an XPM represented as a list of strings.
    I'm certain that this will fail on many XPMs too, but it'll do for
    the ones I use. No check is done that the color is valid, this has
    to be done elsewhere.
    """
    colorRE = re.compile(
            r"^(?P<letter>.).*?c (?P<color>#.*?) s (?P<comment>.*)")
    index = 1
    for line in xpm[1:]:
        m = colorRE.match(line)
        if not m is None:
            comment = m.group('comment')
            if comment == name:
                letter = m.group('letter')
                color = newColor
                xpm[index] = '%s\tc %s s %s' % (letter, color, comment)
        index += 1

def setDefaultPixmap(xpm):
    """Set the pixmap of the program. 

    xpm is an XPM represented as a list of strings, possible gotten
    from readXPM(). This is what we use all the time later. The XBM
    mask is created out of the XPM. If I understand correctly how it
    works we use the upper left rectangle as mask. This is the
    simplest way to do it and is the desired behaviour in most cases.
    """
    pywmgeneral.includePixmap(xpm)

def openXwindow(argv, w, h):
    """Open the X window of given width and height.
    
    The XBM mask is here created from the upper left rectangle of the
    XPM using the given width and height."""
    pywmgeneral.openXwindow(len(argv), argv, w, h)

def redraw():
    """Redraw the window."""
    pywmgeneral.redrawWindow()

def redrawXY(x, y):
    """Redraw a given region of the window."""
    pywmgeneral.redrawWindowXY(x, y)

def copyXPMArea(sourceX, sourceY, width, height, targetX, targetY):
    """Copy an area of the global XPM."""
    if width > 0 or height > 0:
        pywmgeneral.copyXPMArea(sourceX, sourceY, width, height,
                                targetX, targetY)

def addMouseRegion(index, left, top, right, bottom):
    """Add a mouse region in the window."""
    pywmgeneral.addMouseRegion(index, left, top, right, bottom)

def checkMouseRegion(x, y):
    """Check if x,y is in any mouse region. Return that region, otherwise -1.
    """
    return pywmgeneral.checkMouseRegion(x, y)

def getEvent():
    """Check for XEvents and return one if found.

    Return None if we find no events. There may be events pending still
    after this function is called. If an event which we handle is found,
    return a dictionary with information about it. All dictionaries
    contain a 'type' field identifying the event. Now existing events
    with dictionary keys are:
    'buttonrelease':
        x, y, button
    'destroynotify':
    """
    return pywmgeneral.checkForEvents()

def getColorCode(colorName, rgbFileName):
    """Convert a color to rgb code usable in an xpm.
    
    We use the file rgbFileName for looking up the colors. Return None
    if we find no match. The rgbFileName should be like the one found in
    /usr/lib/X11R6/rgb.txt on most sytems.
    """
    f = file(rgbFileName, 'r')
    lines = f.readlines()
    f.close()
    for l in lines:
        if l[0] != '!':
            words = l.split()
            if len(words) > 3:
                name = ' '.join(words[3:])
                if colorName.lower() == name.lower():
                    # Found the right color, get it's code
                    try:
                        r = int(words[0])
                        g = int(words[1])
                        b = int(words[2])
                    except ValueError:
                        continue
                    rgbstr = '#' + str(hex(r))[2:].zfill(2) + \
                                   str(hex(g))[2:].zfill(2) + \
                                   str(hex(b))[2:].zfill(2)
                    return rgbstr
    return None

