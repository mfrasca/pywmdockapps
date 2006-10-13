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
defaultRGBFileList = [
    '/etc/X11/rgb.txt',
    '/usr/lib/X11/rgb.txt',
    '/usr/share/X11/rgb.txt',
    '/usr/X11R6/lib/X11/rgb.txt',
    '/usr/lib/X11/rgb.txt',
    ]

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

def initPixmap(xpm_background=None,
               font_name='6x8',
               bg=0, fg=7,
               width=64, height=64,
               margin=3,
               palette=None):
    """builds and sets the pixmap of the program. 

    a wmdockapp has a 128x112 pixmap

    the (width)x(height) upper left area is the work area in which we put
    what we want to be displayed.

    the remaining upper right area contains patterns that can be used for
    blanking/resetting portions of the displayed area.

    the remaining lower area defines the character set.  this is initialized
    using the corresponding named character set.  a file with this name must
    be found somewhere in the path.  the colours used in the xpm file for
    the charset must be ' ' and '%'.  they will be changed here to bg and
    fg.

    palette is a dictionary
    1: of integers <- [0..15] to colours.
    2: of single chars to colours.

    a default palette is provided, and can be silently overwritten with the
    one passed as parameter.

    The XBM mask is created out of the XPM.
    """

    # a palette is a dictionary from one single letter to an hexadecimal
    # colour.  per default we offer a 16 colours palette including what I
    # consider the basic colours:
    basic_colours = ['black', 'blue3', 'green3', 'cyan3',
                     'red3', 'magenta3', 'yellow3', 'gray',
                     'gray41', 'blue1', 'green1', 'cyan1',
                     'red1', 'magenta1', 'yellow1', 'white']

    alter_palette, palette = palette, {}
    for name, index in zip(basic_colours, range(16)):
        palette['%x'%index] = getColorCode(name)

    # palette = {'0':..., '1':..., ..., 'f':...}
    # named_colours = {'black':'0', 'green': '1', ..., 'white':'f'}
    
    if alter_palette is not None:
        # alter_palette contains 0..15/chr -> 'name'/'#hex'
        # interpret that as chr -> '#hex'
        for k,v in alter_palette.items():
            if isinstance(k, int):
                k = '%x' % k
            k = k[0]
            if not v.startswith('#'):
                v = getColorCode(v)
            palette[k] = v

    if isinstance(bg, str) and len(bg)>1:
        bg = named_colours.get(bg, 0)
    if isinstance(fg, str) and len(fg)>1:
        fg = named_colours.get(fg, 7)
    if isinstance(bg, int):
        bg = '%x' % bg
    if isinstance(fg, int):
        fg = '%x' % fg

    if xpm_background is None:
        #xpm_background = ['0'*width]*4 + ['0000'+bg*(width-8)+'0000']*(height-8) + ['0'*width]*4
        xpm_background = [bg*width]*height

    global char_width, char_height, char_map
    global tile_width, tile_height

    char_width = char_defs[font_name]['width']
    char_height = char_defs[font_name]['height']
    char_map = char_defs[font_name]['map']

    tile_width = width
    tile_height = height
    
    xpm = [
        '128 112 %d 1' % (1+len(palette)),
        ] + [
        ' \tc black'
        ] + [
        '%s\tc %s' % (k,v)
        for k,v in palette.items()
        ] + [
        ' '*width + item[:128-width] for item in xpm_background[:margin]
        ] + [
        ' '*margin+bg*(width-margin-margin-2)+' '*(margin+2) + item[:128-width] for item in xpm_background[margin:-margin-1]
        ] + [
        ' '*width + item[:128-width] for item in xpm_background[-margin-1:]
        ] + [
        line.replace('%', fg).replace(' ', bg)
        for line in char_map
        ]
    if 0:
        print '/* XPM */\nstatic char *_x_[] = {'
        for item in xpm:
            print '"%s",' % item
        print '};'
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

def getColorCode(colorName, rgbFileName=None):
    """Convert a color to rgb code usable in an xpm.
    
    We use the file rgbFileName for looking up the colors. Return None
    if we find no match. The rgbFileName should be like the one found in
    /usr/lib/X11R6/rgb.txt on most sytems.
    """

    if rgbFileName is None:
        for fn in defaultRGBFileList:
            if os.access(fn, os.R_OK):
                rgbFileName = fn
                break
    if rgbFileName is None:
        raise ValueError('cannot find rgb file')

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
                    rgbstr = '#%02x%02x%02x' % (r,g,b)
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
 
