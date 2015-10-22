#-----------------------------------------------------------------------
#
# module hep.bool
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Implementation of bool for older Python versions.

This module provides 'bool', 'True', and 'False' similar to those found
in recent versions of Python.  These symbols are defined only when
Python doesn't include its own built-in."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.ext import BoolArray

#-----------------------------------------------------------------------

if not hasattr(__builtins__, "bool"):

    False = 0

    True = 1


    class bool(object):

        def __new__(class_, value):
            if value:
                return True
            else:
                return False



