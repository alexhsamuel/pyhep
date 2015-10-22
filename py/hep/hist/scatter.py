#-----------------------------------------------------------------------
#
# scatter.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Scatter distribution class."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   axis import *
import copy_reg
from   hep.bool import *
import hep.ext

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

# This all-Python implementation is used when the extension type does
# not support the specified axis types.

class _Scatter(object):
    """A sampling of a bivariate distribution.

    A 'Scatter' consists of '(x, y)' pairs sampled from a bivariate
    joint distribution.

    These attributes are provided:

    'axes' -- A '(x_axis, y_axis)' sequence containing the axis objects.

    'points' -- A sequence of '(x, y)' coordinate pairs of samplings of
    the distribution.  The order of the points is unimportant."""

    def __init__(self, x_axis, y_axis):
        """Create a new 'Scatter' object.

        'x_axis', 'y_axis' -- Specification for the two axes.  Each may
        be an 'Axis' object; or may be a tuple '(type, name, units)',
        where 'name' and 'units' may be omitted.  If an axis
        specification is omitted, a 'float' axis is assumed."""

        self.axes = (x_axis, y_axis, )
        self.points = []


    def __str__(self):
        return "Scatter(x_axis.type=%s, y_axis.type=%s)" \
               % (self.axes[0].type, self.axes[1].type)


    def accumulate(self, values):
        """Add a sampling of the distribution.

        'values' -- An '(x, y)' pair."""

        self.points.append(self.coerce(values))


    def coerce(self, values):
        x, y = values
        x_axis, y_axis = self.axes
        return ( x_axis.type(x), y_axis.type(y) )
        

    def __lshift__(self, values):
        """A synonym for 'accumulate'."""

        self.accumulate(values)


    def __get_range(self):
        # Handle the case of an empty scatter plot.
        if len(self.points) == 0:
            # Return zeros.
            x0, y0 = self.coerce((0, 0))
            return x0, x0, y0, y0

        points_iter = iter(self.points)
        x_min, y_min = points_iter.next()
        x_max, y_max = x_min, y_min
        for x, y in points_iter:
            if x < x_min:
                x_min = x
            elif x > x_max:
                x_max = x
            if y < y_min:
                y_min = y
            elif y > y_max:
                y_max = y

        return (x_min, x_max), (y_min, y_max)


    range = property(__get_range)


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def isScatter(object):
    """Return true if 'object' is a 'Scatter' object."""

    return type(object) in (_Scatter, hep.ext.Scatter, )


def Scatter(x_axis=Axis(float), y_axis=Axis(float), **kw_args):
    """A scatter distribution.

    A 'Scatter' is a sampling from a bivariant distribution which stores
    the exact (x, y) coordinate values of each sample.  There is no
    binning or other approximation, and the range on the coordinates is
    not fixed.

    Note that the memory use of a 'Scatter' object increases in
    proportion to the number of sample points stored in it.

    'x_axis' -- An 'Axis' object describing the x coordinate values, or
    a tuple '(type, name, units)' (the 'name' and 'units' are optional).

    'y_axis' -- An 'Axis' object describing the y coordinate values, or
    a tuple '(type, name, units)' (the 'name' and 'units' are optional).

    '*kw_args' -- Additional keyword arguments to be set as attributes
    on the returned 'Scatter' object."""

    # Handle sloppy axis arguments.
    x_axis = parseAxisArg(x_axis)
    y_axis = parseAxisArg(y_axis)

    # Try to use the extension type.
    try:
        scatter = hep.ext.Scatter(x_axis, y_axis)
    except NotImplementedError:
        # The extension type doesn't support the axis types.  Use the
        # Python implementation instead.
        scatter = _Scatter(x_axis, y_axis)
    # Install keyword arguments as attributes.
    scatter.__dict__.update(kw_args)
    # All done.
    return scatter


def _reduce(scatter):
    """Reduce a 'Scatter' object for pickling.

    Reduces instance of 'Scatter' extension types, as required for the
    standard 'copy_reg' facility."""

    # FIXME: If/when we can pickle 'array' objects, use one here instead
    # of a list.
    points = list(scatter.points)
    # Collect all the stuff we will need to restore the histogram's
    # state. 
    state = (scatter.axes,
             points,
             scatter.__dict__, )
    return _reconstitute, state


def _reconstitute(axes, points, attributes):
    """Rebuild a 'Scatter' from pickled state."""

    scatter = Scatter(*axes, **attributes)
    map(scatter.accumulate, points)
    return scatter


# Mark this constructor function as safe for use in unpickling.
_reconstitute.__safe_for_unpickling__ = True


#-----------------------------------------------------------------------
# configuration
#-----------------------------------------------------------------------

# Register the extension type with 'copy_reg' so that instances of it
# may be pickled.
copy_reg.pickle(hep.ext.Scatter, _reduce)


