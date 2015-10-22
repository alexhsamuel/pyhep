#-----------------------------------------------------------------------
#
# module cuts.py
#
# Copyright 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Functions for constructing. optimizing. and studying cuts."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division
from __future__ import generators

from   hep.fn import enumerate
import hep.hist
from   numarray import *
from   numarray.linear_algebra import inverse
import random

#-----------------------------------------------------------------------
# helper functions
#-----------------------------------------------------------------------

def _getMoments(sample):
    """Return the first three moment matrices of 'sample'."""

    # We'll iterate just once over 'sample'.
    sample = iter(sample)
    # Grab the first sample point.  We need it to set up the moments as
    # arrays of the correct shape.
    try:
        point, weight = sample.next()
    except StopIteration:
        raise ValueError, "sample is empty"
    point = array(point)
    # Initialize the moments.
    moment0 = weight
    moment1 = weight * point
    moment2 = weight * multiply.outer(point, point)
    # Loop over the rest of the sample points.
    for point, weight in sample:
        point = array(point)
        moment0 += weight
        moment1 += weight * point
        moment2 += weight * multiply.outer(point, point)
    # Make sure the weight is non-zero.
    if moment0 == 0:
        raise ValueError, "total sample weight is zero"
    return moment0, moment1, moment2


def _popUnique(value_list):
    """Remove and return the last unqiue element of 'value_list'.

    All consecutive occurrences of the last value at the end of
    'value_list' are removed, and that value is returned."""

    value = value_list.pop(-1)
    while value_list and value_list[-1] == value:
        value_list.pop(-1)
    return value


#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class FisherDiscriminant(object):
    """The Fisher discriminant to separate two samples.

    A Fisher discriminant is a linear classifier in a multidimensional
    space.

    The resulting Fisher discriminant may be scaled and shifted without
    spoiling the optimal separation."""
    
    def __init__(self, sample1, sample2, normalize=False):
        """Compute a Fisher discriminant.

        'sample1', 'sample2' -- Sequences or other iterables of samples.
        Each sample sets must yield at least one sample point.  The
        sample point is of the form '(coordinates, weight)' where
        'coordinates' is a sequence of coordinate values, and 'weight'
        is a value.

        'normalize' -- If true, normalize the Fisher discriminant such
        that its value over 'sample1' has a zero mean and unit standard
        deviation."""

        # Scan the samples, constructing moments.
        m01, m11, m21 = _getMoments(sample1)
        m02, m12, m22 = _getMoments(sample2)
        # Compute centroids.
        c1 = m11 / m01
        c2 = m12 / m02

        # Compute dispersion matrices.
        d1 = m21 / m01 - multiply.outer(c1, c1)
        d2 = m22 / m02 - multiply.outer(c2, c2)
        d = d1 + d2
        # d = (m01 * d1 + m02 * d2) / (m01 + m02)
        # Compute the Fisher coefficients.
        a = dot(inverse(d), c1 - c2)

        if normalize:
            mean = dot(a, c1)
            variance = dot(transpose(a), dot(m21, a)) / m01 - mean * mean
            stddev = sqrt(variance)
            self.coefficients = a / stddev
            self.offset = -mean / stddev
        else:
            self.coefficients = a
            self.offset = 0


    def __repr__(self):
        coefficients = ", ".join(map(str, self.coefficients))
        return "FisherDiscriminant(coefficients=(%s), offset=%s)" \
               % (coefficients, self.offset)


    def __call__(self, values):
        return dot(self.coefficients, values) + self.offset



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def s_over_b(signal, background):
    """'S/B' figure of merit for cuts.

    returns -- 'signal / background' if 'background' is nonzero; twice
    'signal' otherwise."""
    
    if background == 0:
        return signal * 2
    else:
        return signal / background


