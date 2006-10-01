#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Set these so they match your system.
XLibDir = '/usr/X11R6/lib'
XIncludes = '/usr/X11R6/include'

from distutils.core import setup, Extension

module1 = Extension('pywmgeneral',
                    libraries = ['Xpm', 'Xext', 'X11'],
                    library_dirs = [XLibDir],
                    include_dirs = [XIncludes],
                    sources = ['pywmgeneral/pywmgeneral.c'])

setup(name="pywmdockapps",
      version = "$Revision$"[11:-2],

      description='''
         read the whole story at http://pywmdockapps.sourceforge.net/''',
      
      author="Kristoffer Erlandsson & al.",
      author_email="mfrasca@zonnet.nl",
      url="http://ibo.sourceforge.net",
      license="(L)GPL",
      py_modules=['pywmdatetime.pywmdatetime',
                  'pywmgeneral.pywmhelpers',
                  'pywmgeneric.pywmgeneric',
                  'pywmhdmon.pywmhdmon',
                  'pywmseti.pywmseti',
                  'pywmsysmon.pywmsysmon',
                  ],
      ext_modules = [module1])
