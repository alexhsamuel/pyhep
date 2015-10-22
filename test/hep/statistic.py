#--------------------------------------------------*- coding: Latin1 -*-
# imports
#-----------------------------------------------------------------------

from   hep.num import Statistic
from   hep.test import compare
from   math import sqrt

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

s = Statistic(9)
compare(float(s), 9)
compare(s.uncertainty, 3)

s = Statistic(10.5, 2.3)
compare(float(s), 10.5)
compare(s.uncertainty, 2.3)

s = Statistic("10")
compare(float(s), 10)
compare(s.uncertainty, sqrt(10))

s = Statistic("10", 3)
compare(float(s), 10)
compare(s.uncertainty, 3)

s = Statistic("10 +- 2")
compare(float(s), 10)
compare(s.uncertainty, 2)

s = Statistic("10 +- 2", 3)
compare(float(s), 10)
compare(s.uncertainty, 3)

s = Statistic("10 ± 2")
compare(float(s), 10)
compare(s.uncertainty, 2)

s = Statistic(s)
compare(float(s), 10)
compare(s.uncertainty, 2)

s = Statistic(s, 3)
compare(float(s), 10)
compare(s.uncertainty, 3)

