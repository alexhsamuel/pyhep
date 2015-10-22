#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import hep.hist.function
from   hep.test import compare

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

fn = hep.hist.function.SampledFunction1D()
fn.addSample(0, 0)
fn.addSample(1, 3)
fn.addSample(2, 4)
fn.addSample(3, 3)
fn.addSample(4, 0)

compare(fn(0),    0.0,  precision=1e-8)
compare(fn(0.5),  1.5,  precision=1e-8)
compare(fn(1),    3.0,  precision=1e-8)
compare(fn(1.4),  3.4,  precision=1e-8)
compare(fn(2),    4,    precision=1e-8)
compare(fn(2.05), 3.95, precision=1e-8)
compare(fn(3.8),  0.6,  precision=1e-8)

