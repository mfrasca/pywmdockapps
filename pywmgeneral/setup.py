#! /usr/bin/env python

from distutils.core import setup, Extension


# Set these so they match your system.
XLibDir = '/usr/X11R6/lib'
XIncludes = '/usr/X11R6/include'


module1 = Extension('pywmgeneral',
                    libraries = ['Xpm', 'Xext', 'X11'],
                    library_dirs = [XLibDir],
                    include_dirs = [XIncludes],
                    sources = ['pywmgeneral.c'])

setup(name = 'pywmgeneral',
      py_modules = ['pywmhelpers'],
      version = '0.1',
      author = 'Mario Frasca',
      author_email = 'mfrasca@interia.pl',
      description = 'Python module for making WindowMaker dockapps.',
      url = 'http://pywmdockapps.sourceforge.net',
      license = 'GPL',
      ext_modules = [module1])