def s_squared_over_s_plus_b(signal, background):
    """'S**2/(S+B)' figure of merit for cuts.

    returns -- 'signal' squared over the sum of 'signal' and
    'background' (or zero if both are zero).""" 

    if signal + background > 0:
        return signal * signal / (signal + background)
    else:
        return 0


def makeSortArray(values):
    """Construct sorting indices for the columns of 'values'.

    returns -- An integer array the same shape as 'values'.  Each column
    'i' of the result contains row indices of 'values' that sorts the
    corresponding column 'i' of 'values'."""

    num_events, num_vars = values.shape

    # Choose a type for the result large enough to hold row indices of
    # 'values'. 
    if num_events < (1 << 15):
        sort_type = Int16
    else:
        sort_type = Int32
    # Construct the output array.
    sort_array = array(
        shape=(num_events, num_vars), type=sort_type)
    # Fill in sort indices.
    for var in range(num_vars):
        sort_array[:, var] = argsort(values[:, var])

    return sort_array


def searchSorted(values, sort_indices, target):
    """Binary search for 'target' in 'values'.

    'values' -- A sequence of values.

    'sort_indices' -- A sequence of indices into 'values' which sort
    'values' into ascending order.

    'target' -- The target value of the search.

    returns -- The index of the element in 'sort_indices' which points
    to the smallest element of 'values' larger than 'target'."""

    assert values.shape == sort_indices.shape
    num_values, = values.shape

    # Check if the target is outside the range of 'values'.
    if target <= values[sort_indices[0]]:
        return 0
    if target >= values[sort_indices[-1]]:
        return num_values

    # Perform a binary search.
    i0 = 0
    i2 = num_values - 1
    while i2 > i0 + 1:
        i1 = (i0 + i2) // 2
        v1 = values[sort_indices[i1]]
        if v1 == target:
            return i1
        elif v1 > target:
            i2 = i1
        else:
            i0 = i1
    return i2


def findSortedIntersection(array0, array1):
    """Find the intersection of two sorted arrays.

    'array0', 'array1' -- Two sorted 'numarray' arrays.

    returns -- A 'numarray' array of elements occuring in both 'array0'
    and 'array1'."""

    n0, = array0.shape
    i0 = 0
    n1, = array1.shape
    i1 = 0

    result = []
    # Scan over the arrays simultaneously.
    while i0 < n0 and i1 < n1:
        # Look at the next element in each.
        v0 = array0[i0]
        v1 = array1[i1]
        # Are they the same?
        if v0 == v1:
            # Yes.  The item goes in the intersection.
            result.append(v0)
            i0 += 1
            i1 += 1
        else:
            # No.  Drop the smaller of the items.
            if v0 < v1:
                i0 += 1
            else:
                i1 += 1
    # Convert the result to an array.
    return array(result)
                

def selectEvents(events, sort_indices, cuts):
    """Select from 'events' those that satisfy all of 'cuts'.

    'events' -- A two-dimensional array whose rows are events.

    'sort_indices' -- Sorting indices for 'events' (see
    'makeSortArray').

    'cuts' -- A sequence of cuts.  Each is of the form '(var_index,
    sense, value)', where 'var_index' is a column index in 'events';
    'sense' is the sense of the cut, and 'value' is the cut value.

    returns -- Row indices of 'events' for events that satisfy all the
    cuts."""

    row_indices = None
    # Loop over cuts.
    for var_index, cut_sense, cut_value in cuts:
        # Find the index into the sort index array of the first element
        # that passes the cuts.
        cut_index = searchSorted(
            events[:, var_index], sort_indices[:, var_index], cut_value)
        # Construct an array of row indices for events that pass this cut.
        if cut_sense == ">":
            indices = sort_indices[cut_index :, var_index]
        else:
            indices = sort_indices[: cut_index, var_index]
        indices = sort(indices)
        # Accumulate the running intersection of row indices of events
        # that have passed all the cuts so far.
        if row_indices is None:
            row_indices = indices
        else:
            row_indices = findSortedIntersection(row_indices, indices)
            
    return row_indices


