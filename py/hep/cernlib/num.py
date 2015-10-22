#-----------------------------------------------------------------------
#
# num.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Numerical functions based on CERNLIB."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import ext

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def chiSquareCDF(x, n):
    """CDF for chi-square distribution.

    'n' -- The chi-squared parameter; must be one or larger.

    returns -- The probability that a random variable chosen
    according to a chi-square distribution with 'n' degrees of
    freedom will have a value of 'x' or lower."""

    return 1 - ext.prob(x, n)


