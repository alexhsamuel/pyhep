#-----------------------------------------------------------------------
#
# module hep.hist.axis
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Histogram axes."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

import copy
import hep
from   hep.bool import *
from   hep.num import *
from   hep.py import getCommonType, coerceTypes
import math

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Axis:
    """Base axis class."""


    def __init__(self, axis_type=float, **kw_args):
        if type(axis_type) is not type:
            raise ValueError, "axis type must be a Python type"
        self.type = axis_type
        self.__dict__.update(kw_args)


    def __repr__(self):
        if hasattr(self, "range") and self.range is not None:
            range = ", range=(%r, %r)" % self.range
        else:
            range = ""
        return "Axis(%s%s)" % (self.type.__name__, range)



#-----------------------------------------------------------------------

class BinnedAxis(Axis):
    """Base for binned axis types."""

    pass



#-----------------------------------------------------------------------

class EvenlyBinnedAxis(BinnedAxis):
    """A binned axis with evenly-spaced bins.

    A 'Axis' consists of a mapping from a set of values to bin numbers.
    The axis spans a range '(lo, hi)' of values of a numerical type.
    Values must satisfy 'lo <= value < hi'; otherwise, 'value' is
    considered to be an underflow or overflow.

    The bin numbers are consecutive integers starting at zero.  In
    addition, the strings "underflow" and "overflow" are valid bin
    numbers; these correspond to values below and above the acceptable
    range of values."""


    def __init__(self, num_bins, range, axis_type=float, **kw_args):
        """Construct a new axis.

        'num_bins' -- The number of bins.

        'range' -- A pair '(lo, hi)', specifying the allowed range of
        values.

        'axis_type' -- The Python type used to represent values."""

        # Make sure 'axis_type' is a type.
        if type(axis_type) is not type:
            raise ValueError, "axis type must be a Python type"
        # Make sure 'lo' and 'hi' are of the right type.
        lo, hi = range
        try:
            lo = axis_type(lo)
            hi = axis_type(hi)
        except ValueError:
            raise ValueError, \
                  "axis lo and hi must be of the axis type"
        # Perform sanity checks on the range.
        if lo == hi:
            raise ValueError, "axis range is empty"
        if lo > hi:
            lo, hi = hi, lo
        # If the axis type is integral, the range must be an even
        # multiple of the number of bins.
        if axis_type in (int, long) \
           and ((hi - lo) % num_bins) != 0:
            raise ValueError, \
                  "number of bins must be a divisor of axis range"

        BinnedAxis.__init__(self, axis_type, **kw_args)
        self.__num_bins = int(num_bins)
        self.__range = (lo, hi)


    def __repr__(self):
        result = "EvenlyBinnedAxis(%d, %r" \
                 % (self.__num_bins, self.__range)
        if hasattr(self, "name"):
            result += ", name=%r" % self.name
        if hasattr(self, "units"):
            result += ", units=%r" % self.units
        result += ")"
        return result


    number_of_bins = property(lambda self: self.__num_bins)
    """The number of bins on the axis."""

    range = property(lambda self: self.__range)
    """The range of values spanned by the axis."""

    type = property(lambda self: self.type)
    """The type used to represent values."""
        

    def __call__(self, value):
        """Return the bin number corresponding to 'value'."""

        try:
            # Convert value to the right type.
            value = self.type(value)
        except ValueError:
            # Conversion failed.
            raise ValueError, "axis value %s is not of type %s" \
                  % (repr(value), self.type)

        lo, hi = self.__range
        num_bins = self.__num_bins
        # Compute the bin number.
        bin_number = int(math.floor(
            ((value - lo) * num_bins) / (hi - lo)))
        if bin_number < 0:
            # Underflow bin.
            return "underflow"
        elif bin_number >= num_bins:
            # Overflow bin.
            return "overflow"
        else:
            # A normal bin.
            return bin_number


    def getBinRange(self, bin_number):
        """Return the range of values corresponding to a bin.

        'bin_number' -- The number of the bin to consider.

        returns -- A pair '(lo, hi)', specifying the range of that bin.

        If 'bin_number' is "underflow", returns '(None, axis_lo)', where
        'axis_lo' is the minimum value of the entire axis.  Similarly,
        if 'bin_number' is "overflow", returns '(axis_hi, None)'."""

        lo, hi = self.__range
        num_bins = self.__num_bins
        
        if bin_number == "underflow":
            return (None, lo)

        elif bin_number >= 0 and bin_number < num_bins:
            # A regular bin.
            bin_lo = lo + bin_number * (hi - lo) / num_bins
            bin_hi = lo + (bin_number + 1) * (hi - lo) / num_bins
            return (self.type(bin_lo), self.type(bin_hi))

        elif bin_number == "overflow":
            return (hi, None)
        
        else:
            raise ValueError, "unknown bin number %s" % repr(bin_number)


    def getBinCenter(self, bin_number):
        """Return the central value of a bin."""

        if bin_number in ("underflow", "overflow"):
            raise ValueError, bin_number
        bin_lo, bin_hi = self.getBinRange(bin_number)
        return (bin_lo + bin_hi) / 2