def scanCut(sig_values, bkg_values, sense):
    """Scan a cut over a single variable.

    'sig_values', 'bkg_values' -- Sequences of values of a variable for
    signal and background events.

    'sense' -- The cut sense.

    returns -- A generator over possible cuts.  For each cut, the
    generator yields '(cut_value, sig_count, bkg_count)', where
    'cut_value' is the position of the cut; and 'sig_count' and
    'bkg_count' give the number of signal and background events accepted
    by the cut, respectively."""

    epsilon = 1e-12

    # Construct sorted lists of values.
    sig_values = list(sig_values)
    sig_values.sort()
    num_sig = len(sig_values)
    bkg_values = list(bkg_values)
    bkg_values.sort()
    num_bkg = len(bkg_values)

    value = None
    # Loop over all signal and background values, in descending order.
    while sig_values or bkg_values:
        # Choose the next signal or background value, whichever is
        # next.
        if value is None:
            if not bkg_values:
                value = sig_values[-1] + 2 * epsilon
            elif not sig_values:
                value = bkg_values[-1] + 2 * epsilon
            else:
                value = max(sig_values[-1], bkg_values[-1]) + 2 * epsilon
        elif not bkg_values:
            value = _popUnique(sig_values) - epsilon
        elif not sig_values:
            value = _popUnique(bkg_values) - epsilon
        elif sig_values[-1] > bkg_values[-1]:
            value = _popUnique(sig_values) - epsilon
        else:
            value = _popUnique(bkg_values) - epsilon

        # Compute the figure of merit for the cut assuming the cut is at
        # the most recent value, using the number of signal and
        # background values we have passed.
        if sense == ">":
            sig_count = num_sig - len(sig_values)
            bkg_count = num_bkg - len(bkg_values)
        else:
            sig_count = len(sig_values)
            bkg_count = len(bkg_values)
        yield value, sig_count, bkg_count
            

def optimize(sig_values, bkg_values, sense,
             fom_fn=s_squared_over_s_plus_b):
    """Optimize a cut over a single variable.

    'sig_values', 'bkg_values' -- Sequences of values of a variable for
    signal and background events.

    'sense' -- The cut sense, either ">" or "<".

    'fom_fn' -- The figure of merit function.  This should be a function
    of the number of signal events and the number of background events.

    returns -- '(cut_value, fom)' where 'cut_value' is the position of
    the cut that maximizes the figure of merit, and 'fom' is its value
    there.""" 

    assert sense in (">", "<")
    # Track the best cut.
    best_cut = None
    best_fom = None
    # Scan over possible cuts.
    cut_iter = scanCut(sig_values, bkg_values, sense)
    for cut_value, sig_count, bkg_count in cut_iter:
        # Compute the FOM.
        fom = fom_fn(sig_count, bkg_count)
        # Keep the best cut so far.
        if best_fom is None or fom > best_fom:
            best_fom = fom
            best_cut = cut_value

    return best_cut, best_fom


