#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cuts import FisherDiscriminant, optimize
from   hep.test import assert_
import random

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# Generate some samples.
samples1 = [ ((random.normalvariate(0, 1), random.normalvariate(0, 1)), 1)
             for n in xrange(1000) ]
samples2 = [ ((random.normalvariate(2, 1), random.normalvariate(3, 2)), 1)
             for n in xrange(1000) ]

# Construct the Fisher discriminant.
fisher = FisherDiscriminant(samples1, samples2)

# Compute the Fisher values for each sample.
f1 = [ fisher(s) for (s, w) in samples1 ]
f2 = [ fisher(s) for (s, w) in samples2 ]
# Find the optimal cut on the Fisher discriminant.
cut, fom = optimize(f1, f2, ">")

# Count the number of signal events that were correctly classified.
right1 = 0
for value in f1:
    if value > cut:
        right1 += 1
assert_(right1 > 900)

# Count the number of background events that were correctly classified.
right2 = 0
for value in f2:
    if value < cut:
        right2 += 1
assert_(right2 > 800)

