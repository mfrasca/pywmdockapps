"""pywmhelpers.py

Various helper functions when writing wm dockapps in Python. This module
is way better commented than the pywmgeneral one. This is the one
intented for use in applications. Many functions are just wrappers
around the ones in pywmgeneral but with nicer interfaces and better
documentation.

Copyright (C) 2003 Kristoffer Erlandsson

Licensed under the GNU General Public License


Changes:

2006-10-10 Mario Frasca
redesigned xpm initialization

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

def getCenterStartPos(s, areaWidth, offset):
    """Get the x starting position if we want to paint s centred."""
    w = len(s) * char_width
    textArea = areaWidth - offset * 2 - 1
    return (textArea - w) / 2

def addChar(ch, x, y, xOffset, yOffset, width, height):
    """Paint the character ch at position x, y in the window.

    Return the (width, height) of the character painted.  (will be useful if
    we implement proportional char sets)
    
    the library only supports lower ascii: 32-127.  any other will cause a
    ValueError exception.

    if the character being painted falls partly out of the boundary, it will
    be clipped without causing an exception.  this works even if the
    character starts out of the boundary.
    """

    if not (32 <= ord(ch) <= 127):
        raise ValueError, "Unsupported Char: '%s'(%d)" % (ch, ord(ch))
    stringsize = 128 - (128 % char_width)
    pos = (ord(ch)-32) * char_width
    chY, chX = (pos / stringsize) * char_height + 64, pos % stringsize
    targX = x + xOffset
    targY = y + yOffset
    pywmgeneral.copyXPMArea(chX, chY, char_width, char_height, targX, targY)
    return (char_width, char_height)

def addString(s, x, y, xOffset, yOffset, width, height):
    """Add a string at the given x and y positions.
    
    Call addChar repeatedely, so the same exception rules apply."""
    lastW = 0
    for letter in s:
        w, h = addChar(letter, x + lastW, y, 
                       xOffset, yOffset, width, height)
        lastW += w

def getVertSpacing(numLines, margin, height, yOffset):
    """Return the optimal spacing between a number of lines.
    
    margin is the space we want between the first line and the top."""
    h = height - (numLines * char_height + 1) - yOffset * 2 - margin
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

def initPixmap(xpm_background=None,
               font_name='6x8',
               bg='0', fg='7',
               width=64, height=64,
               palette=None):
    """builds and sets the pixmap of the program. 

    a wmdockapp has a 128x112 pixmap

    the 64x64 upper left area is the work area in which we put what we want
    to be displayed.

    the 64x64 upper right area contains the pattern for blanking the area.
    this is initialized using the xpm_background parameter.  xpm_background
    must contain a list of 64 strings of length 64.

    the remaining lower area defines the character set.  this is initialized
    using the corresponding named character set.  a file with this name must
    be found somewhere in the path.

    xpm_background and the font must share the same palette.  the font must
    be black/white.

    The XBM mask is created out of the XPM.
    """

    if xpm_background is None:
        #xpm_background = ['0'*width]*4 + ['0000'+bg*(width-8)+'0000']*(height-8) + ['0'*width]*4
        xpm_background = [bg*width]*height
    if palette is None:
        palette = {
            0: ('#000000','transparent'),
            1: ('#000080','blue'),
            2: ('#008080','cyan'),
            3: ('#008000','green'),
            4: ('#808000','yellow'),
            5: ('#800000','red'),
            6: ('#800080','purple'),
            7: ('#c0c0c0','light_gray'),
            8: ('#000000','black'),
            9: ('#0000ff','light_blue'),
            10: ('#00ffff','light_cyan'),
            11: ('#00ff00','light_green'),
            12: ('#ffff00','light_yellow'),
            13: ('#ff0000','light_red'),
            14: ('#ff00ff','light_purple'),
            15: ('#ffffff','white'),
            }

    global char_width, char_height, char_map
    global tile_width, tile_height

    char_width = char_defs[font_name]['width']
    char_height = char_defs[font_name]['height']
    char_map = char_defs[font_name]['map']

    tile_width = width
    tile_height = height
    
    xpm = [
        '128 112 %d 1' % len(palette),
        ] + [
        '%x\tc %s s %s' % (k, v[0], v[-1])
        for k,v in palette.items()
        ] + [
        '0'*64 + item for item in xpm_background[:3]
        ] + [
        '000'+bg*(64-8)+'00000' + item for item in xpm_background[3:-4]
        ] + [
        '0'*64 + item for item in xpm_background[-4:]
        ] + [
        line.replace('%', fg).replace(' ', bg)
        for line in char_map
        ]
    
    pywmgeneral.includePixmap(xpm)
    return char_width, char_height

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

char_defs = {
    '5x7': {
    'width': 5,
    'height': 7,
    'map': [
"       %   % %           %           %    %   %                                   %    %   %%  %%%%   %  %%%%  %%  %%%%  %%     ",
"       %   % %  % %  %%% %  %  %     %   %     %   % %   %                    %  % %  %%  %  %    %  %%  %    %       % %  %    ",
"       %   % % %%%%%% %    %  % %    %   %     %    %    %                   %   % %   %     %  %%  % %  %%%  %%%    %   %%     ",
"       %        % %  %%%  %    %         %     %   %%% %%%%%     %%%%       %    % %   %    %     % %%%%    % %  %   %  %  %    ",
"               %%%%%  % %%  % % %        %     %    %    %    %%       %%  %     % %   %   %   %  %   %  %  % %  %  %   %  %    ",
"       %        % %  %%%    %  % %        %   %    % %   %    %        %%         %   %%% %%%%  %%    %   %%   %%   %    %%     ",
"                                                             %                                                                  ",
" %%                             %   %%   %%  %%%   %%  %%%  %%%% %%%%  %%  %  %  %%%    % %  % %    %  % %  %  %%  %%%   %%     ",
"%  %  %%   %%     %       %    % % %  % %  % %  % %  % %  % %    %    %  % %  %   %     % % %  %    %%%% %% % %  % %  % %  %    ",
"%  %  %%   %%    %  %%%%   %     % % %% %  % %%%  %    %  % %%%  %%%  %    %%%%   %     % %%   %    %%%% %% % %  % %  % %  %    ",
" %%%            %           %   %  % %% %%%% %  % %    %  % %    %    % %% %  %   %     % %%   %    %  % % %% %  % %%%  %  %    ",
"   %  %%   %%    %  %%%%   %       %    %  % %  % %  % %  % %    %    %  % %  %   %  %  % % %  %    %  % % %% %  % %    %% %    ",
" %%   %%   %      %       %     %   %%  %  % %%%   %%  %%%  %%%% %     %%% %  %  %%%  %%  %  % %%%% %  % %  %  %%  %     %%     ",
"          %                                                                                                                %    ",
"%%%   %%   %%% %  % %  % %  % %  %  % % %%%%  %%%       %%%   %        %        %            %        %       %      %     %    ",
"%  % %  %   %  %  % %  % %  % %  %  % %    %  %   %       %  % %        %       %            %       % %      %                 ",
"%  %  %     %  %  % %  % %  %  %%   % %   %   %    %      %                 %%% %%%   %%   %%%  %%   %    %%% %%%   %%     %    ",
"%%%    %    %  %  % %  % %%%%  %%    %   %    %     %     %                %  % %  % %    %  % % %% %%%  %  % %  %   %     %    ",
"% %  %  %   %  %  %  %%  %%%% %  %   %  %     %      %    %                % %% %  % %    %  % %%    %    %%  %  %   %     %    ",
"%  %  %%    %   %%   %%  %  % %  %   %  %%%%  %%%       %%%      %%%%       % % %%%   %%   %%%  %%   %   %    %  %  %%%  % %    ",
"                                                                                                          %%%             %     ",
"%     %%                                      %                                    %   %   %    % %                             ",
"%      %                                      %                                   %    %    %  % %  % % %                       ",
"% %    %  % %  %%%   %%  %%%   %%% %%%   %%% %%%  %  %  % % %  % %  % %  % %%%%  %%    %    %%                                  ",
"%%     %  %%%% %  % %  % %  % %  % %  % %%    %   %  %  % % %  %  %%  %  %   %    %    %    %       %   %                       ",
"% %    %  %  % %  % %  % %  % %  % %      %%  %   %  %  % % %%%%  %%   % %  %     %    %    %                                   ",
"%  %  %%% %  % %  %  %%  %%%   %%% %    %%%    %%  %%%   %  %%%% %  %   %  %%%%    %   %   %        % % %                       ",
"                         %       %                                     %                                                        ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
    ]
    },
    '6x8': {
    'width': 6,
    'height': 8,
    'map': [
"        %    %  %  % %    %   %   %  %%       %    %   %                                         %%%    %    %%%   %%%     %    ",
"        %    %  %  % %   %%%% %   % %  %     %    %     %   %   %   %                           %   %  %%   %   % %   %   %%    ",
"        %    %  % %%%%% %        %   %%     %    %       %   % %    %                         % %  %%   %       %     %  % %    ",
"        %          % %   %%%    %    %           %       %  %%%%% %%%%%       %%%%%          %  % % %   %     %%    %%  %  %    ",
"                  %%%%%     %  %    % % %        %       %   % %    %                       %   %%  %   %    %        % %%%%%   ",
"                   % %  %%%%  %   % %  %          %     %   %   %   %     %           %%   %    %   %   %   %     %   %    %    ",
"        %          % %    %   %   %  %% %          %   %                  %           %%  %      %%%   %%%  %%%%%  %%%     %    ",
"                                                                         %                                                      ",
"%%%%%  %%%  %%%%%  %%%   %%%                 %%       %%     %%%   %%%    %   %%%%   %%%  %%%   %%%%% %%%%%  %%%  %   %  %%%    ",
"%     %   % %   % %   % %   %               %           %   %   % %   %  % %  %   % %   % %  %  %     %     %   % %   %   %     ",
"%%%%  %        %  %   % %   %   %     %    %    %%%%%    %      % % %%% %   % %   % %     %   % %     %     %     %   %   %     ",
"    % %%%%    %    %%%   %%%%             %               %    %  % % % %%%%% %%%%  %     %   % %%%%  %%%   %  %% %%%%%   %     ",
"    % %   %   %   %   %     %              %    %%%%%    %    %   % %%% %   % %   % %     %   % %     %     %   % %   %   %     ",
"%   % %   %   %   %   % %   %   %     %     %           %         %     %   % %   % %   % %  %  %     %     %   % %   %   %     ",
" %%%   %%%    %    %%%   %%%          %      %%       %%      %    %%%  %   % %%%%   %%%  %%%   %%%%% %      %%%  %   %  %%%    ",
"                                     %                                                                                          ",
"  %%% %   % %     %   % %   %  %%%  %%%%   %%%  %%%%   %%%  %%%%% %   % %   % %   % %   % %   % %%%%%  %%%         %%%    %     ",
"   %  %  %  %     %% %% %   % %   % %   % %   % %   % %   %   %   %   % %   % %   % %   % %   %     %  %             %   % %    ",
"   %  % %   %     % % % %%  % %   % %   % %   % %   % %       %   %   % %   % %   %  % %  %   %    %   %    %        %  %   %   ",
"   %  %%    %     %   % % % % %   % %%%%  %   % %%%%   %%%    %   %   % %   % %   %   %    % %    %    %     %       %          ",
"   %  % %   %     %   % %  %% %   % %     %   % % %       %   %   %   % %   % % % %  % %    %    %     %      %      %          ",
"%  %  %  %  %     %   % %   % %   % %      %%%  %  %  %   %   %   %   %  % %  %% %% %   %   %   %      %       %     %          ",
" %%   %   % %%%%% %   % %   %  %%%  %        %% %   %  %%%    %    %%%    %   %   % %   %   %   %%%%%  %%%      %  %%%          ",
"                                                                                                                                ",
"      %           %               %          %%       %       %       %        %%                                               ",
"       %          %               %         %         %                 %       %                                               ",
"        %    %%%  %      %%%%     %  %%%    %    %%%% %      %%      %% %       %   %% %  %%%%   %%%  %%%%   %%%% %%%%   %%%%   ",
"                % %%%%  %      %%%% %   %  %%%% %   % %%%%    %       % % %%    %   % % % %   % %   % %   % %   % %   % %       ",
"             %%%% %   % %     %   % %%%%%   %   %   % %   %   %       % %%      %   % % % %   % %   % %   % %   % %      %%%    ",
"            %   % %   % %     %   % %       %    %%%% %   %   %       % % %     %   % % % %   % %   % %%%%   %%%% %         %   ",
"             %%%% %%%%   %%%%  %%%%  %%%    %       % %   %  %%%      % %  %%  %%%  % % % %   %  %%%  %         % %     %%%%    ",
"%%%%%                                           %%%%               %%%                                %         %               ",
"                                            %%%   %   %%%                                                                       ",
"  %                                        %      %      %                                                                      ",
"%%%%% %   % %   % %   % %   % %   % %%%%%  %      %      %                                                                      ",
"  %   %   % %   % % % %  % %  %   %    %  %       %       %  %% %                                                               ",
"  %   %   % %   % % % %   %   %   %   %    %      %      %  % %%                                                                ",
"  %   %   %  % %  % % %  % %   %%%%  %     %      %      %                                                                      ",
"   %%  %%%%   %    % %  %   %    %  %%%%%   %%%   %   %%%                                                                       ",
"                              %%%                                                                                               ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
"                                                                                                                                ",
    ]
    },
    '8x8': {
    'width': 8,
    'height': 8,
    'map': [
"           %%    %%  %%  %%  %%    %%    %%   %   %%%%       %%     %%    %%                                                    ",
"           %%    %%  %%  %%  %%   %%%%%  %%  %%  %%  %%     %%     %%      %%    %%  %%    %%                                 %%",
"           %%    %%  %% %%%%%%%% %%         %%    %%%%     %%     %%        %%    %%%%     %%                                %% ",
"           %%            %%  %%   %%%%     %%     %%%             %%        %%  %%%%%%%% %%%%%%          %%%%%%             %%  ",
"                        %%%%%%%%     %%   %%     %%  %%%          %%        %%    %%%%     %%                              %%   ",
"                         %%  %%  %%%%%   %%  %%  %%  %%            %%      %%    %%  %%    %%      %%              %%     %%    ",
"           %%            %%  %%    %%    %   %%   %%%%%%            %%    %%                       %%              %%    %%     ",
"                                                                                                  %%                            ",
"  %%%%     %%     %%%%    %%%%       %%  %%%%%%   %%%%   %%%%%%   %%%%    %%%%                      %%%          %%%      %%%%  ",
" %%  %%    %%    %%  %%  %%  %%     %%%  %%      %%  %%  %%  %%  %%  %%  %%  %%                    %%              %%    %%  %% ",
" %% %%%   %%%        %%      %%    %%%%  %%%%%   %%         %%   %%  %%  %%  %%    %%      %%     %%     %%%%%%     %%       %% ",
" %%% %%    %%       %%     %%%   %%  %%      %%  %%%%%     %%     %%%%    %%%%%                  %%                  %%     %%  ",
" %%  %%    %%     %%         %%  %%%%%%%     %%  %%  %%    %%    %%  %%      %%                   %%     %%%%%%     %%     %%   ",
" %%  %%    %%    %%      %%  %%      %%  %%  %%  %%  %%    %%    %%  %%  %%  %%    %%      %%      %%              %%           ",
"  %%%%   %%%%%%  %%%%%%   %%%%       %%   %%%%    %%%%     %%     %%%%    %%%%             %%       %%%          %%%       %%   ",
"                                                                                          %%                                    ",
"  %%%%     %%    %%%%%    %%%%   %%%%    %%%%%%  %%%%%%   %%%%   %%  %%   %%%%     %%%%  %%  %%  %%      %%   %% %%  %%   %%%%  ",
" %%  %%   %%%%   %%  %%  %%  %%  %% %%   %%      %%      %%  %%  %%  %%    %%       %%   %% %%   %%      %%% %%% %%% %%  %%  %% ",
" %% %%%  %%  %%  %%  %%  %%      %%  %%  %%      %%      %%      %%  %%    %%       %%   %%%%    %%      %%%%%%% %%%%%%  %%  %% ",
" %% %%%  %%%%%%  %%%%%   %%      %%  %%  %%%%    %%%%    %% %%%  %%%%%%    %%       %%   %%%     %%      %% % %% %%%%%%  %%  %% ",
" %%      %%  %%  %%  %%  %%      %%  %%  %%      %%      %%  %%  %%  %%    %%       %%   %%%%    %%      %%   %% %% %%%  %%  %% ",
" %%   %  %%  %%  %%  %%  %%  %%  %% %%   %%      %%      %%  %%  %%  %%    %%    %% %%   %% %%   %%      %%   %% %%  %%  %%  %% ",
"  %%%%   %%  %%  %%%%%    %%%%   %%%%    %%%%%%  %%       %%%%   %%  %%   %%%%    %%%    %%  %%  %%%%%%  %%   %% %%  %%   %%%%  ",
"                                                                                                                                ",
" %%%%%    %%%%   %%%%%    %%%%   %%%%%%  %%  %%  %%  %%  %%   %% %%  %%  %%  %%  %%%%%%    %%%            %%%                   ",
" %%  %%  %%  %%  %%  %%  %%  %%    %%    %%  %%  %%  %%  %%   %% %%  %%  %%  %%      %%   %%       %%       %%                  ",
" %%  %%  %%  %%  %%  %%  %%        %%    %%  %%  %%  %%  %%   %%  %%%%   %%  %%     %%    %%       %%       %%                  ",
" %%%%%   %%  %%  %%%%%    %%%%     %%    %%  %%  %%  %%  %% % %%   %%     %%%%     %%    %%        %%        %%  %%% %%         ",
" %%      %%  %%  %%%%        %%    %%    %%  %%  %%  %%  %%%%%%%  %%%%     %%     %%      %%       %%       %%  %% %%%          ",
" %%       %%%%   %% %%   %%  %%    %%    %%  %%   %%%%   %%% %%% %%  %%    %%    %%       %%       %%       %%                  ",
" %%         %%%  %%  %%   %%%%     %%     %%%%     %%    %%   %% %%  %%    %%    %%%%%%    %%%     %%     %%%                   ",
"                                                                                                                                ",
"   %%                                                                                                                           ",
"    %%           %%                  %%             %%%          %%        %%        %%  %%       %%%                           ",
"     %%   %%%%   %%       %%%%       %%   %%%%     %%     %%%%%  %%                      %%        %%    %%  %%  %%%%%    %%%%  ",
"             %%  %%%%%   %%       %%%%%  %%  %%   %%%%%  %%  %%  %%%%%    %%%        %%  %% %%     %%    %%%%%%% %%  %%  %%  %% ",
"          %%%%%  %%  %%  %%      %%  %%  %%%%%%    %%    %%  %%  %%  %%    %%        %%  %%%%      %%    %%%%%%% %%  %%  %%  %% ",
"         %%  %%  %%  %%  %%      %%  %%  %%        %%     %%%%%  %%  %%    %%        %%  %% %%     %%    %% % %% %%  %%  %%  %% ",
"          %%%%%  %%%%%    %%%%    %%%%%   %%%%     %%        %%  %%  %%   %%%%       %%  %%  %%   %%%%   %%   %% %%  %%   %%%%  ",
"                                                         %%%%%                    %%%%                                          ",
"                                                                                          %%%%            %%%%                  ",
"                                   %%                                                     %%     %%         %%     %%           ",
" %%%%%    %%%%%  %%%%%    %%%%%  %%%%%%  %%  %%  %%  %%  %%   %% %%  %%  %%  %%  %%%%%%   %%      %%        %%    %%%%          ",
" %%  %%  %%  %%  %%  %%  %%        %%    %%  %%  %%  %%  %% % %%  %%%%   %%  %%     %%    %%       %%       %%   %%  %%         ",
" %%  %%  %%  %%  %%       %%%%     %%    %%  %%  %%  %%  %%%%%%%   %%    %%  %%    %%     %%        %%      %%                  ",
" %%%%%    %%%%%  %%          %%    %%    %%  %%   %%%%    %%%%%   %%%%    %%%%%   %%      %%         %%     %%                  ",
" %%          %%  %%      %%%%%      %%%   %%%%%    %%     %% %%  %%  %%     %%   %%%%%%   %%%%        %%  %%%%          %%%%%%%%",
" %%          %%                                                          %%%%                                                   ",
    ]
    },
    }
 
