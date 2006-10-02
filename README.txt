[WHAT] 
pywmdockapps is a small suite of python modules that will help you develop
WindowMaker dockapps in python. pywmgeneral.py, the central module of the
suite, is mostly a wrapper around the functions from the popular
wmgeneral.c, but some new functions are added too.

the suite also contains the Python written module pywmhelpers.py which
contains functions to aid the development of wm dockapps.  This module
contains python functions that wrap up the functions which the extension
module provides.  They ease up argument passing and give nicer return
values.  Some additional functions, like help for handling a simple
configuration file is also available.  This module is better documented than
the pywmgeneral.  It is adviced to only use pywmhelpers and not touch the
pywmgeneral module directly at all. For information about how to use the
module, see the documentation in pywmhelpers.py. It is also possible to
import it in the interactive interpreter and issue 'help(pywmhelpers)'.

a small set of samples are provided.  all of them make use of the module
pywmgeneral.

[INSTALLATION]
python ./setup install

[CONTACT]
Anything related to this piece of software can be e-mailed to me, Mario
Frasca <mfrasca@interia.pl>.

