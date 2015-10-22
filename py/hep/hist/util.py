#--------------------------------------------------*- coding: Latin1 -*-
#
# util.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Utility functions for working with histograms."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division
from __future__ import generators

from   axis import *
import hep.py
from   hep.fn import enumerate, scan
from   hep.num import Statistic
import hep.text
from   histogram import *
from   math import sqrt, hypot
import random
import sys

#-----------------------------------------------------------------------
# helper functions
#-----------------------------------------------------------------------

def _makeSureHistogramsAreSimilar(*histograms):
    for hist in histograms[1:]:
        if hist.dimensions != histograms[0].dimensions:
            raise ValueError, \
                  "histograms must have the same number of dimensions"
        for axis1, axis2 in zip(hist.axes, histograms[0].axes):
            if axis1.range != axis2.range:
                raise ValueError, "each axis must have the same range"
            if axis1.number_of_bins != axis2.number_of_bins:
                raise ValueError, \
                      "each axis must have the same number of bins"


def _cloneHistogram(histogram, **kw_args):
    """Produce a copy of 'histogram'.

    '**kw_args' -- Overrides when creating the duplicate."""

    if "bin_type" not in kw_args:
        kw_args["bin_type"] = histogram.bin_type
    if "error_model" not in kw_args:
        kw_args["error_model"] = histogram.error_model
    duplicate = apply(Histogram, histogram.axes, kw_args)
    duplicate.__dict__.update(histogram.__dict__)
    return duplicate


def _format(number):
    """Format number in for a 7-character field."""
    
    if number == None:
        return "   None"
    elif type(number) in (int, long):
        return "%7d" % number
    elif type(number) == float:
        if number == 0:
            return "      0"
        elif abs(number) < 1e-2:
            return "%3.1e" % number
        elif abs(number) < 1e+4:
            return "%7.3f" % number
        else:
            return "%3.1e" % number
    else:
        assert False


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def BinIterator(histogram, overflow=False):
    """Return an iterator over bins of 'histogram'.

    'overflow' -- If true, include all underflow and overflow bins.

    returns -- An iterator of triplets '(bin_number, contents, error)'
    for all bins in 'histogram'."""
    
    for bin_number in AxesIterator(histogram.axes, overflow):
        yield bin_number, \
              histogram.getBinContent(bin_number), \
              histogram.getBinError(bin_number)
        

def BinValueIterator(histogram, overflow=False):
    """Return an iterator over bin contents of 'histogram'.

    'overflow' -- If true, include all underflow and overflow bins.

    returns -- An iterator of contents of all bins in 'histogram'."""

    for bin_number in AxesIterator(histogram.axes, overflow):
        yield histogram.getBinContent(bin_number)
        

def BinErrorIterator(histogram, overflow=False):
    """Return an iterator over bin errors of 'histogram'.

    'overflow' -- If true, include all underflow and overflow bins.

    returns -- An iterator of bin errors of all bins in 'histogram'."""

    for bin_number in AxesIterator(histogram.axes, overflow):
        yield histogram.getBinError(bin_number)
        

def fillBinValues(histogram, values, overflow=False):
    values = iter(values)
    for bin_number in AxesIterator(histogram.axes, overflow):
        histogram.setBinContent(bin_number, values.next())


