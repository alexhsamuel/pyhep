#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.cernlib import integrate
from   hep.test import compare
from   math import *

#-----------------------------------------------------------------------
# tests
#-----------------------------------------------------------------------

compare(integrate("x ** 2", ("x", 0, 1)),
        1 / 3, precision=1e-6)

compare(integrate("gaussian(0, 1, x)", ("x", -1, 1)),
        0.682689, precision=1e-6)

compare(integrate("cos(x)", ("x", -100, 100)),
        2 * sin(100), precision=1e-6)

compare(integrate("sqrt(1 - x ** 2)", ("x", 0, 1)),
        pi / 4, precision=1e-6)


def foo(x):
    return sin(x) / x


compare(integrate(foo, ("x", -100, 100)),
        pi, precision=0.1)


def bar(x):
    return sin(x) ** 2


compare(integrate(bar, ("x", -pi / 2, 0)),
        pi / 4, precision=1e-6)