#-----------------------------------------------------------------------

class UnevenlyBinnedAxis(BinnedAxis):

    def __init__(self, bin_edges, axis_type=float, **kw_args):
        """Construct a new axis.

        'axis_type' -- The Python type used to represent values."""

        # Make sure there are at least two edges specified.
        if len(bin_edges) < 2:
            raise ValueError, "'bin_edges' must have two elements"
        # Guess the axis type.
        axis_type = getCommonType(bin_edges)
        # Make sure 'axis_type' is a type.
        if type(axis_type) is not type:
            raise ValueError, "axis type must be a Python type"
        # Make sure 'bin_edges' are of the right type.
        bin_edges = [ axis_type(e) for e in bin_edges ]
        # Make sure they're ascending.
        bin_edges.sort()

        BinnedAxis.__init__(self, axis_type, **kw_args)
        self.bin_edges = bin_edges


    def __repr__(self):
        return "UnevenlyBinnedAxis(%s)" % repr(self.bin_edges)


    number_of_bins = property(lambda self: len(self.bin_edges) - 1)
    """The number of bins on the axis."""

    range = property(lambda self:
                     (self.bin_edges[0], self.bin_edges[-1]))
    """The range of values spanned by the axis."""

    type = property(lambda self: self.type)
    """The type used to represent values."""
        

    def __call__(self, value):
        """Return the bin number corresponding to 'value'."""

        try:
            # Convert value to the right type.
            value = self.type(value)
        except ValueError:
            # Conversion failed.
            raise ValueError, "axis value %s is not of type %s" \
                  % (repr(value), self.type)

        if value < self.bin_edges[0]:
            # Underflow bin.
            return "underflow"
        elif value >= self.bin_edges[-1]:
            # Overflow bin.
            return "overflow"
        else:
            # A normal bin.  Perform binary search to find the bin
            # number. 
            return hep.binarySearch(self.bin_edges, value)


    def getBinRange(self, bin_number):
        """Return the range of values corresponding to a bin.

        'bin_number' -- The number of the bin to consider.

        returns -- A pair '(lo, hi)', specifying the range of that bin.

        If 'bin_number' is "underflow", returns '(None, axis_lo)', where
        'axis_lo' is the minimum value of the entire axis.  Similarly,
        if 'bin_number' is "overflow", returns '(axis_hi, None)'."""

        if bin_number == "underflow":
            return (None, self.bin_edges[0])

        elif bin_number >= 0 and bin_number < len(self.bin_edges) - 1:
            # A regular bin.
            return (self.bin_edges[bin_number],
                    self.bin_edges[bin_number + 1])

        elif bin_number == "overflow":
            return (self.bin_edges[-1], None)
        
        else:
            raise ValueError, "unknown bin number %s" % repr(bin_number)


    def getBinCenter(self, bin_number):
        """Return the central value of a bin."""

        if bin_number in ("underflow", "overflow"):
            raise ValueError, bin_number
        bin_lo, bin_hi = self.getBinRange(bin_number)
        return (bin_lo + bin_hi) / 2



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def AxisIterator(axis, overflows=False, range=None):
    """Return an iterator over bin numbers for 'axis'.

    The iterator yields bin numbers in ascending order.

    'axis' -- An 'BinnedAxis' object.

    'overflows' -- If true, include underflow and overflow bins."""

    if overflows:
        yield "underflow"
    for index in xrange(axis.number_of_bins):
        if range is not None:
            # Check that the bin is in range.
            lo, hi = axis.getBinRange(index)
            if lo < range[0] or hi > range[1]:
                continue
        yield index
    if overflows:
        yield "overflow"


def AxesIterator(axes, overflows=False, range=None):
    """Return an interator over bin numbers for 'axes'.

    'axes' -- A sequence of 'BinnedAxis' objects.

    'overflows' -- If true, include underflow and overflow bins."""

    if range is None:
        range = len(axes) * (None, )

    # Handle the zero-dimensional case.
    if len(axes) == 0:
        yield ()
        return

    # Handle the general case recursively.  Get the first axis, and loop
    # over the rest, prepending each to all indices of the remaining
    # axes.
    for first_index in AxisIterator(axes[0], overflows, range[0]):
        for next in AxesIterator(axes[1 :], overflows, range[1 :]):
            yield (first_index, ) + next


def getBinRange(axes, bin_numbers):
    return [ a.getBinRange(n)
             for (a, n) in zip(axes, bin_numbers) ]


def parseAxisArg(arg):
    # Is it already an 'Axis'?
    if arg is None:
        return Axis(float)
    elif isinstance(arg, Axis):
        # Yes.  Use a copy of it.
        return copy.copy(arg)
    else:
        # No.  Construct one.
        # How many arguments?
        if len(arg) >= 1:
            axis_type = arg[0]
        else:
            axis_type = float
        axis = Axis(axis_type)
        if len(arg) >= 2:
            axis.name = arg[1]
        if len(arg) >= 3:
            axis.units = arg[2]
        if len(arg) >= 4:
            try:
                lo, hi = arg[3]
            except TypeError:
                raise ValueError, "range must be a '(low, high)' pair"
            if lo is not None:
                lo = axis_type(lo)
            if hi is not None:
                hi = axis_type(hi)
            axis.range = (lo, hi)

        return axis
    

