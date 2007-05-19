#!/usr/bin/env python

"""pywmphoto.py

WindowMaker dockapp that displays a static xpm

Copyright (C) 2006-2007 Mario Frasca

Licensed under the GNU General Public License.


Changes:
2006-10-27 Mario Frasca
First workingish version

2007-05-19 Mario Frasca
more compact form, based on wmdocklib.wmoo and optparse.
"""

from wmdocklib import wmoo

def main():

    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="read background from file", metavar="FILE")
    parser.add_option("-d", "--debug", dest="debug", 
                      action="store_true", default=False,
                      help="print the pixmap")

    (options, args) = parser.parse_args()

    app = wmoo.Application(background = options.filename,
                           margin = 3,
                           debug = options.debug)

    app.run()

if __name__ == '__main__':
    main()
