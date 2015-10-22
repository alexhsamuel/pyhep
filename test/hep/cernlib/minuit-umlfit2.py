#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cernlib.minuit import maximumLikelihoodFit
import hep.table
from   hep.test import compare
import random

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

schema = hep.table.Schema()
schema.addColumn("x", "float32")
table = hep.table.create("minuit-umlfit2.table", schema)
for i in xrange(100):
    table.append(x=random.normalvariate(3, 1))

result = maximumLikelihoodFit(
    "gaussian(mu, sigma, x)", (("mu", 0), ("sigma", 10, 0.1, 0, 1000)),
    table)
print result

compare(result.minuit_status, 3)
compare(result.values["mu"], 3, precision=0.3)
compare(result.values["sigma"], 1, precision=0.3)
