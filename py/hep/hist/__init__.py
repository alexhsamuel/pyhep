#-----------------------------------------------------------------------
#
# module hep.hist
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Histograms.

The following error models are supported:

  'explicit' -- Asymmetrical errors may be specified for each bin using
  the 'setError' method.  No errors are computed automatically.

  'gaussian' -- The symmetrical error on the value of each bin is
  computed assuming a Gaussian distribution.

  'none' -- Bins have zero errors.

  'poisson' -- The asymmetrical error on the value of each bin is computed
  assuming a Poisson distribution.

  'quadrature' -- The symmetrical error on each bin is square root of
  the sum of squares of weights accumulated to that bin.

Error values are always of type 'float'.
"""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

from   axis import Axis, BinnedAxis, AxisIterator, AxesIterator
import copy
import copy_reg
from   function import Function1D, isFunction, SampledFunction1D, \
                       sampleFunction1D
from   function import Graph, ContourGraph, isGraph, \
                       makeContourGraphFromHist
from   hep import ext
from   hep.bool import *
from   histogram import Histogram, Histogram1D, isHistogram
from   scatter import isScatter, Scatter
import sys
from   util import *

