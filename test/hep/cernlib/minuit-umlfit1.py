#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cernlib.minuit import maximumLikelihoodFit
from   hep.test import compare
import random

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

result = maximumLikelihoodFit(
    "gaussian(mu, sigma, x)", (("mu", 0), ("sigma", 10, 0.1, 0, 100)),
    [ {"x": random.normalvariate(3, 1)} for i in xrange(100) ])

compare(result.minuit_status, 3)
compare(result.values["mu"], 3, precision=0.3)
compare(result.values["sigma"], 1, precision=0.3)
