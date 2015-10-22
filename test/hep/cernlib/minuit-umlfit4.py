#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.cernlib.minuit import maximumLikelihoodFit
from   hep.test import compare
from   math import exp
from   random import random

#-----------------------------------------------------------------------
# test
#-----------------------------------------------------------------------

# The PDF for the test distribution; not normalized.
def pdf(a, b, x):
    return a + exp(b * x)


# Use acceptance-rejection to construct a sample from this PDF.
samples = []
pdf_max = pdf(1, 3, 1)
while len(samples) < 10000:
    x = random()
    if pdf_max * random() < pdf(1, 3, x):
        samples.append({ "x": x })

result = maximumLikelihoodFit(
    pdf,
    (("a", 2, 0.1, 0, 1000), ("b", 2, 0.1, 0, 10)),
    samples,
    normalization_range=(("x", 0, 1), ))
print result

compare(result.minuit_status, 3)
compare(result.values["a"], 1, precision=1.0)
compare(result.values["b"], 3, precision=1.0)
