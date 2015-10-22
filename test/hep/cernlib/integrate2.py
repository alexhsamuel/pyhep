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

compare(integrate("(x + y) ** 2", ("x", 0, 1), ("y", 0, 1)),
        7 / 6, precision=1e-6)

compare(integrate("r", ("r", 0, 2), ("y", 0, 2 * pi)),
        4 * pi, precision=1e-6)

compare(integrate("r", ("r", 0, 2), ("y", 0, 2 * pi)),
        4 * pi, precision=1e-6)

compare(integrate("cos(x + y) * sin(x - y)", ("x", -1, 1), ("y", 0, 1)),
        -sin(1) ** 2, precision=1e-6)

compare(integrate("sin(sqrt(x**2 + 2 * y**2)) / (1 + sqrt(2 * x**2 + y**2))",
                  ("x", -5, 5), ("y", -5, 5), accuracy=1e-4),
        0.086, precision=0.01)


def f(x, y):
    return sin(sqrt(x**2 + 2 * y**2)) / (1 + sqrt(2 * x**2 + y**2))

compare(integrate(f, ("x", -5, 5), ("y", -5, 5), accuracy=1e-5),
        0.086, precision=0.001)

