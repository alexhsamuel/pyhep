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

# The PDF for the test distribution.
def pdf(a, b, x, y):
    return a * b * exp(a * x + b * y) / ((exp(a) - 1) * (exp(b) - 1))


# Use acceptance-rejection to construct a sample from this PDF.
samples = []
pdf_max = pdf(3, 1, 1, 1)
while len(samples) < 1000:
    x = random()
    y = random()
    if (pdf_max * random() < pdf(3, 1, x, y)):
        samples.append({"x": x, "y": y})

result = maximumLikelihoodFit(pdf, (("a", 3), ("b", 1)), samples)
print result

compare(result.minuit_status, 3)
compare(result.values["a"], 3, precision=0.5)
compare(result.values["b"], 1, precision=0.5)