def parseBinnedAxisArg(arg):
    """Parse a binned axis specification from 'arg'.

    If 'arg' is a 'BinnedAxis' object, it is simply returned.
    Otherwise, it is assumed to be a sequence with format

        '(num_bins, range, name, units)'

    where 'range' is a '(lo, hi)' pair, and 'name' and 'units' are
    optional.   

    returns -- A 'BinnedAxis' object."""

    # Is it already an 'BinnedAxis'?
    if isinstance(arg, BinnedAxis):
        # Yes.  Use a copy of it.
        return copy.copy(arg)

    # Is it some other kind of axis?
    elif isinstance(arg, Axis):
        # Oops.  We need a binned axis.
        raise TypeError, "axis must be binned"

    # Not an axis object; interpret it as a sequence.
    else:
        # How many arguments?
        try:
            length = len(arg)
        except ValueError:
            length = None
        if length is None or length not in (2, 3, 4):
            raise ValueError, \
                  "axis must have the form " \
                  "'(num_bins, range[, name[, units]])'"

        # Unpack the basic stuff.
        num_bins = arg[0]
        try:
            lo, hi = arg[1]
        except TypeError:
            raise TypeError, "range must be a '(lo, hi)' pair"
        # Infer the axis type.
        lo, hi = coerce(lo, hi)
        axis_type = type(lo)

        # Make the axis.
        axis = EvenlyBinnedAxis(num_bins, (lo, hi), axis_type)

        # If there's another element, it's the axis name.
        if length >= 3:
            # This argument used to be the axis type.  Check that we're
            # not passed a type by code that hasn't been updated.
            # FIXME: Remove this after a while.
            if type(arg[2]) == type:
                raise TypeError, "third element is the axis name"
            axis.name = str(arg[2])
        # If there's another element, it's the axis units.
        if length >= 4:
            axis.units = str(arg[3])

        return axis
    

def wrap1D(arg):
    try:
        length = len(arg)
    except TypeError:  # 'len() of unsized object'
        return (arg, )
    else:
        return arg


def combineAxes(axis0, axis1):
    axis = None

    if isinstance(axis0, EvenlyBinnedAxis) \
       and isinstance(axis1, EvenlyBinnedAxis) \
       and axis0.range == axis1.range:
        # Two evenly-binned histograms with the same range.  Do they
        # have compatible binning?
        if axis0.number_of_bins % axis1.number_of_bins == 0:
            axis = copy.copy(axis0)
        elif axis1.number_of_bins % axis0.number_of_bins == 0:
            axis = copy.copy(axis1)

    elif isinstance(axis0, BinnedAxis) \
         and not isinstance(axis1, BinnedAxis) \
         and (not hasattr(axis1, "range")
              or axis1.range is None
              or isIntervalSubset(axis1.range, axis0.range)):
        # Only 'axis0' is binned, and either 'axis1' has no range or its
        # range is contained in that of 'axis0'.
        axis = copy.copy(axis0)

    elif isinstance(axis1, BinnedAxis) \
         and not isinstance(axis0, BinnedAxis) \
         and (not hasattr(axis0, "range")
              or axis0.range is None 
              or isIntervalSubset(axis0.range, axis1.range)):
        # Only 'axis1' is binned, and either 'axis0' has no range or its
        # range is contained in that of 'axis1'.
        axis = copy.copy(axis1)

    # Have we failed to combine the axes so far?
    if axis is None:
        # Construct a lowest-common-denominator unbinned axis.
        axis_type = coerceTypes(axis0.type, axis1.type)
        if hasattr(axis0, "range") and hasattr(axis1, "range"):
            range = intervalUnion(axis0.range, axis1.range)
        elif hasattr(axis0, "range"):
            range = axis0.range
        elif hasattr(axis1, "range"):
            range = axis1.range
        else:
            range = None
        axis = Axis(axis_type)
        # Combine other attributes, giving 'axis0' precedence.
        axis.__dict__.update(axis1.__dict__)
        axis.__dict__.update(axis0.__dict__)
        # Set the range.
        axis.range = range

    return axis


def combineAxisList(axes):
    if len(axes) == 0:
        axis = Axis(int, range=(0, 1))
    elif len(axes) == 1:
        axis = copy.copy(axes[0])
    else:
        axis = copy.copy(axes[0])
        for next in axes[1 :]:
            axis = combineAxes(axis, next)

    if not hasattr(axis, "range"):
        axis.range = (0, 1)
    range = axis.range

    # Is the range degenerate?
    if range is None:
        axis.range = (0, 1)
    elif range[0] == range[1]:
        assert not isinstance(axis, BinnedAxis)
        # Yes.  Is it zero?
        if range[0] == 0:
            # Just make something up.
            axis.range = (0, 1)
        else:
            # Adjust the range to an interval around the value.
            axis.range = (range[0] - abs(range[0]) / 2,
                          range[0] + abs(range[0]) / 2)

    return axis


