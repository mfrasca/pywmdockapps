#!/usr/bin/env python
"""pywmwet.py
WindowMaker dockapp that tracks a Wolf:ET server and displays following info:
->Map Name
-># of Allies
-># of Axis
-># of Spectators (if server using 'P' cvar

Copyright (C) 2007 Nathan Lundquist
Licensed under the GNU General Public License.
Changes:
2007-01-16 Nate Lundquist
First attempt
"""

import sys, getopt, os
import socket
import wmdocklib
import time, datetime

DEFAULT_PORT = 27960
DEFAULT_INTERVAL = 60 #seconds
WIDTH = 64
HEIGHT = 64
XOFFSET = 4
YOFFSET = 4
MARGIN = 1
LINE_SPACING = 4

usage = '''
pywmwet.py [options]
Available options are:
-h, --help                          Print this help text
-s, --server <server address>       Server to track
-p, --port <port>                   Server port [default: 27960]
-u, --update-interval <seconds>     Delay between updates [default: 60 sec]
'''


def parse_command_line(argv):
    shorts = 'hs:p:u:'
    longs = ['help', 'server=', 'port=', 'update-interval=']

    try:
        opts, nonOptArgs = getopt.getopt(argv[1:], shorts, longs)
    except getopt.GetoptError, e:
        print 'Error parsing commandline: ' + str(e)
        print usage
        sys.exit(2)
    d = {}
    for o, a in opts:
        if o in ('-h', '--help'):
            print usage
            sys.exit(0)
        if o in ('-s', '--server'):
            d['server'] = a
        if o in ('-p', '--port'):
            d['port'] = int(a)
        else:
            d['port'] = DEFAULT_PORT
        if o in ('-u', '--update-interval'):
            d['update-interval'] = int(a)
        else:
            d['update-interval'] = DEFAULT_INTERVAL
    return d

def query_server(server, port):
    try:
        query = '\xFF\xFF\xFF\xFF\x02getstatus\x0a\x00'
        addr = (server, port)
        sockobj = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sockobj.connect(addr)
        sockobj.send(query)
        data = sockobj.recv(4096)
        data = data[18:]
        sockobj.shutdown(0)
        sockobj.close()
        #print 'query success'
        #print data
        return data
    except socket.error:
        #print 'query failure'
        return False

def get_map(data):
    data = data.split('\\')
    i = data.index('mapname')
    return ' '.join(data[i+1].split('_')).title()

def get_num_allies(data):
    data = data.split('\\')
    try: #servers using older cvar
        i = data.index('Players_Allies')
        allies = data[i+1]
        return len(allies.split())
    except ValueError: #possibly newer server using 'P' cvar
        try:
            #3 - Spectator, 2 - Allies, 1 - Axis
            i = data.index('P')
            slots = data[i+1]
            allies = 0
            for slot in slots:
                if slot == '2':
                    allies += 1
            return allies
        except ValueError: #no players connected?
            return 0

def get_num_axis(data):
    data = data.split('\\')
    try: #server using old cvar
        i = data.index('Players_Axis')
        axis = data[i+1]
        return len(axis.split())
    except ValueError: #possible new cvar
        try:
            #3 - Spectator, 2 - Allies, 1 - Axis
            i = data.index('P')
            slots = data[i+1]
            axis = 0
            for slot in slots:
                if slot == '1':
                    axis += 1
            return axis
        except ValueError: #no players
            return 0

def get_num_spectators(data):
    #This will only work with servers that use the newer 'P' cvar
    data = data.split('\\')
    try:
        #3 - Spectator, 2 - Allies, 1 - Axis
        i = data.index('P')
        slots = data[i+1]
        spec = 0
        for slot in slots:
            if slot == '3':
                spec += 1
        return spec
    except ValueError: #check if old cvars in use
        if 'Players_Axis' in data or 'Players_Allies' in data:
            #old cvars in use, so we don't know how many spectators there are
            return '??'
        else: #no players
            return 0

def get_players(data):
    players = []
    player_data = data.strip().split('\n')[1:]
    for player_line in player_data:
        player = strip_name(player_line.split('"')[1])
        players.append(player)
    return players

def scroll_players(players):
    pass

def strip_name(name):
    stripped_name = ''
    skip_next = False
    for x in range(len(name)):
        if name[x] != '^' and skip_next != True:
            stripped_name += name[x]
        elif name[x] == '^':
            skip_next = True
            continue
        skip_next = False
    return stripped_name
            

def scroll_text(s, y, speed):
    #not sure if this is the best way to do this...
    cen_pos = get_center(s)
    end_pos = (cen_pos *2) - (MARGIN * 2) - 64
    for x in range(WIDTH, end_pos, -1):
        add_string(s, x, y)
        wmdocklib.redraw()
        time.sleep(speed)

def get_center(s):
    return wmdocklib.getCenterStartPos(s, WIDTH, XOFFSET)

def add_string(s, x, y):
    return wmdocklib.addString(s, x, y, XOFFSET, YOFFSET, WIDTH, HEIGHT)

def get_spacing(line_no):
    if line_no == 1:
        return MARGIN
    else:
        # 1 + (4) + 4
        return MARGIN + (char_height * (line_no - 1)) + LINE_SPACING * (line_no - 1)

def check_for_events():
    event = wmdocklib.getEvent()
    while not event is None:
        if event['type'] == 'destroynotify':
            sys.exit(0)
        event = wmdocklib.getEvent()

def main_loop(server, port, update_interval):
    dif = datetime.timedelta(seconds=update_interval)
    last_updated = datetime.datetime.now()
    just_started = True
    while 1:
        check_for_events()
        now = datetime.datetime.now()
        if now > (last_updated + dif) or just_started == True:
            data = query_server(server, port)
            if not data:
                add_string('Server', get_center('Server'), get_spacing(1))
                add_string('Not', get_center('Not'), get_spacing(2))
                add_string('Found', get_center('Found'), get_spacing(3))
                just_started = False
            else:
                mapname = get_map(data)
                num_allies = get_num_allies(data)
                num_axis = get_num_axis(data)
                num_specs = get_num_spectators(data)
                last_updated = datetime.datetime.now()
                just_started = False
            
        if data:
            add_string(('Allies:%s' % str(num_allies)), MARGIN, get_spacing(2) + 5)
            add_string(('Axis:%s' % str(num_axis)), MARGIN, get_spacing(3) + 5)
            add_string(('Spec:%s' % str(num_specs)), MARGIN, get_spacing(4) + 5)
            
            #mapname last in case it has to scroll
            if get_center(mapname) < MARGIN:
                scroll_text(mapname, get_spacing(1), 0.04)
            else:
                add_string(mapname, get_center(mapname), get_spacing(1))

        wmdocklib.redraw()
        time.sleep(0.1)

def main():
    clConfig = parse_command_line(sys.argv)
    try:
        program_name = sys.argv[0].split(os.sep)[-1]
    except IndexError: 
        program_name = ''

    if not clConfig.has_key('server'):
        print '\nYou must supply a server using the -s/--server option.\n'
        print 'Use -h flag to see more options.'
        sys.exit(2)

    global char_width, char_height
    char_width, char_height = wmdocklib.initPixmap(font_name='5x7', fg=3)
    wmdocklib.openXwindow(sys.argv, 64, 64)

    try:
        main_loop(clConfig['server'], clConfig['port'], clConfig['update-interval'])
    except KeyboardInterrupt:
        print 'Goodbye.'
        sys.exit(0)

if __name__ == '__main__':
    main()

 	  	 