def iterativeOptimize(sig_events, bkg_events, initial_cuts,
                      fom_fn=s_squared_over_s_plus_b):
    """Optimize several cuts by iteratively optimizing them individually.

    'sig_events', 'bkg_events' -- Arrays whose rows are signal and
    background events, respectively.

    'initial_cuts' -- Cuts of the form '(var_index, sense, cut_value)',
    where 'var_index' is a column index in 'sig_events' and
    'bkg_events'; 'sense' is the cut sense; and 'cut_value' is the
    initial position of the cut.

    'fom_fn' -- The figure of merit function.  This should be a function
    of the number of signal events and the number of background events.

    returns -- '(cuts, fom)', where 'cuts' is the result of optimizing
    the 'cut_value's in 'initial_cuts', and 'fom' is the best figure of
    merit."""

    num_sig, num_vars = sig_events.shape
    num_bkg, num_bkg_vars = bkg_events.shape
    if num_vars != num_bkg_vars:
        raise ValueError, "samples must have the same number of columns"

    # Set up the cuts.
    for cut in initial_cuts:
        assert cut[1] in ("<", ">")
    cuts = list(initial_cuts)
    num_cuts = len(cuts)
    # Construct sort arrays for the events.
    sort_sig = makeSortArray(sig_events)
    sort_bkg = makeSortArray(bkg_events)

    # The best FOM so far.
    best_fom = None
    # The FOM at the end of the previous iteration.
    last_fom = None
    # Keep going as long as the FOM improves.
    while last_fom is None or best_fom > last_fom:
        last_fom = best_fom
        # Loop over the cuts in random order.
        cut_indices = range(num_cuts)
        random.shuffle(cut_indices)
        for cut_index in cut_indices:
            # Consider this cut.
            var_index, cut_sense, cut_value = cuts[cut_index]
            # Select all signal and background events that pass all cuts,
            # with the cut under consideration excluded.
            other_cuts = cuts[: cut_index] + cuts[cut_index + 1 :]
            cut_sig_rows = selectEvents(sig_events, sort_sig, other_cuts)
            cut_bkg_rows = selectEvents(bkg_events, sort_bkg, other_cuts)
            # Construct lists of the values of the variable to optimize,
            # after the other cuts have been applied.
            cut_sig_values = \
                take(sig_events[:, var_index], cut_sig_rows)
            cut_bkg_values = \
                take(bkg_events[:, var_index], cut_bkg_rows)
            if len(cut_sig_values) == 0 and len(cut_bkg_values) == 0:
                # No events pass the remaining cuts.
                continue
            # Optimize this cut.
            new_cut, new_fom = optimize(cut_sig_values, cut_bkg_values,
                                        cut_sense, fom_fn=fom_fn)
            # Use the new optimum cut value.
            cuts[cut_index] = (var_index, cut_sense, new_cut)
            # The result of optimizing one cut while holding the others
            # at their current positions should never yield a worse FOM.
            assert best_fom is None or new_fom >= best_fom
            # Go with it.
            best_fom = new_fom

    return cuts, best_fom
    

def makeFOMCurve(sig_values, bkg_values, sense,
                 fom_fn=s_squared_over_s_plus_b):
    """Return a 'Function1D' object for the FOM for a cut."""

    # Build the function object.
    lo = min(min(sig_values), min(bkg_values))
    hi = max(max(sig_values), max(bkg_values))
    fom_curve = hep.hist.SampledFunction1D(
        (float, "cut value", "", (lo, hi)), name="F.O.M.")
    # Scan over cut values, filling it in.
    cut_iter = scanCut(sig_values, bkg_values, sense)
    for cut_value, sig_count, bkg_count in cut_iter:
        fom_curve.addSample(cut_value, fom_fn(sig_count, bkg_count))

    return fom_curve


def makeFOMCurves(sig_events, bkg_events, cuts,
                  fom_fn=s_squared_over_s_plus_b):
    """Return 'Function1D' objects for a set of cuts.

    returns -- A sequence of 'Function1D' objects containing the FOM as
    a function of cut value for each cut in 'cuts', where all the other
    cuts have been applied."""

    result = []

    sort_sig = makeSortArray(sig_events)
    sort_bkg = makeSortArray(bkg_events)

    for cut_index in range(len(cuts)):
        var_index, cut_sense, cut_value = cuts[cut_index]
        # Select all signal and background events that pass all cuts,
        # with the cut under consideration excluded.
        other_cuts = cuts[: cut_index] + cuts[cut_index + 1 :]
        cut_sig_rows = selectEvents(sig_events, sort_sig, other_cuts)
        cut_bkg_rows = selectEvents(bkg_events, sort_bkg, other_cuts)
        # Construct lists of the values of the variable to optimize,
        # after the other cuts have been applied.
        cut_sig_values = take(sig_events[:, var_index], cut_sig_rows)
        cut_bkg_values = take(bkg_events[:, var_index], cut_bkg_rows)
        # Find the FOM function.
        result.append(makeFOMCurve(cut_sig_values, cut_bkg_values,
                                   cut_sense, fom_fn))

    return result

        
