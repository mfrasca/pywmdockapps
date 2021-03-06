#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Set these so they match your system.
XLibDir = '/usr/X11R6/lib'
XIncludes = '/usr/X11R6/include'

from distutils.core import setup, Extension

module1 = Extension('wmdocklib.pywmgeneral',
                    libraries = ['Xpm', 'Xext', 'X11'],
                    library_dirs = [XLibDir],
                    include_dirs = [XIncludes],
                    sources = ['wmdocklib/pywmgeneral.c'])

setup(name="pywmdockapps",
      version = "$Revision$"[11:-2],

      description='''
         read the whole story at http://pywmdockapps.sourceforge.net/''',
      
      author="Kristoffer Erlandsson & al.",
      author_email="mfrasca@zonnet.nl",
      url="http://pywmdockapps.sourceforge.net",
      license="(L)GPL",
      packages=['wmdocklib',
                ],
      scripts=['examples/pywmdatetime.py',
               'examples/pywmhdmon.py',
               'examples/pywmseti.py',
               'examples/pywmsysmon.py',
               'examples/pywmphoto.py',
               'examples/pywmwet.py',
               'examples/pywmradio.py',
               'examples/pywmgeneric.py'],
      package_data={'wmdocklib': ['*.xpm']},
      ext_modules = [module1])
