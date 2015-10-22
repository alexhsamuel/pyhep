#-----------------------------------------------------------------------
#
# module histogram
#
# Copyright 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Implementation of histogram classes."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import array
from   axis import *
import copy_reg
import hep.ext
import hep.py
import math

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

_error_models = (
    "asymmetric",
    "gaussian",
    "none",
    "poisson",
    "symmetric",
    )

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class _Histogram:
    """An N-dimensional histogram with evenly-binned axes.

    A 'Histogram' is a histogram in one or more dimensions.  The axis in
    each dimension may have different range, binnning, and type.
    Underflow and overflow bins are included for each dimension."""

    def __init__(self, axes, bin_type, error_model):
        """Create a new binned histogram.

        'axes' -- A sequence containing axes for the histogram.  The
        number of axis elements is the number of dimensions of the
        histogram.  Each element is an 'BinnedAxis' instance.

        'bin_type' -- The type used to store bin contents.

        'error_model' -- The error model to use.""" 

        # Get and check the number of dimensions.
        dimensions = len(axes)
        if dimensions == 0:
            raise ValueError, "at least one axis must be specified"

        # Make sure the error model is recognized.
        error_model = str(error_model)
        if error_model not in _error_models:
            raise ValueError, "unknown error model %r" % error_model

        # Compute the number of bins required to store bin contents.
        num_bins = reduce(
            lambda n, axis: n * (axis.number_of_bins + 2), axes, 1)

        # Save stuff.
        self.__axes = axes
        self.__bin_type = bin_type
        self.__error_model = error_model
        self.__num_bins = num_bins

        # Construct arrays for the bin contents and errors.
        zero = bin_type(0)
        self.__bins = num_bins * [ zero ] 
        # Use an 'array' object if possible.
        type_code = hep.py.getTypeCode(bin_type)
        if type_code is not None:
            self.__bins = array.array(type_code, self.__bins)

        # Likewise for the squared errors, if we're collecting
        # quadrature errors.  Always use floats for bin errors.
        if error_model == "asymmetric":
            self.__lo_errors = array.array('d', num_bins * [ 0.0 ])
            self.__hi_errors = array.array('d', num_bins * [ 0.0 ])
        elif error_model == "symmetric":
            self.__errors = array.array('d', num_bins * [ 0.0 ])

        # Initialize things.
        self.__number_of_samples = 0


    def __repr__(self):
        return "Histogram(%s, bin_type=%s)" \
               % (", ".join(map(str, self.__axes)),
                  self.__bin_type.__name__)


    dimensions = property(lambda self: len(self.__axes))
    """The number of axis dimensions."""


    axes = property(lambda self: self.__axes)
    """A sequence of 'BinnedAxis' instaces describing the axes."""


    number_of_samples = property(lambda self: self.__number_of_samples)
    """The number of times an entry has been accumulated."""


    bin_type = property(lambda self: self.__bin_type)
    """The type used to represent the content of a bin."""


    error_model = property(lambda self: self.__error_model)
    """The model used to determine bin errors."""


    def accumulate(self, coordinates, weight=1):
        """Add to the content of the bin corresponding to 'coordinates'.

        'coordinates' -- A sequence of coordinates along the axes of the
        histogram.

        'weight' -- The amount to add to the bin content."""

        weight = self.__bin_type(weight)
        bin_index = self._getIndexForCoordinates(coordinates)
        # Accumulate bin content.
        self.__bins[bin_index] += weight
        # Accumulate the sum of squares of weights.
        if self.__error_model == "symmetric":
            self.__errors[bin_index] += weight * weight
        elif self.__error_model == "asymmetric":
            self.__lo_errors[bin_index] += weight * weight
            self.__hi_errors[bin_index] += weight * weight
        # Maintain number of entries.
        self.__number_of_samples += 1


    def __lshift__(self, coordinates):
        self.accumulate(coordinates, weight=1)


    def getBinContent(self, bin_numbers):
        """Return the accumulated weight contained in a bin.

        'bin_numbers' -- A sequence of bin numbers for the axes of the
        histogram."""

        bin_index = self._getIndexForBinNumbers(bin_numbers)
        return self.__bins[bin_index]


    def setBinContent(self, bin_numbers, bin_content):
        """Set the weight contained in a bin.

        'bin_numbers' -- A sequence of bin numbers for the axes of the
        histogram."""

        bin_content = self.__bin_type(bin_content)
        bin_index = self._getIndexForBinNumbers(bin_numbers)
        self.__bins[bin_index] = bin_content


    def setBinError(self, bin_numbers, bin_error):
        if self.__error_model in ("symmetric", "asymmetric"):
            try:
                lo, hi = bin_error
            except TypeError:
                lo = bin_error
                hi = bin_error
            lo = abs(float(lo))
            hi = abs(float(hi))
            bin_index = self._getIndexForBinNumbers(bin_numbers)
            # Store the square of the provided error values.
            if self.__error_model == "asymmetric":
                self.__lo_errors[bin_index] = lo * lo
                self.__hi_errors[bin_index] = hi * hi
            elif self.__error_model == "symmetric":
                error = max(abs(float(lo)) * abs(float(hi)))
                self.__errors[bin_index] = error * error
        else:
            # The bin error may not be set explicitly with other models.
            raise RuntimeError, \
                  "cannot set errors with error model %r" \
                  % self.__error_model


    def getBinError(self, bin_numbers):
        """Return the error on the content of a bin.

        'bin_numbers' -- A sequence of bin numbers for the axes of the
        histogram."""

        if self.__error_model == "none":
            # No errors.
            return (0.0, 0.0)
        elif self.__error_model == "asymmetric":
            bin_index = self._getIndexForBinNumbers(bin_numbers)
            return (math.sqrt(self.__lo_errors[bin_index]),
                    math.sqrt(self.__hi_errors[bin_index]))
        elif self.__error_model == "symmetric":
            # Return the square root of the sum of weights squared.
            bin_index = self._getIndexForBinNumbers(bin_numbers)
            error = math.sqrt(self.__errors[bin_index])
            return (error, error)
        elif self.__error_model == "poisson":
            value = int(abs(self.__bins[bin_index]))
            print hep.ext.getPoissonErrors(value)
            return hep.ext.getPoissonErrors(value)
        elif self.__error_model == "gaussian":
            bin_index = self._getIndexForBinNumbers(bin_numbers)
            error = math.sqrt(abs(self.__bins[bin_index]))
            return (error, error)


    def getBinRange(self, bin_numbers):
        """Return the range of coordinates corresponding to a bin.

        'bin_numbers' -- A sequence of bin numbers for the axes of the
        histogram.

        returns -- A sequence of '(min, max)' pairs specifying the
        coordinate range of the specified bin along each axis."""

        return map(lambda (number, axis): axis.getBinRange(number),
                   zip(bin_numbers, self.__axes))


    def map(self, coordinates):
        """Return the bin numbers of the bin corresponding to 'coordinates'."""

        try:
            if len(coordinates) != self.dimensions:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError, "a value must be a sequence of %d items" \
                  % self.dimensions

        # Convert 'coordinates' to bin numbers.
        return [ a(c) for (a, c) in zip(self.__axes, coordinates) ]


    def __rmul__(self, constant):
        import util
        return util.scale(self, constant)


    def __rdiv__(self, constant):
        import util
        return util.scale(self, 1 / constant)


    def __add__(self, other):
        import util
        return util.add(self, other)


    def __sub__(self, other):
        import util
        return util.add(self, other, scale2=-1)


    def _getIndexForCoordinates(self, coordinates):
        """Return the index of the bin corresponding to 'coordinates'."""

        # Get the corresponding bin index.
        return self._getIndexForBinNumbers(self.map(coordinates))


    def _getIndexForBinNumbers(self, bin_numbers):
        """Return the index of the bin specified by 'bin_numbers'."""

        try:
            if len(bin_numbers) != self.dimensions:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError, "a value must be a sequence of %d items" \
                  % self.dimensions
        
        index = 0
        # Loop over axes.
        for bin_number, axis in zip(bin_numbers, self.__axes):
            num_bins = axis.number_of_bins
            # Find the bin number along this axis.
            if bin_number == "underflow":
                # Underflow bin is stored first.
                bin_index = 0
            elif bin_number == "overflow":
                # Overflow bin is stored last.
                bin_index = num_bins + 1
            else:
                try:
                    bin_number = int(bin_number)
                    if bin_number < 0 or bin_number >= num_bins:
                        raise ValueError
                except ValueError:
                    raise ValueError, \
                       "bin number must be between 0 and %d" % num_bins
                # Bin index is one more than the bin number.
                bin_index = bin_number + 1
            # Compute the overall bin index so far, in column-major (?)
            # order. 
            index = index * (num_bins + 2) + bin_index
        assert(index >= 0 and index < len(self.__bins))
        return index


                