def slice(histogram, slice_index, bins="all"):
    """Slice or project an axis in a multidimensional histogram.

    This function slices (N-1)-dimensional planes from an N-dimensional
    histogram, and adds them together to produce an (N-1)-dimensional
    histogram.  Any dimension may be sliced, and any or all bins along
    that axis may be specified to be added together in the slice.

    To produce a simple single-bin-wide slice of the histogram, specify
    the dimension number to slice for 'slice_index', and the bin number
    (as a one-element sequence) for 'bins'.  To produce a slice wider
    than one bin, specify a consecutive range of bin numbers for 'bins'.

    To projection out one dimension of the histogram, specify the
    dimension number for 'slice_index', and either '"all"' (to include
    overflow and underflow bins) or '"range"' (to leave out overflow and
    underflow bins) for 'bins'.

    'histogram' -- The histogram to slice or project.  It must be of two
    or more dimensions.

    'slice_index' -- The index of the axis to slice or project.  Must be
    less than the number of dimensions of 'histogram'.

    'bins' -- A sequence of bin numbers specifying which bins to slice
    or project.  If '"all"', all bins on the slice axis, including
    overflow and underflow, are added together.  If '"range"', all bins
    except overflow and underflow are added.

    returns -- A histogram of one fewer dimensions that 'histogram'."""

    if histogram.dimensions == 1:
        raise ValueError, "a one-dimensional histogram may not be sliced"
    if slice_index < 0 or slice_index >= histogram.dimensions:
        raise ValueError, "invalid slide axis index %d" % slice_index

    axes = histogram.axes
    # Get the axis being sliced or projected out.
    slice_axis = axes[slice_index]
    # Splice out that axis, to obtain the remaining axes.
    unsliced_axes = axes[:slice_index] + axes[slice_index + 1:]

    # Figure out which bins on the slice axis we'll add together.
    if bins == "all":
        # A projection: add all bins, including overflows.
        slice_bin_numbers = tuple(AxisIterator(slice_axis, True))
        title = "projection over "
    elif bins == "range":
        # A projection, not including overflows.
        slice_bin_numbers = tuple(AxisIterator(slice_axis, False))
        title = "projection (without overflows) over "
    else:
        # A subset of bins.
        slice_bin_numbers = tuple(bins)
        title = "slice of "
    # Make the title descriptive.
    if hasattr(slice_axis, "name"):
        title += slice_axis.name
    else:
        title += "axis %d" % slice_index
    if hasattr(histogram, "title"):
        title += " of " + histogram.title

    # Construct the resulting histogram.
    error_model = histogram.error_model
    result = Histogram(bin_type=histogram.bin_type, title=title,
                       error_model=error_model, *unsliced_axes)

    # Loop over all bin numbers that we're *not* slicing, i.e. bin
    # numbers in the remaining non-slice axes.  These are bin numbers in
    # the resulting histogram.
    for sliced_bin_numbers in AxesIterator(unsliced_axes):
        # Construct a bin number template for the original histogram,
        # which has the bin numbers of 'sliced_bin_numbers' and a
        # placeholder for the bin number on the slice axis.
        bin_number = list(sliced_bin_numbers[:slice_index]) \
                     + [None, ] \
                     + list(sliced_bin_numbers[slice_index:])
        bin_value = 0
        if error_model == "symmetric":
            errors = 0
        elif error_model == "asymmetric":
            lo_errors = 0
            hi_errors = 0
        # Now loop over bins to be included in the slice.
        for slice_bin_number in slice_bin_numbers:
            # Complete the bin number by filling in the bin number along
            # the slice axis.
            bin_number[slice_index] = slice_bin_number
            # Accumulate bin contents.
            bin_value += histogram.getBinContent(bin_number)
            # Add bin errors in quadrature.
            if error_model == "symmetric":
                errors += histogram.getBinError(bin_number)[0] ** 2
            elif error_model == "asymmetric":
                lo, hi = histogram.getBinError(bin_number)
                lo_errors += lo * lo
                hi_errors += hi * hi
        # Fill in the bin contents and error in the result.
        result.setBinContent(sliced_bin_numbers, bin_value)
        if error_model == "symmetric":
            result.setBinError(sliced_bin_numbers, sqrt(errors))
        elif error_model == "asymmetric":
             result.setBinError(sliced_bin_numbers,
                            (sqrt(lo_errors), sqrt(hi_errors)))

    return result


def project(events,
            histograms,
            weight=None):
    """Fill historams from rows.

    For each row in 'events', each histogram in 'histograms' is
    accumulated.  For each histogram, the value to accumulate is
    computed from an 'expression' method on that histogram object.

    If a 'weight' function is provided, it is called for each row to
    compute the weight used to accumulate all histograms for that row.

    'events' -- A sequence or iterator of tabel rows or similar
    dictionary objects.

    'histograms' -- A sequence of histograms.  Each must have a a
    callable 'expression' attribute, which is called on each row to
    determine the value to accumulate.

    'weight' -- A callable to determine the weight to use for each row.

    returns -- The number of events (or total weight) projected."""

    def makeProjection(histogram):
        result = (histogram.expression, histogram.accumulate)
        try:
            result += (histogram.selection, )
        except AttributeError:
            pass
        return result

    projections = [ makeProjection(h) for h in histograms ]

    return hep.table.project(events, projections, weight, True)


def getRange(histogram, bin_numbers=None, errors=False, overflows=False):
    """Return the range of values of bins of a histogram.

    'bin_numbers' -- An iteratable over bin numbers to consider.

    'errors' -- If true, the range of errors is considered when
    computing the range.

    returns -- The '(min, max)' range of values."""

    if bin_numbers is None:
        bin_numbers = AxesIterator(histogram.axes, overflows=overflows)

    min = None
    max = None
    # Loop over bins.
    for bin_number in bin_numbers:
        # Find the bin value and error.
        value = histogram.getBinContent(bin_number)
        if errors:
            lo_err, hi_err = histogram.getBinError(bin_number)
            lo = value - lo_err
            hi = value + hi_err
        else:
            lo = value
            hi = value
        # Update the min and max.
        if min is None or lo < min:
            min = lo
        if max is None or hi > max:
            max = hi

    return (min, max)


