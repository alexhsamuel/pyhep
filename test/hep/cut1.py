#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.cuts
from   hep.num import in_range
from   hep.test import assert_
from   numarray import array, Float32
from   random import normalvariate, random
import os

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

sig_values = array(shape=(1000, 4), type=Float32)
for i in range(sig_values.shape[0]):
    sig_values[i, 0] = normalvariate(0, 1)
    sig_values[i, 1] = normalvariate(0, 1)
    sig_values[i, 2] = normalvariate(0, 1)
    sig_values[i, 3] = normalvariate(0, 1)

bkg_values = array(shape=(5000, 4), type=Float32)
for i in range(bkg_values.shape[0]):
    bkg_values[i, 0] = normalvariate( 0, 2)
    bkg_values[i, 1] = normalvariate( 1, 1)
    bkg_values[i, 2] = normalvariate(-1, 1)
    bkg_values[i, 3] = normalvariate(-1, 1)

cuts = [
    (0, "<", random()),
    (0, ">", random()),
    (1, "<", random()),
    (2, ">", random()),
    (3, ">", random()),
    ]    

cuts, fom = hep.cuts.iterativeOptimize(sig_values, bkg_values, cuts)

assert_(in_range(0, cuts[0][2], 3))
assert_(in_range(-3, cuts[1][2], 0))
assert_(cuts[2][2] > 0)
assert_(cuts[3][2] < 0)
assert_(cuts[4][2] < 0)

assert_(fom > 300)