#-----------------------------------------------------------------------

class _Histogram1D(_Histogram):
    """A one-dimensional evenly-binned histogram.

    This class is a convenience subclass of '_Histogram' for
    one-dimensional histograms.  Coordinates and bin numbers may be
    specified as individual values rather than (one-element)
    sequences."""


    axis = property(lambda self: self.axes[0])


    def accumulate(self, coordinates, weight=1):
        return _Histogram.accumulate(self, wrap1D(coordinates), weight)


    def __lshift__(self, coordinates):
        return _Histogram.__lshift__(self, wrap1D(coordinates))


    def getBinContent(self, bin_numbers):
        return _Histogram.getBinContent(self, wrap1D(bin_numbers))

        
    def setBinContent(self, bin_numbers, content):
        return _Histogram.setBinContent(self, wrap1D(bin_numbers), content)


    def getBinError(self, bin_numbers):
        return _Histogram.getBinError(self, wrap1D(bin_numbers))

        
    def setBinError(self, bin_numbers, error):
        return _Histogram.setBinError(self, wrap1D(bin_numbers), error)


    def getBinRange(self, bin_numbers):
        return _Histogram.getBinRange(self, wrap1D(bin_numbers))

        
    def map(self, coordinates):
        return _Histogram.map(self, wrap1D(coordinates))



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def Histogram(*axes, **kw_args):
    """Create a histogram with one or more evenly-binned axes.

    '*axes' -- The axes of the histogram.  The number of axis
    arguments is the number of dimensions of the histogram.

    Each axis argument may be,

      * A 'BinnedAxis' instance.

      * A sequence of the form '(num_bins, min, max, axis_type)', where
        'num_bins' is the number of bins in that dimension (not
        including overflow and underflow bins), '(min, max)' is a pair
        specifying the range of coordinates, and 'axis_type' is the type
        used to represent coordinate values in that dimension.
        Optionally, 'axis_type' may be omitted, in which case it is
        inferred from the types of 'min' and 'max'.

    '**kw_args' -- Additional keyword arguments to add as instance
    attributes.

    The type used to store bin contents may be specified by the
    'bin_type' keyword argument; otherwise, 'int' is assumed."""

    # Get and check the number of dimensions.
    dimensions = len(axes)
    if dimensions == 0:
        raise ValueError, "at least one axis must be specified"
    # Process the list of axes.
    axes_list = map(parseBinnedAxisArg, axes)
    assert len(axes_list) == dimensions

    # Get the bin type from a keyword argument, or assume 'float'.
    try:
        bin_type = kw_args["bin_type"]
        del kw_args["bin_type"]
    except KeyError:
        bin_type = int
    # Make sure the bin type is a numerical type.
    try:
        if bin_type(0) != 0:
            raise ValueError
    except ValueError:
        raise ValueError, "'bin_type' must be a numerical type"

    # Get the error model from a keyword argument, or assume 'poisson'.
    try:
        error_model = kw_args["error_model"]
        del kw_args["error_model"]
    except KeyError:
        if bin_type in (int, long):
            error_model = "poisson"
        else:
            error_model = "gaussian"

    result = None
    # Try to create an extension type instance for this histogram.
    try:
        # FIXME: This is so we can unpickle old histogram objects.  It
        # should be removed.
        for axis in axes_list:
            if hasattr(axis, "_EvenlyBinnedAxis__max"):
                axis._EvenlyBinnedAxis__range = (
                    axis._EvenlyBinnedAxis__min,
                    axis._EvenlyBinnedAxis__max)
                del axis._EvenlyBinnedAxis__min
                del axis._EvenlyBinnedAxis__max

        if dimensions == 1:
            result = hep.ext.Histogram1D(axes_list, bin_type, error_model)
        elif dimensions == 2:
            result = hep.ext.Histogram2D(axes_list, bin_type, error_model)
    except NotImplementedError:
        # That's OK.  Fall through to use the Python implementation.
        pass

    if result is None:
        # No extension type is available.  Use the Python
        # implementation. 
        if dimensions == 1:
            result = _Histogram1D(axes_list, bin_type, error_model)
        else:
            result = _Histogram(axes_list, bin_type, error_model)

    # Set any additional keyword arguments that were specified.
    result.__dict__.update(kw_args)

    # All done.
    return result