def scale(histogram, factor, error_model="asymmetric", bin_type=float):
    """Scale the contents of a histogram by a constant factor.

    'error_model' -- The error model to use for the scaled histogram.

    'bin_type' -- The bin type of the scaled histogram. 

    returns -- A copy of 'histogram', with bin contents scaled by
    'factor'."""
    
    # Make the copy.
    result = _cloneHistogram(
        histogram, bin_type=bin_type, error_model=error_model)
        
    # Fill the bins.
    for bin in AxesIterator(histogram.axes, True):
        result.setBinContent(bin, factor * histogram.getBinContent(bin))
        if error_model in ("symmetric", "asymmetric"):
            lo, hi = histogram.getBinError(bin)
            result.setBinError(bin,
                            (abs(factor) * lo, abs(factor) * hi))

    return result


def accumulate(hist1, hist2, scale2=1):
    """Multiply and add 'hist2' into 'hist1'.

    Adds binwise the contents of 'hist2' times 'scale2' to corresponding
    bins of 'hist1'."""

    # FIXME: This should be implemented as an extension function (or
    # methods), and the 'scale' and 'add' methods should call it.

    _makeSureHistogramsAreSimilar(hist1, hist2)
    do_errors = hist1.error_model in ("symmetric", "asymmetric")

    # Add the bin contents.
    for bin in AxesIterator(hist1.axes, True):
        contents = hist1.getBinContent(bin) \
                   + scale2 * hist2.getBinContent(bin)
        hist1.setBinContent(bin, contents)
        if do_errors:
            lo1, hi1 = hist1.getBinError(bin)
            lo2, hi2 = hist2.getBinError(bin)
            hist1.setBinError(bin, (hypot(lo1, scale2 * lo2),
                                    hypot(hi1, scale2 * hi2)))


def add(hist1, hist2, scale2=1, error_model="asymmetric", bin_type=float):
    """Add two histograms.

    'hist1', 'hist2' -- Two histograms.  They must have the same
    dimensions, axes, and binning.

    'scale2' -- Scale factor for 'hist2'.

    'error_model' -- The error model to use for the scaled histogram.

    'bin_type' -- The bin type of the scaled histogram.  

    returns -- A new histogram whose bins contain the sum of contents of
    'hist1' and 'scale2' times 'hist2'."""

    # Make the copy.
    _makeSureHistogramsAreSimilar(hist1, hist2)
    result = _cloneHistogram(
        hist1, bin_type=bin_type, error_model=error_model)

    # Add the bin contents.
    for bin in AxesIterator(hist1.axes, True):
        contents = hist1.getBinContent(bin) + scale2 * hist2.getBinContent(bin)
        result.setBinContent(bin, contents)
        if error_model in ("symmetric", "asymmetric"):
            lo1, hi1 = hist1.getBinError(bin)
            lo2, hi2 = hist2.getBinError(bin)
            result.setBinError(bin, (hypot(lo1, scale2 * lo2),
                                  hypot(hi1, scale2 * hi2)))
    return result


def divide(hist1, hist2, error_model="asymmetric", bin_type=float):
    """Divide bin-by-bin two histograms.

    'hist1', 'hist2' -- Two histograms.  They must have the same
    dimensions, axes, and binning.

    'error_model' -- The error model to use for the scaled histogram.

    'bin_type' -- The bin type of the scaled histogram.  

    returns -- A new histogram whose bins contain quotients of contents
    of 'hist1' and 'hist2'."""

    # Make the copy.
    _makeSureHistogramsAreSimilar(hist1, hist2)
    result = _cloneHistogram(
        hist1, bin_type=bin_type, error_model=error_model)
    # Divide the bin contents.
    for bin in AxesIterator(hist1.axes, True):
        v1 = hist1.getBinContent(bin)
        v2 = hist2.getBinContent(bin)
        if v1 == 0 or v2 == 0:
            result.setBinContent(bin, 0)
        else:
            result.setBinContent(bin, v1 / v2)
            if error_model in ("symmetric", "asymmetric"):
                q1 = 1 / v2
                q2 = v1 / (v2 * v2)
                lo1, hi1 = hist1.getBinError(bin)
                lo2, hi2 = hist2.getBinError(bin)
                result.setBinError(bin, (hypot(q1 * lo1, q2 * lo2),
                                         hypot(q1 * hi1, q2 * hi2)))
                
    return result


def integrate(histogram, overflows=False, ranges=None):
    """Integrate a histogram.

    'overflows' -- Whether to include underflow and overflow bins in the
    sum.

    returns -- The sum of bin contents of 'histogram'."""

    result = 0
    for bin_index in AxesIterator(histogram.axes, overflows, ranges):
        bin_value = Statistic(histogram.getBinContent(bin_index),
                              histogram.getBinError(bin_index)[0])
        result += bin_value
    return result