def efficiencyFromHist(histogram, sense):
    """Compute an efficiency function from a histogram.

    Constructs a function esimating the efficiency of cutting on the
    distribution sampled by 'histogram'.  The efficiency function is
    sampled at the edge of each bin of the histogram.  The underflow and
    overflow bins are included in the efficiency calculation.

    'histogram' -- A one-dimensional histogram, with non-zero integral.

    'sense' -- The sense of a cut.  If '">"', the cut is a minimum cut,
    i.e. at each value, the resulting function gives the efficiency of
    selecting larger values.  If '"<"', the cut is a maximum cut.

    returns -- A function object."""

    if sense not in ("<", ">"):
        raise ValueError, "'sense' must be \">\" or \"<\""

    # Integrate the histogram.  This is the denominator for
    # efficiencies. 
    integral = hep.hist.integrate(histogram, overflows=True)
    if integral == 0:
        raise ValueError, "histogram integral is zero"

    # Construct the efficiency function.
    axis = histogram.axis
    name = getattr(axis, "name", "value")
    units = getattr(axis, "units", "")
    function = hep.hist.SampledFunction1D(
        (float, "%s cut" % name, units, axis.range, "efficiency"))

    # For a ">" cut, we scan over bins in ascending order; for a "<"
    # cut, descending.
    bin_numbers = list(
        hep.hist.AxisIterator(axis, overflows=True))
    if sense == "<":
        bin_numbers.reverse()

    # Now scan over bins.  We don't need the last one, which is the
    # overflow bin for a ">" cut, the underflow bin for a "<" cut.
    total = 0
    for bin_number in bin_numbers[: -1]:
        total += histogram.getBinContent(bin_number)
        # Use the upper edge of the bin we just included for a ">" cut,
        # the lower edge for a "<" cut.
        if sense == ">":
            value = axis.getBinRange(bin_number)[1]
        else:
            value = axis.getBinRange(bin_number)[0]
        assert value is not None
        # Store the efficiency up to and including this bin.
        efficiency = (integral - total) / integral
        function.addSample(value, efficiency)

    return function


def fomFromHists(sg_hist, bg_hist, min_count=0):
    if sg_hist.axis.range != bg_hist.axis.range \
       or sg_hist.axis.number_of_bins != bg_hist.axis.number_of_bins:
        raise TypeError, "histogram axes are not compatible"
    axis = sg_hist.axis

    result = hep.hist.Histogram(sg_hist.axis, bin_type=float,
                                error_model="symmetric")

    s = 0
    se2 = 0
    b = 0
    be2 = 0
    
    max_fom = None
    max_fom_err = None
    max_cut = None

    bin_numbers = list(hep.hist.AxisIterator(sg_hist.axis))
    bin_numbers.reverse()
    for bin_number in bin_numbers:
        s += sg_hist.getBinContent(bin_number)
        se2 += sg_hist.getBinError(bin_number)[1] ** 2
        b += bg_hist.getBinContent(bin_number)
        be2 += bg_hist.getBinError(bin_number)[1] ** 2

        if s + b <= 0 or s + b < min_count:
            fom = 0
            fom_err = 0
        else:
            fom = s ** 2 / (s + b)
            fom_err = s / (s + b) ** 2 \
                      * sqrt(((s + 2 * b) ** 2) * se2 + (s ** 2) * be2)
        cut = axis.getBinCenter(bin_number)
        result.setBinContent(bin_number, fom)
        result.setBinError(bin_number, fom_err)

        if max_fom is None or fom > max_fom:
            max_fom = fom
            max_fom_err = fom_err
            max_cut = cut

    return result, (max_fom, max_fom_err, max_cut)


