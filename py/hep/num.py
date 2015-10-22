#--------------------------------------------------*- coding: Latin1 -*-
#
# num.py
#
#-----------------------------------------------------------------------

"""Numerical and mathematical functions and code."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division
from __future__ import generators

# from   ext import erf, erfc
import math
import operator
import random

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

golden_ratio = (1 + math.sqrt(5)) / 2

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Statistic(float):
    """A number with statistical uncertainty.

    A 'Statistic' object is a 'float' with an extra attribute
    'uncertainty' that contains a statistical uncertainty.  The
    statistic can be used in ordinary arithmetical operations, and the
    uncertainty is propagated assuming each statistic is from an
    independent normal distribution.

    Create a statistic by specifying its value and uncertainty,
    e.g. 'Statistic(val, unc)'.  Both the value and uncertainty are
    converted to 'float'.  You may also specify the value and
    uncertainty together in a string of the form '"val +- unc"' or
    '"val ± unc"'.  If the uncertainty is unspecified or 'None', the
    square root of the value is used."""

    def __new__(class_, value, uncertainty=None):
        # Convert moments to statistics.
        if isinstance(value, Moments):
            val = value.mean
            unc = value.standard_deviation
        # Handle strings specially.
        elif isinstance(value, str):
            # If the uncertainty was specified in the string, extract it.
            if "±" in value:
                val, unc = map(float, value.split("±", 1))
            elif value.find("+-") != -1:
                val, unc = map(float, value.split("+-", 1))
            else:
                # No uncertainty in the string.  Treat the string as the
                # value only.
                val = float(value)
                unc = None
        else:
            # Convert the value to a float value.
            val = float(value)
            # Take the uncertainty from the 'uncertainty' attribute, if
            # present.
            if hasattr(value, "uncertainty"):
                unc = value.uncertainty
            else:
                unc = None

        # The 'uncertainty' argument overrides uncertainty extracted
        # from 'value'.
        if uncertainty is not None:
            unc = float(uncertainty)
        # Still no uncertainty?  Use the square root of the value.
        if unc is None:
            unc = math.sqrt(abs(val))

        # Make sure the uncertainty is positive.
        if unc < 0:
            raise ValueError, "negative uncertainty %f" % unc

        # Build the statistic.
        statistic = float.__new__(class_, val)
        statistic.__uncertainty = unc
        return statistic


    uncertainty = property(lambda self: self.__uncertainty)


    def __repr__(self):
        return "Statistic(%f, %f)" % (float(self), self.uncertainty)


    def __str__(self):
        return "%f ± %f" % (float(self), self.uncertainty)


    def __neg__(self):
        return Statistic(-float(self), self.uncertainty)


    def __add__(self, other):
        if hasattr(other, "uncertainty"):
            return Statistic(
                float(self) + float(other),
                math.hypot(self.uncertainty, other.uncertainty))
        else:
            return Statistic(float(self) + other, self.uncertainty)
        

    def __radd__(self, other):
        return Statistic.__add__(self, other)

        
    def __sub__(self, other):
        if hasattr(other, "uncertainty"):
            return Statistic(
                float(self) - float(other),
                math.hypot(self.uncertainty, other.uncertainty))
        else:
            return Statistic(float(self) - other, self.uncertainty)


    def __rsub__(self, other):
        return -Statistic.__sub__(self, other)


    def __mul__(self, other):
        if hasattr(other, "uncertainty"):
            return Statistic(
                float(self) * float(other),
                math.hypot(float(self) * other.uncertainty,
                           float(other) * self.uncertainty))
        else:
            return Statistic(float(self) * other, self.uncertainty * other)
    

    def __rmul__(self, other):
        return Statistic.__mul__(self, other)


    def __div__(self, other):
        if hasattr(other, "uncertainty"):
            return Statistic(
                float(self) / float(other),
                math.hypot(float(self) * other.uncertainty,
                           float(other) * self.uncertainty)
                / float(other) ** 2)
        else:
            return Statistic(float(self) / other, self.uncertainty / other)


    def __rdiv__(self, other):
        if hasattr(other, "uncertainty"):
            return Statistic(
                float(other) / float(self),
                math.hypot(float(self) * other.uncertainty,
                           float(other) * self.uncertainty)
                / float(self) ** 2)
        else:
            return Statistic(other / float(self), self.uncertainty / other)


    # Use the same division operators for true division.
    __truediv__ = __div__
    __rtruediv__ = __rdiv__


    def format(self, value_digits=6, uncertainty_digits=None, exponent=None):
        if uncertainty_digits is None:
            uncertainty_digits = value_digits
        if exponent is None:
            return "%.*f ± %.*f" \
                   % (value_digits, float(self),
                      uncertainty_digits, self.uncertainty)
        elif exponent == "%":
            if value_digits > 0:
                value_size = 4 + value_digits
            else:
                value_size = 3
            if uncertainty_digits > 0:
                uncertainty_size = 3 + uncertainty_digits
            else:
                uncertainty_size = 2
            return "(%*.*f ± %*.*f)%%" \
                   % (value_size, value_digits,
                      100 * float(self),
                      uncertainty_size, uncertainty_digits,
                      100 * self.uncertainty)
        elif isinstance(exponent, int):
            scale = 10 ** (-exponent)
            return "(%.*f ± %.*f)x10^%d" \
                   % (value_digits, scale * float(self),
                      uncertainty_digits, scale * self.uncertainty,
                      exponent)



#-----------------------------------------------------------------------

class Efficiency:
    """The efficiency of a sampled process.

    Estimates the binonmial parameter from a sampling of trials from a
    binomial process.  The trials may be weighted.

    The 'float' value of an efficiency object is 'p / t', where 'p' is
    the number of passing samples (sum of weights of passing samples)
    and 't' is the total number of samples (sum of weights of all
    samples).  The 'uncertainty' attribute holds an estimate of the
    uncertainty on the efficiency, 'p (t - p) / t ** 3'."""


    def __init__(self):
        self.tries = 0
        self.passes = 0.0


    def __repr__(self):
        return "Efficiency(tries=%r, passes=%r)" \
               % (self.tries, self.passes)


    def __str__(self):
        return self.format()


    def sample(self, outcome, weight=1):
        """Record the outcome of a trial.

        'outcome' -- A boolean value, indicating whether the trial was
        successful.

        'weight' -- The statistical weight of this sample."""
        
        weight = float(weight)
        self.tries += weight
        if outcome:
            self.passes += weight


    def __lshift__(self, outcome):
        """Equivalent to 'sample' with unit weight."""

        self.sample(outcome)


    def __float__(self):
        if self.tries != 0:
            return self.passes / self.tries
        else:
            return 0


    def __get_uncertainty(self):
        p = self.passes
        t = self.tries
        if t != 0:
            return math.sqrt(p * (t - p) / (t ** 3))
        else:
            return 0


    uncertainty = property(__get_uncertainty)


    def format(self, digits=1, exponent="%"):
        return Statistic(self).format(digits, digits, exponent)
        


#-----------------------------------------------------------------------

class Moments(object):

    def __init__(self, numbers=()):
        self.count = 0
        self.sum = 0
        self.sum_sq = 0
        for number in numbers:
            self << number


    def __lshift__(self, number):
        self.count += 1
        self.sum += number
        self.sum_sq += number * number


    def __get_mean(self):
        n = self.count
        if n < 1:
            return 0
        else:
            return self.sum / n


    mean = property(__get_mean)


    def __get_variance(self):
        n = self.count
        if n < 2:
            return 0
        return n / (n - 1) * (self.sum_sq / n - (self.sum / n) ** 2)


    variance = property(__get_variance)


    def __get_standard_deviation(self):
        # Due to roundoff errors, the variance may be slightly
        # negative.  Return zero in that case.
        return math.sqrt(max(self.variance, 0))


    standard_deviation = property(__get_standard_deviation)
            

    def __get_statistic(self):
        return Statistic(self.mean, self.standard_deviation)


    statistic = property(__get_statistic)



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def binary(x, bits=32):
    """Represent the least significant 'bits' of 'x' in binary form."""

    result = ""
    x = long(x)
    bit = 1l << (bits - 1)
    while bit > 0:
        if x & bit != 0:
            result += "1"
        else:
            result += "0"
        bit >>= 1
    return result


def gaussian(mu, sigma, x):
    """Return a probability density from a Gaussian distribution.

    'mu' -- The distribution's mean.

    'sigma' -- The distribution's standard deviation.

    'x' -- The value at which to evaluate the probability density."""

    return 0.3989422804014326779399 \
           * math.exp(-0.5 * ((x - mu) / sigma)**2) \
           / sigma


def almost_equal(num0, num1, fraction=1e-5):
    """Return true if 'num0' and 'num1' are almost equal.

    'fraction' -- The fraction of the larger of 'num0' and 'num1'
    within which the values are almost equal."""

    return abs(num0 - num1) < fraction * max(abs(num0), abs(num1))


def get_bit(value, bit):
    """Return 'True' if bit 'bit' is set in 'value'."""
    
    return value & (1 << bit) != 0


def hypot(*terms):
    """Generalized multidimensional hypotenuse.

    'terms' -- Any number of numerical terms.

    returns -- The square root of the sum of squares of 'terms'."""
    
    return math.sqrt(
        reduce(lambda sum, term: sum + term * term,
               terms,
               0))


def mhypot(first_term, *terms):
    """Generalized multidimensional hypotenuse with Minkowski metric.

    returns -- The square root of the square of the 'first_term' minus
    the sum of squares of remaining '*terms'."""
    
    return math.sqrt(reduce(lambda sum, term: sum - term * term,
                            terms, first_term * first_term))


def factorial(n):
    """Compute the factorial of 'n'."""

    # Check the argument.
    if n < 0:
        raise ValueError, "'n' must be nonnegative"
    if n != long(n):
        raise ValueError, "'n' must be integral"
    # Compute the factorial.
    # FIXME: Use a less naive algorithm.
    result = 1
    for i in xrange(2, n + 1):
        result *= i
    return result


def in_range(min_value, value, max_value):
    """Return true if 'value' is in a semi-open interval."""

    return value >= min_value and value < max_value


def near(central_value, half_interval, value):
    """'abs(central_value - value) < half_interval'."""

    return abs(central_value - value) < half_interval


def if_then(condition, value_if_true, value_if_false):
    """Return a conditional value.

    returns -- 'value_if_true' if 'condition' is true; otherwise
    'value_if_false'.  Note that the types of the two possible results
    are coerced together."""

    value_if_true, value_if_false = coerce(value_if_true, value_if_false)

    if condition:
        return value_if_true
    else:
        return value_if_false


def sum(values):
    """Return the sum of 'values'."""

    return reduce(lambda a, b: a + b, values, 0)


def product(values):
    """Return the product of 'values'."""

    return reduce(lambda a, b: a * b, values, 1)


def mean(values):
    """Return the mean of a sequence of values.

    'values' -- A sequence or iterable of numbers."""
    
    length = 0
    sum = 0
    for value in values:
        length += 1
        sum += value
    if length == 0:
        raise ValueError, "no values"
    return sum / length


def variance(values, sample=False):
    """Return the variance of a sequence of values.

    'values' -- A sequence or iterable of numbers."""
    
    num = 0
    sum = 0
    sum_of_squares = 0
    for value in values:
        num += 1
        sum += value
        sum_of_squares += value * value
    if num == 0:
        raise ValueError, "no values"
    mean = sum / num
    result = sum_of_squares / num - mean * mean
    if sample:
        result *= num / (num - 1)
    return result


def standard_deviation(values, sample=False):
    """Return the standard deviation of a sequence of values.

    'values' -- A sequence or iterable of numbers."""

    return math.sqrt(variance(values, sample))


def constrain(value, lo=None, hi=None):
    """Return 'value' constrained to the range '(lo, hi)'.

    If 'lo' or 'hi' is 'None', that constraint is ignored."""

    if lo is not None and value < lo:
        return lo
    if hi is not None and value > hi:
        return hi
    return value


def range(min, max=None, step=1):
    """Return an iterator over a range of values from 'min' to 'max'.

    returns -- An iterator over values starting at 'min' and less than
    'max', each incremented by 'step'."""
    
    # Allow 'range(n)' as shorthand for 'range(0, n)'.
    if max is None:
        max = min
        min = 0

    x = min
    while x < max:
        yield x
        x += step


def multirange(*ranges):
    """Generate the outer product of ranges.

    '*ranges' -- Pairs of the form '(lo, hi)'.

    returns -- A generator over the outer product of the specified
    ranges.  Each generated element is a tuple with number of elements
    equal to the number of arguments ('*ranges')."""

    if len(ranges) > 1:
        for x in range(*ranges[0]):
            for y in multirange(*ranges[1 :]):
                yield (x, ) + y
    else:
        for x in range(*ranges[0]):
            yield (x, )
    

def grid(count, lo, hi):
    x = lo
    step = (hi - lo) / (count - 1)
    for c in xrange(count - 1):
        yield x
        x += step
    yield hi


def multigrid(*ranges):
    if len(ranges) > 1:
        for x in grid(*ranges[0]):
            for y in multigrid(*ranges[1 :]):
                yield (x, ) + y
    else:
        for x in grid(*ranges[0]):
            yield (x, )
   

def intervalUnion(interval0, interval1):
    return (min(interval0[0], interval1[0]),
            max(interval0[1], interval1[1]))


def isIntervalSubset(interval0, interval1):
    """Return true if 'interval0' is a subset of 'interval1'."""
    
    return interval0[0] >= interval1[0] and interval0[1] <= interval1[1]


def dividerange(lo, hi, count):
    for i in xrange(count):
        interval_lo = (hi - lo) * i / count
        interval_hi = (hi - lo) * (i + 1) / count
        yield interval_lo, interval_hi
    

def unweight(samples, weight_fn, random=random.random):
    """Unweight 'samples' by acceptance-rejection.

    Generate an unweighted subset of 'samples'.  The probability of
    including a sample is computed by 'weight_fn'.

    'samples' -- An iterable.

    'weight_fn' -- Function that computes the weight of a sample.  Must
    return a number between zero and one.

    'random' -- A function that generates uniform random numbers between
    zero and one.

    yields -- A subset of 'samples'."""

    for sample in samples:
        weight = weight_fn(sample)
        assert 0 <= weight <= 1
        if random() < weight:
            yield sample


#-----------------------------------------------------------------------
# stuff that depends on CERNLIB
#-----------------------------------------------------------------------

try:
    from hep.cernlib.num import *
except ImportError:
    pass