def normalize(histogram, normalization=1, overflows=False):
    """Noramlize a histogram.

    Returns a copy of 'histogram', scaled so that the sum of bins is
    equal to 'normalization'.  If 'overflows' is true, underflow and
    overflow bins are included in the normalization."""

    # Integrate the histogram.
    integral = integrate(histogram, overflows)
    # Return the scaled histogram.
    if integral != 0:
        return scale(histogram, normalization / integral)
    else:
        return scale(histogram, 1)


def normalizeSlices(histogram, slice_index=0, normalization=1,
                    overflows=False):
    """Normalize slices in 'histogram'.

    Construct a copy of 'histogram' in which slices along axis
    'slice_index' are normalized independently to 'normalization'.  (The
    slice is scaled so that the integral of a one-dimensional slice
    along the slice index is 'noramlization'.)

    'histogram' -- The histogram to normalize.

    'slice_index' -- The axis index along which to slice.

    'normalization' -- The value of the integral to which to noramlize
    each slice.

    'overflows' -- If true, include the contents of overflow bins in the
    normalization.

    returns -- A normalized copy of 'histogram'."""

    if histogram.dimensions == 1:
        raise ValueError, "a one-dimensional histogram may not be sliced"
    if slice_index < 0 or slice_index >= histogram.dimensions:
        raise ValueError, "invalid slice axis index %d" % slice_index

    axes = histogram.axes
    # Get the axis being sliced or projected out.
    slice_axis = axes[slice_index]
    # Splice out that axis, to obtain the remaining axes.
    unsliced_axes = axes[:slice_index] + axes[slice_index + 1:]
    # Construct the bin numbers along the slice axis.
    slice_bin_numbers = tuple(AxisIterator(slice_axis, overflows))

    # Construct the resulting histogram.
    error_model = histogram.error_model
    result = Histogram(bin_type=histogram.bin_type,
                       error_model=error_model, *histogram.axes)
                              
    # Loop over all bin numbers that we're *not* slicing, i.e. bin
    # numbers in the remaining non-slice axes.  
    for sliced_bin_numbers in AxesIterator(unsliced_axes):
        # Construct a bin number template for the original histogram,
        # which has the bin numbers of 'sliced_bin_numbers' and a
        # placeholder for the bin number on the slice axis.
        bin_number = list(sliced_bin_numbers[:slice_index]) \
                     + [None, ] \
                     + list(sliced_bin_numbers[slice_index:])
        slice_value = 0
        # Integrate the slice.
        for slice_bin_number in slice_bin_numbers:
            # Complete the bin number by filling in the bin number along
            # the slice axis.
            bin_number[slice_index] = slice_bin_number
            # Accumulate bin contents.
            slice_value += histogram.getBinContent(bin_number)
        # Compute the scale factor for this slice.
        if slice_value == 0:
            # Don't divide by zero.
            scale = 1
        else:
            scale = normalization / slice_value
        # Copy the slice into the result, scaling to normalize.
        for slice_bin_number in slice_bin_numbers:
            bin_number[slice_index] = slice_bin_number
            # Scale and copy bin content.
            result.setBinContent(
                bin_number,
                scale * histogram.getBinContent(bin_number))
            # Scale and copy bin error, if necessary.
            if error_model in ("symmetric", "antisymmetric"):
                lo, hi = histogram.getBinError(bin_number)
                result.setBinError(
                    bin_number,
                    (scale * lo, scale * hi))

    return result


def getMoment(histogram, moment):
    """Compute a moment of 'histogram' in each dimensions.

    'histogram' -- A histogram.

    'moment' -- Which moment to compute.  For 'moment' equal to one,
    computes the mean value along each dimension.

    returns -- A sequence of values, each of which is a moment in a
    the corresponding dimension of the histogram."""

    dimensions = histogram.dimensions
    axes = histogram.axes
    
    sums = [0] * dimensions
    weights = [0] * dimensions
    for bin_index in AxesIterator(histogram.axes):
        weight = histogram.getBinContent(bin_index)
        if weight == 0:
            continue
        for dim in xrange(dimensions):
            pos = axes[dim].getBinCenter(bin_index[dim])
            sums[dim] += (pos ** moment) * weight
            weights[dim] += weight

    for dim in xrange(dimensions):
        if sums[dim] != 0:
            sums[dim] /= weights[dim]

    return sums

            
def mean(histogram):
    """Return the mean of 'histogram' along each axis."""

    return getMoment(histogram, 1)


def variance(histogram):
    """Return the variance of 'histogram' along each axis."""

    moments1 = getMoment(histogram, 1)
    moments2 = getMoment(histogram, 2)
    return [ m2 - m1 ** 2 for (m1, m2) in zip(moments1, moments2) ]


