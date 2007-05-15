#!/usr/bin/env python

"""pywmoonop.py

object oriented WindowMaker dockapp doing nothing

Copyright (C) 2007 Mario Frasca

Licensed under the GNU General Public License.
"""

from wmdocklib import wmoo
thisapp = wmoo.Application()

if __name__ == '__main__':
    thisapp.run()