def Histogram1D(*axis, **kw_args):
    """Create a one-dimensional histogram.

      'Histogram1D(num_bins, lo, hi, type, name, units, **kw_args)'

    is simply an abbreviation for

      'Histogram((num_bins, lo, hi, type, name, units), **kw_args)'.

    As with the expanded form, 'type', 'name', and 'units' may be
    omitted."""

    return Histogram(axis, **kw_args)


def isHistogram(object):
    """Return true if 'object' is a histogram instance."""

    return isinstance(object, _Histogram) \
           or isinstance(object, hep.ext.Histogram1D) \
           or isinstance(object, hep.ext.Histogram2D)


def _reduce(histogram):
    """Reduce a histogram for pickling.

    Reduces histograms, including instances of histogram extension
    types, as required for the standard 'copy_reg' facility."""

    # FIXME: If/when we can pickle 'array' objects, use one here instead
    # of a list.
    bin_contents = [ histogram.getBinContent(bin)
                     for bin in AxesIterator(histogram.axes, True) ]
    if histogram.error_model in ("symmetric", "asymmetric"):
        bin_errors = [ histogram.getBinError(bin)
                       for bin in AxesIterator(histogram.axes, True) ]
    else:
        bin_errors = None
    # Collect all the stuff we will need to restore the histogram's
    # state. 
    state = (
        histogram.axes,
        histogram.bin_type,
        histogram.error_model,
        histogram.number_of_samples,
        bin_contents,
        bin_errors,
        histogram.__dict__, )
    return _reconstitute, state


def _reconstitute(axes, bin_type, error_model, number_of_samples,
                  bin_contents, bin_errors, attributes):
    """Rebuild a histogram from pickled state."""

    # Build the histogram.
    histogram = Histogram(
        bin_type=bin_type, error_model=error_model, *axes)
    # Restore its data.
    histogram.number_of_samples = number_of_samples
    value_iter = iter(bin_contents)
    if bin_errors is not None:
        error_iter = iter(bin_errors)
    else:
        error_iter = None
    for bin in AxesIterator(axes, True):
        histogram.setBinContent(bin, value_iter.next())
        if error_iter is not None:
            histogram.setBinError(bin, error_iter.next())
    # Restore other attributes.
    histogram.__dict__.update(attributes)
    # All done.
    return histogram
    

# Mark this constructor function as safe for use in unpickling.
_reconstitute.__safe_for_unpickling__ = True


#-----------------------------------------------------------------------
# configuration
#-----------------------------------------------------------------------

# Register the histogram extension types with 'copy_reg' so that they
# may be pickled.
copy_reg.pickle(hep.ext.Histogram1D, _reduce)
copy_reg.pickle(hep.ext.Histogram2D, _reduce)