def standardDeviation(histogram):
    """Return the standard deviation of 'histogram' along each axis."""

    return [ sqrt(v) for v in variance(histogram) ]


def getBinCenter(axes, bin_numbers):
    return [ axis.getBinCenter(bin_number)
             for axis, bin_number in zip(axes, bin_numbers) ]


def makeNiceRange(lo, hi, margin_factor=1):
    """Find a range of "nice" values including the range '(lo, hi)'.

    'margin_factor' -- A scale factor, greater than one, specifying
    additional space to allow on either end of the scale beyond 'lo' and
    'hi'.  For instance, a value of 1.1 will leave an extra 10% on
    either side of the scale.

    returns -- A '(lo, hi)' interval containing the original 'lo' and
    'hi'."""
    
    # Check arguments.
    if margin_factor < 1:
        raise ValueError, "'margin_factor' must be at least one"""
    # Scale the range by the margin factor.
    if lo < 0:
        lo *= margin_factor
    else:
        lo /= margin_factor
    if hi < 0:
        hi /= margin_factor
    else:
        hi *= margin_factor
    # Don't allow an empty range.
    if lo == hi:
        if lo == 0:
            return (-1, 1)
        elif abs(lo) < 1:
            return (lo - abs(lo) / 10, lo + abs(lo) / 10)
        else:
            return (lo - 1, lo + 1)
    # Find the order of magnitude of values.
    scale = round(math.log10(abs(abs(lo) - abs(hi))))
    # Round the low and high values to a power of ten that is an order
    # of magnitude lower than the scale.
    scale_mag = 10 ** (scale - 1)
    lo = scale_mag * math.floor(lo / scale_mag)
    hi = scale_mag * math.ceil(hi / scale_mag)

    return lo, hi


def autoHistogram1D(values, number_of_bins=None, range=None,
                    weights=None, name=None, units=None):
    """Construct a 1D histogram from some values.

    'values' -- An iterable of values.  They must all be the same type.

    'numer_of_bins' -- The number of bins in the histogram.  If 'None',
    it is chosen automatically.

    'range' -- The range of the histogram.  If 'None', it is chosen
    automatically.

    'weights' -- An iterable of weights corresponding to 'values'.  If
    'None', unit weights are used.

    'name' -- Name describing the values for the histogram's axis.

    'units' -- Units of the values.

    returns -- A histogram."""

    if len(values) == 0:
        raise ValueError, "'values' is empty"
    value_type = type(values[0])

    if number_of_bins is None:
        # Choose a reasonable number of bins.
        number_of_bins = min(100, max(10, len(values) / 10))

    if range is None:
        # Compute the actual range of values.
        lo, hi = hep.fn.minmax(None, values)
        if value_type in (int, long):
            # For integral types, expand the upper limit by one so the
            # largest value fits in the last bin.
            hi += 1
            # We also need to adjust the range so it is a multiple of
            # the number of bins.
            hi += number_of_bins - (hi - lo) % number_of_bins
        else:
            lo, hi = makeNiceRange(lo, hi)
    else:
        lo, hi = range
    # Cast the range to the appropriate type.
    lo, hi = map(value_type, (lo, hi))
    
    # Use 'float' bins if weights are given, 'int' otherwise.
    if weights is None:
        bin_type = int
        error_model = "poisson"
    else:
        bin_type = float
        error_model = "symmetric"

    # Construct the histogram.
    histogram = Histogram1D(number_of_bins, (lo, hi),
                            bin_type=bin_type, error_model=error_model)
    if name is not None:
        histogram.axis.name = name
    if units is not None:
        histogram.axis.units = units
    # Fill the values into it.
    if weights is None:
        map(histogram.accumulate, values)
    else:
        for value, weight in zip(values, weights):
            histogram.accumulate(value, weight)

    return histogram


