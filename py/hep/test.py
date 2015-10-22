#-----------------------------------------------------------------------
#
# module hep.test
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Regression testing support."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import sys

#-----------------------------------------------------------------------
# exceptions
#-----------------------------------------------------------------------

class TestFailure(Exception):
    pass



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def assert_(expression):
    if not expression:
        raise TestFailure, "assertion failed"


def compare(value, expected, precision=None):
    if type(value) in (list, tuple) and type(expected) in (list, tuple):
        if len(value) != len(expected):
            result = False
        else:
            try:
                result = reduce(
                    lambda r1, r2: r1 and r2,
                    map(lambda (v, e): compare(v, e, precision),
                        zip(value, expected)),
                    True)
            except TestFailure:
                result = False

    elif precision is not None:
        result = (abs(value - expected) <= precision)

    else:
        result = (value == expected)

    if result:
        return True
    else:
        raise TestFailure, \
              "expected %s; got %s" % (repr(expected), repr(value))


def compareSequence(value, expected, ordered=True):
    value = list(value)
    expected = list(expected)
    if not ordered:
        value.sort()
        expected.sort()
    return compare(value, expected)


