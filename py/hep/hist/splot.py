#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import numarray
from   numarray.linear_algebra import inverse

outer_product = numarray.multiply.outer

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def makeSPlot(categories, samples):
    """Construct the sPlot weights function.

    'categories' -- A sequence of categories.  Each is a pair '(pdf,
    num)', where 'pdf' is the normalized PDF of the *reduced* variables
    for the category, and 'num' is the number of samples in that
    category.

    'samples' -- A iterable of samples.

    returns -- A function that takes a sample as its argument and
    returns an array of sPlot weights for the given categories."""

    num_categories = len(categories)

    # Split the 'categories' argument into a sequence of PDFs and an
    # array of numbers.
    pdfs = [ f for (f, n) in categories ]
    nums = numarray.array([ n for (f, n) in categories ], type="Float64")

    # Accumulate the inverse of the covariance matrix.
    V_inv = numarray.zeros((num_categories, num_categories), "Float64")
    for sample in samples:
        # Evaluate PDFs for this sample.
        pds = numarray.array([ f(sample) for f in pdfs ])
        # Compute the contribution for this sample.
        denominator = numarray.dot(nums, pds) ** 2
        if denominator != 0:
            V_inv += outer_product(pds, pds) / denominator
    # Invert to obtain the covariance matrix.
    V = inverse(V_inv)

    def getWeights(sample):
        # Evaluate PDFs for this sample.
        pds = numarray.array([ f(sample) for f in pdfs ])
        # Compute an array of the weights.
        denominator = numarray.dot(nums, pds)
        if denominator != 0:
            return numarray.matrixmultiply(V, pds) / denominator
        else:
            return numarray.zeros((num_categories, ), "Float32")

    getWeights.covariance_matrix = V
    return getWeights