def autoHistogram(values, numbers_of_bins=None, ranges=None,
                  weights=None):
    """Construct a histogram from some values.

    Each element of 'values', as well as 'numbers_of_bins' and 'ranges',
    must be a sequence of the same length.  That length is the number
    of dimensions of the histogram.

    'values' -- An iterable of values.  Each is a sequence of numbers,
    all of the same length.

    'numbers_of_bins' -- The number of bins along each axis of the
    histogram.  If an element is 'None', the number of bins along that
    axis is chosen automatically.  If 'numbers_of_bins' is 'None',
    binning on all axes is chosen automatically.

    'ranges' -- The range along each axis.  If an element is 'None', the
    range along that axis is chosen automatically.  If 'ranges' is
    'None', all axis ranges are chosen automatically.

    'weights' -- An iterable of weights corresponding to 'values'.  If
    'None', unit weights are used.

    returns -- A histogram."""

    if len(values) == 0:
        raise ValueError, "'values' is empty"
    # Determine the number of dimensions.
    dimensions = len(values[0])
    # Determine the types of the columns.
    value_types = [ type(c) for c in values[0] ]

    if numbers_of_bins is None:
        # Assume 'None' along each dimension.
        numbers_of_bins = dimensions * [None]
    else:
        numbers_of_bins = list(numbers_of_bins)
    if len(numbers_of_bins) != dimensions:
        raise ValueError, "'numbers_of_bins' is wrong length"
    # Assign default numbers of bins to dimensions for which it is not
    # specified. 
    for i in range(dimensions):
        if numbers_of_bins[i] is None:
            # Choose a reasonable number of bins.
            numbers_of_bins[i] = 20

    if ranges is None:
        # Assume 'None' along each dimension
        ranges = dimensions * [None]
    else:
        ranges = list(ranges)
    if len(ranges) != dimensions:
        raise ValueError, "'ranges' is wrong length"
    # Determine range automatically along each dimension for which it is
    # not specified. 
    for i in range(dimensions):
        if ranges[i] is None:
            # Compute the actual range of values.
            lo, hi = hep.fn.minmax(None, [ v[i] for v in values ])
            if value_types[i] in (int, long):
                # For integral types, expand the upper limit by one so
                # the largest value fits in the last bin.
                hi += 1
                # We also need to adjust the range so it is a multiple
                # of the number of bins.
                hi += numbers_of_bins[i] - (hi - lo) % numbers_of_bins[i]
            else:
                lo, hi = makeNiceRange(lo, hi)
        else:
            lo, hi = ranges[i]
        # Cast the range to the appropriate type. 
        ranges[i] = value_types[i](lo), value_types[i](hi)
    
    # Use 'float' bins if weights are given, 'int' otherwise.
    if weights is None:
        bin_type = int
    else:
        bin_type = float

    # Construct the histogram.
    histogram = Histogram(*zip(numbers_of_bins, ranges),
                          **{ "bin_type": bin_type })
    # Fill the values into it.
    if weights is None:
        map(histogram.accumulate, values)
    else:
        for value, weight in zip(values, weights):
            histogram.accumulate(value, weight)

    return histogram


def addBin(histogram, bin_number, total=None):
    bin_type = histogram.bin_type
    error_model = histogram.error_model

    if total is None:
        if error_model == "symmetric":
            total = (bin_type(0), 0.0)
        elif error_model == "asymmetric":
            total = (bin_type(0), (0.0, 0.0))
        else:
            total = (bin_type(0), None)

    value, error = total
    value += histogram.getBinContent(bin_number)
    if error_model == "symmetric":
        error = hypot(error, histogram.getBinError(bin_number)[0])
    elif error_model == "asymmetric":
        lo0, hi0 = error
        lo1, hi1 = histogram.getBinError(bin_number)
        error = hypot(lo0, lo1), hypot(hi0, hi1)
    return value, error


def rebin(histogram, grouping):
    """Combine bins in 1D 'histogram'.

    'histogram' -- A one-dimensional histogram with an evenly-binned x
    axis. 

    'grouping' -- The number of bins to be combined into a single bin.
    Must be a divisor of the numebr of bins of 'histogram'.

    returns -- A new histogram."""

    if histogram.dimensions != 1:
        raise NotImplementedError, \
              "%d-dimensional histograms" % histogram.dimensiosn
    if not isinstance(histogram.axis, EvenlyBinnedAxis):
        raise NotImplemenetedError, "axis must be evenly binned"
    
    old_axis = histogram.axis
    if histogram.axis.number_of_bins % grouping != 0:
        raise ValueError, "'grouping' must divide the number of bins"

    new_axis = EvenlyBinnedAxis(old_axis.number_of_bins / grouping,
                                old_axis.range,
                                old_axis.type)
    hep.py.copyPublicAttributes(new_axis, old_axis)

    new_histogram = Histogram(
        new_axis,
        bin_type=histogram.bin_type,
        error_model=histogram.error_model)
    hep.py.copyPublicAttributes(new_histogram, histogram)

    for bin_number in AxisIterator(new_axis, overflows=True):
        if bin_number in ("underflow", "overflow"):
            total = addBin(histogram, bin_number)
        else:
            total = None
            for bn in range(bin_number * grouping,
                            (bin_number + 1) * grouping):
                total = addBin(histogram, bn, total)
        value, error = total
        new_histogram.setBinContent(bin_number, value)
        if error is not None:
            new_histogram.setBinError(bin_number, error)
            
    return new_histogram


def dump(histogram, out=sys.stdout):
    """Write a summary of 'histogram' to 'out'.

    'out' -- A file object."""

    axes = histogram.axes

    out.write("Histogram")
    if hasattr(histogram, "name"):
        out.write(" \"%s\"" % histogram.name)
    out.write(", %d dimensions\n" % histogram.dimensions)

    out.write("%s bins" % histogram.bin_type.__name__)
    if hasattr(histogram, "units"):
        out.write(" in \"%s\"" % histogram.units)
    out.write(", %r error model\n" % histogram.error_model)
    
    for key in histogram.__dict__.keys():
        out.write("%s: %r\n" % (key, histogram.__dict__[key]))

    out.write("\n")

    for i, axis in enumerate(axes): 
        if i == 0:
            out.write("axes: ")
        else:
            out.write("      ")
        out.write("%s\n" % axis)

    out.write("\n")

    if histogram.error_model == "none":
        def formatError(error):
            return ""
    elif histogram.error_model in ("symmetric", "gaussian"):
        def formatError(error):
            return "±" + _format(error[0])
    elif histogram.error_model in ("asymmetric", "poisson"):
        def formatError(error):
            return "+%s -%s" % (_format(error[1]), _format(error[0]))

    abbrev = hep.text.abbreviator(17)
    for i, axis in enumerate(axes):
        if hasattr(axis, "name") and axis.name:
            name = abbrev(axis.name)
        else:
            name = "axis %d" % i
        out.write("%s " % name.center(17))
    out.write("  " + "bin value / error".center(27) + "\n")
    
    out.write((27 + 18 * len(axes)) * "-" + "\n")

    for bin_numbers in AxesIterator(axes, overflows=True):
        ranges = [ a.getBinRange(n)
                   for (a, n) in zip(axes, bin_numbers) ]
        for range in ranges:
            out.write("[%s,%s) " 
                      % (_format(range[0]), _format(range[1])))
        out.write("  " + _format(histogram.getBinContent(bin_numbers)) + " "
                  + formatError(histogram.getBinError(bin_numbers)) + "\n")

    out.write("\n")
    

def transformAxis(histogram, transformation, which_axis=0, axis_name=None):
    """Apply a transformation to one axis of a histogram.

    A new histogram is created with one axis transformed according to
    'transformation'.  This function does not rebin data or transform
    bin contents in any other way.  All it does is transform the
    positions of bins along the axis (creating an unvenly-binned axis),
    and copies bin contents from 'histogram' to the corresponding
    transformed bins in the new histogram.

    'transformation' -- A callable that transforms values along the
    transformed axis.  The transformation must be monotonically
    increasing.

    'which_axis' -- In a multidimensional histogram, the index of the
    axis to transform.

    'axis_name' -- The name to use for the new axis.  If 'None', one is
    generated from the old axis name.

    returns -- A new histogram."""

    axis = histogram.axes[which_axis]
    error_model = histogram.error_model
    
    # Compute bin edges for the new histogram by transforming bin edges
    # of the old histogram.
    bin_edges = []
    for bin_number in AxisIterator(axis):
        lo, hi = axis.getBinRange(bin_number)
        lo = transformation(lo)
        hi = transformation(hi)
        # Make sure the bin edges stay ordered.
        if hi <= lo:
            raise ValueError, \
                  "transformation must increase monotonically"
        # Keep the low bin edge.
        bin_edges.append(lo)
    # We also need the upper edge of the last bin.
    bin_edges.append(hi)

    # Construct the axis for the transformed histogram.
    new_axis = UnevenlyBinnedAxis(bin_edges)
    # Set the name.
    if axis_name is None:
        if hasattr(axis, "name"):
            new_axis.name = "transformed %s" % axis.name
        else:
            # Don't set the name.
            pass
    else:
        new_axis.name = axis_name
    # Construct a set of new axes, substituting the transformed axis.
    new_axes = list(histogram.axes)
    new_axes[which_axis] = new_axis

    # Construct the transformed histogram.
    new_histogram = apply(Histogram, new_axes,
        { "bin_type": histogram.bin_type, "error_model": error_model })
    # Copy bin contents.
    for bin_numbers in AxesIterator(new_axes, overflows=True):
        new_histogram.setBinContent(
            bin_numbers, histogram.getBinContent(bin_numbers))
        # Copy bin errors too, if appropriate.
        if error_model in ("symmetric", "asymmetric",):
            new_histogram.setBinError(
                bin_numbers, histogram.getBinError(bin_numbers))

    return new_histogram


def makeSample1D(name, number_of_entries=1000):
    """Construct a sample one-dimensional histogram.

    'name' -- The name of the sample histogram.  Valid names are
    '"flat"' (uniform between zero and one), '"normal gaussian"'
    (Gaussian with zero mean and unit standard deviation), and
    '"gaussian"' (Gaussian with a mean and standard deviation of two).

    'number_of_entries' -- The number of random entries to fill into the
    histogram.

    returns -- A new histogram."""

    import random

    if name == "flat":
        range = (0.0, 1.0)
        generate = random.random
    elif name == "normal gaussian":
        range = (-5.0, 5.0)
        generate = lambda : random.normalvariate(0, 1)
    elif name == "gaussian":
        range = (-6.0, 10.0)
        generate = lambda : random.normalvariate(2, 2)
    else:
        raise ValueError, "unknown sample histogram name %r" % name

    # Make the histogram.
    histogram = Histogram1D(20, range, title=name)
    # Fill it.
    for i in xrange(number_of_entries):
        histogram << generate()

    return histogram


def smooth2D(histogram, smoothing=1):
    """Smooth a two-dimensional histogram.

    Smooths 'histogram' by averaging neighboring bins.  The number of
    neighbors in each direction is given by 'smoothing', so for each bin
    in the smoothed histogram, a total of '(2 * smoothing + 1) ** 2'
    bins are included in the average, except for edge bins.

    returns -- A new histogram."""

    # Make an empty histogram.
    smoothed = Histogram(
        histogram.axes[0], histogram.axes[1],
        bin_type=histogram.bin_type, error_model="none")

    nx = histogram.axes[0].number_of_bins
    ny = histogram.axes[1].number_of_bins
    for bx, by in AxesIterator(histogram.axes):
        # Compute the value for bin '(bx, by)'.  Count the number of
        # bins included in the average, as well as the sum.
        num = 0
        sum = 0
        # Average over neighbors, but don't go past edges.
        for x in range(max(0, bx - smoothing),
                       min(bx + smoothing + 1, nx)):
            for y in range(max(0, by - smoothing),
                           min(by + smoothing + 1, ny)):
                num += 1
                sum += histogram.getBinContent((x, y))
        smoothed.setBinContent((bx, by), sum / num)

    return smoothed


def Generator1D(histogram):
    """A random number generator distributed according to 'histogram'.

    Returns a random number generator that yields random numbers within
    the range of one-dimensional 'histogram', where the probability of
    choosing a number within each bin is proportional to the bin
    contents.  The probability is uniform within the bin.  Underflow and
    overflow bins are ignored.

    returns -- A generator that yields random numbers."""

    axis = histogram.axis
    lo, hi = axis.range
    num_bins = axis.number_of_bins
    
    # Construct a table of cumulative bin contents.
    bin_contents = [
        histogram.getBinContent(b) for b in AxisIterator(axis) ]
    cumulative = list(scan(lambda x, y: x + y, bin_contents, 0))
    # The total integral is the last element of this table.
    integral = cumulative[-1]

    # Choose the function to generate the actual value, once we've
    # narrowed down the bin.  The value is distributed uniformly within
    # the bin.  We need different functions depending on whether the
    # axis values are integral or floating-point.
    if isinstance(axis.type, int) or isinstance(axis.type, long):
        uniform = random.randrange
    else:
        uniform = random.uniform

    # Generate indefinitely.
    while True:
        # Choose a random value less than the total integral.
        x = random.uniform(0, integral)
        # Look up, by binary search, the largest bin whose cumulative
        # integral is larger than this value.  That's the bin we'll use.
        b0 = 0
        b1 = num_bins // 2
        b2 = num_bins
        while True:
            if b1 != 0 and x < cumulative[b1 - 1]:
                b2 = b1
                b1 = (b0 + b1) // 2
            elif x >= cumulative[b1]:
                b0 = b1
                b1 = (b1 + b2) // 2
            else:
                # Found the right bin.
                break
        # Throw a value within this bin.
        lo, hi = axis.getBinRange(b1)
        yield uniform(lo, hi)


def getComparisonChiSquare(histogram0, histogram1):
    """Compute the chi square comparing two histograms.

    The chi square is the sum of squares of bin differences divided by
    the combined error.  The combined error on a bin is the individual
    bin errors of the two histograms added in quadrature.  Bins that are
    zero in both histograms are omitted.

    The two histograms must have the same range and binning.

    returns -- 'chi_square, number_of_bins', where 'number_of_bins' is
    the number of bins used to compute the chi square."""
    
    _makeSureHistogramsAreSimilar(histogram0, histogram1)

    chi_square = 0
    num_bins = 0
    for bin in AxesIterator(histogram0.axes):
        x0 = histogram0.getBinContent(bin)
        lo, hi = histogram0.getBinError(bin)
        err0 = (lo + hi) / 2
        x1 = histogram1.getBinContent(bin)
        lo, hi = histogram1.getBinError(bin)
        err1 = (lo + hi) / 2
        
        err = err0 ** 2 + err1 ** 2
        if err == 0 and x0 == 0 and x1 == 0:
            pass
        else:
            chi_square += (x0 - x1) ** 2 / err
            num_bins += 1

    return chi_square, num_bins


