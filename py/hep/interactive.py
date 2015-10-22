#-----------------------------------------------------------------------
#
# interactive.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
# 
#-----------------------------------------------------------------------

"""Interactive PyHEP.

These global variables are available in interactive PyHEP:

  'iwin' -- The draw object (see 'hep.draw') for the window in which
  interactive plots are displayed.  'None' if no window is currently
  shown.

  'i_zone' -- The draw object for the plot zone of the most recent
  plot.  See 'idivide()' and 'iselect()'.

  'ifig' -- The 'hep.hist.plot.Plot' object (see 'hep.hist.plot') for
  the most recent plot.

  'cwd' -- A 'Directory' object for the current working directory (see
  'hep.fs').

Further, consult the help documentation for the following interactive
functions: 'ihelp()', 'idivide()', 'iselect()', 'iplot()', 'iredraw()',
'iprint()', 'iproject()', 'idump()', 'icram()'.
"""

# The contents of this file are executed in the Python interpreter for
# an interactive PyHEP session, usually via the PYTHONSTARTUP
# environment variable.  Thus, all names in this module are defined in
# interactive global namespace.

# FIXME: Instead of that, insert names into '__main__.__dict__'.  But
# this might cause problems for the global variables 'iwin', etc., which
# should not be shared.

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division
from __future__ import generators

import copy
from   hep.bool import *
import hep.draw
from   hep.draw import Color, Gray, HSV, inch, point
from   hep.draw import Line, Polygon, Symbol, Text, Markers
from   hep.draw import GridLayout, BrickLayout, SplitLayout
import hep.draw.xwindow
import hep.draw.postscript
import hep.expr
import hep.fn
import hep.fs
from   hep.hist import Histogram, Histogram1D, Scatter
from   hep.hist import ezplot
import hep.hist.plot
from   hep.lorentz import lab
from   hep.num import *
from   hep.pdt import default as pdt
import hep.py
from   math import *
import os
import sys

#-----------------------------------------------------------------------
# script
#-----------------------------------------------------------------------

if hep.py.is_interactive:
    # Print who we are.
    import hep.config
    print "PyHEP version %s in %s." \
          % (hep.config.version, hep.config.base_dir)

    # Invoke the interactive startup script in this directory, if any.
    if os.path.isfile(".interactive.py"):
        execfile(".interactive.py")

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

# Colors.
globals().update(hep.draw.colors)

#-----------------------------------------------------------------------
# global state
#-----------------------------------------------------------------------

iwin = None
ifig = None
iborder = 0.01

cwd = hep.fs.getdir(".")

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def __setupWindow():
    """Set up for drawing plots.

    After calling this function, 'iwin' is set to the drawing
    window."""

    global iwin

    if iwin is None:
        layout = GridLayout(1, 1, border=iborder)
        vx, vy = 0.20, 0.12
        wx, wy = 0.30, 0.18
        iwin = hep.draw.xwindow.FigureWindow(layout, (wx, wy), (vx, vy))
        iwin.title = "Interactive PyHEP"
        # Start with the first cell.
        layout.__position = (0, 0)
        # Flag that we shouldn't advance one cell the next time
        # something is drawn.
        layout.__do_not_advance = True


def __nextFigure():
    global ifig
    global iwin

    # Get the layout.
    if not isinstance(iwin.figure, BrickLayout):
        raise RuntimeError, "window is not showing a layout"
    layout = iwin.figure

    # Has this layout been flagged not to advance a cell?
    if layout.__do_not_advance:
        # Yes.  Clear the flag and don't advance.
        layout.__do_not_advance = False
        return
    
    # Get the current row and column.  
    column, row = layout.__position
    # Compute the next cell's coordinates.
    column += 1
    if column >= layout.rows[row]:
        column = 0
        row += 1
        if row >= len(layout.rows):
            row = 0
    # Set the new position.
    layout.__position = (column, row)
    ifig = layout[column, row]


def ihelp():
    """Print help for interactive PyHEP."""
    
    global __doc__

    print __doc__


def iresize(page_size):
    global iwin

    vrt_width, vrt_height = hep.draw.parsePageSize(page_size)

    # Make sure we have a window.
    __setupWindow()
    # Get the physical size of the screen.
    scr_width, scr_height = hep.draw.xwindow.screen_size
    # Does the virtual size fit on the screen?
    if vrt_width > scr_width or vrt_height > scr_height:
        # No.  Scale it down so that it occupies 80% of the screen width
        # or height.
        scale = 0.8 * min(scr_width / vrt_width, scr_height / vrt_height)
        win_width, win_height = vrt_width * scale, vrt_height * scale
    else:
        # Yes.  Use the virtual size as the window size.
        win_width, win_height = vrt_width, vrt_height

    iwin.resize((win_width, win_height))
    iwin.virtual_size = vrt_width, vrt_height
    print win_width/win_height, vrt_width/vrt_height
    iwin.redraw()


def ibricks(*rows, **style):
    global iwin
    
    for num_columns in rows:
        if num_columns < 1:
            raise ValueError, "columns must be positive"

    # Make sure we have a window.
    __setupWindow()
    # Set up the layout.
    style.setdefault("border", iborder)
    layout = BrickLayout(rows, **style)
    layout.__position = (0, 0)
    iwin.figure = layout
    iwin.figure.__do_not_advance = True


def igrid(columns, rows, **style):
    """Divide the plot window into a grid of plot zones.

    The window is cleared and the upper-left zone selected.

    'columns', 'rows' -- The number of rows and columns into which to
    divide the window."""

    global iwin

    # Check arguments.
    if columns < 1 or rows < 1:
        raise ValueError, "'rows' and 'columns' must be positive"

    # Make sure we have a window.
    __setupWindow()
    # Set up the grid.
    style.setdefault("border", iborder)
    iwin.figure = GridLayout(columns, rows, **style)
    iwin.figure.__position = (0, 0)
    iwin.figure.__do_not_advance = True


def iselect(column, row):
    """Select a plot zone in the plot window."""

    global ifig
    global iwin

    # Make sure we have a window.
    __setupWindow()
    # Get the layout.
    if not isinstance(iwin.figure, BrickLayout):
        raise RuntimeError, "window is not showing a layout"
    layout = iwin.figure
    # Validate arguments.
    if row >= len(layout.rows):
        raise ValueError, "row number out of range"
    if column >= layout.rows[row]:
        raise ValueError, "column number out of range"

    # Select the cell and its figure.
    layout.__position = (column, row)
    ifig = layout[column, row]
    # Flag that we should not advance a cell the next time somethign is
    # drawn. 
    layout.__do_not_advance = True


def ishow(figure):
    global ifig
    global iwin

    # Make sure we have a window.
    __setupWindow()
    # Advance to the next cell.
    __nextFigure()
    # Show it.
    layout = iwin.figure
    column, row = layout.__position
    layout[column, row] = figure
    ifig = figure


class __IStyle(dict):
    """Default style for interactive plots."""

    def __styles(self):
        global iwin
        if not hasattr(iwin, "figure") \
           or not hasattr(iwin.figure, "figures"):
            # The window is not showing a layout.  Don't do anything.
            return

        for figure in iwin.figure.figures:
            if hasattr(figure, "style"):
                yield figure.style


    def delall(self, key):
        """Remove 'key' from the default style and all figures."""

        if key in self:
            del self[key]
        for style in self.__styles():
            if key in style:
                del style[key]


    def setall(self, key, value):
        """Set 'key' to 'value' in the default style and all figures."""

        self[key] = value
        for style in self.__styles():
            style[key] = value



istyle = __IStyle()


def _convertDataForPlot(data, **kw_args):
    normalize = kw_args.get("normalize", None)

    # What is it?
    if hep.hist.isHistogram(data):
        # If normalization was specified, apply it.
        if normalize is not None:
            data = hep.hist.normalize(data, normalization=normalize)
    elif hep.hist.isScatter(data) \
         or hep.hist.isFunction(data):
        # The plot can handle these directly.
        pass
    elif hep.expr.isExpression(data) \
         or isinstance(data, str) \
         or callable(data):
        # It looks like something to plot as a function.  Convert it to
        # an expression. 
        data = hep.expr.asExpression(data)
        # Wrap the expression in an expression function.
        data = hep.hist.Function1D(data)
    else:
        raise TypeError, "don't know how to plot %s" % repr(data)

    return data


def iplot(*data_args, **kw_args):
    """Plot with the current style.

    Sets 'ifig' to the produced 'Plot' object.

    '*data_args' -- The data to plot.  Pass '1' or '2' to make an empty
    one- or two-dimensional plot.

    'normalize' (keyword argument) -- Normalize histograms to this
    value.

    'statistics' (keyword argument) -- If provided, display statistics.
    The value is a list of statistic names.

    '**kw_args' -- Additional style attributes with which to override
    the current style.  The style is applied to the new plot object."""
    
    global ifig
    global istyle
    global iwin
    
    if len(data_args) == 0:
        # Nothing to do.
        return

    # If there is a single numerical positional argument, treat it as
    # the number of dimensions for an empty plot.
    if len(data_args) == 1 and isinstance(data_args[0], int):
        dimensions = data_args[0]
        if dimensions not in (1, 2):
            raise ValueError, \
                  "%d-dimensional plots not supported" % dimensions
        series_data = []
    # Otherwise, interpret positional arguments as data items to plot. 
    else:
        # Perform some convenience conversions of data objects.
        series_data = [ _convertDataForPlot(d, **kw_args)
                        for d in data_args ]
        dimensions = series_data[0].dimensions
        # Make sure all have the same number of dimensions.
        for data in series_data[1 :]:
            if data.dimensions != dimensions:
                raise ValueError, "data have different dimensionality"

    # Make sure we have a window to draw to.
    __setupWindow()
    
    # Construct a style, starting with the default style and adding any
    # unused keyword arguments.
    statistics = hep.popkey(kw_args, "statistics", None)
    style = dict(istyle)
    style.update(kw_args)

    # Make the new plot.
    plot = hep.hist.plot.Plot(dimensions, **style)
    # Add in the data.
    for data in series_data:
        plot.append(data)
    # Show the plot.
    ishow(plot)

    if statistics is not None:
        ifig.append(hep.hist.plot.Statistics(statistics, *series_data))

    
def iseries(*data_args, **kw_args):
    global ifig
    global istyle
    global iwin

    # Perform some convenience conversions of data objects.
    series_data = [ _convertDataForPlot(d, **kw_args)
                    for d in data_args ]
    if len(series_data) == 0:
        return

    # Make sure there is a plot.
    if not isinstance(ifig, hep.hist.plot.Plot):
        raise RuntimeError, "figure is not a plot"
    dimensions = ifig.dimensions

    # Construct a style, starting with the default style and adding any
    # unused keyword arguments.
    statistics = hep.popkey(kw_args, "statistics", None)
    style = dict(istyle)
    style.update(kw_args)

    for data in series_data:
        # Make sure the existing plot has the right number of
        # dimensions.
        if dimensions != data.dimensions:
            raise ValueError, \
                  "data is %d-dimensional, plot is %d-dimensional" \
                  % (data.dimensions, dimensions)
        # Add a series to the current plot.
        ifig.append(data, **style)
    
    if statistics is not None:
        ifig.append(hep.hist.plot.Statistics(statistics, *series_data))


def iprint(file_name, size=None, page_size=None, border=None):
    """Print the current plot window to a file.

    'file_name' -- The name of the output file.  The format of the output
    file is inferred from its extension.

    Supported output formats:

      '.ps' -- One-page PostScript file (8.5 by 11 inches)

      '.eps' -- Encapsulated PostScript file

    """
    
    global iwin
    
    if size is None:
        size = iwin.virtual_size

    if file_name.endswith(".ps"):
        if page_size is None:
            page_size = "letter"
        page_size = hep.draw.parsePageSize(page_size)
        if border is None:
            # Default border is 2 cm.
            border = 0.02

        # Construct a layout adding a border to the window contents.
        layout = GridLayout(1, 1, size=size, border=border)
        layout[0, 0] = iwin.figure

        # Render to a PostScript file.  
        hep.draw.postscript.PSFile(
            file_name, page_size=page_size).render(layout)

    elif file_name.endswith(".eps"):
        if border is None:
            # No default border.
            border = 0
        if page_size is None:
            sx, sy = size
            page_size = sx + 2 * border, sy + 2 * border
            
        # Construct a layout adding a border to the window contents.
        layout = GridLayout(1, 1, size=size, border=border)
        layout[0, 0] = iwin.figure

        # Render to an EPS file.
        hep.draw.postscript.EPSFile(file_name, page_size).render(layout)

    else:
        # Don't know how to handle this.
        raise ValueError, \
              "don't know how to print to file '%s'" % file_name


def iproj1(table, expression, selection=None, weight=None,
           number_of_bins=None, range=None, plot=True, over=False, **style):
    """Project a 1D histogram from a table.

    Accumulates 'expression' evaluated on each row of 'table' into a new
    histogram.  Plots the histogram in the display window.

    'selection' -- If specified, an expression to select rows to include
    in the projection.  Only rows for whicah the expression evaluates to
    a true value are included.

    'weight' -- An expression to compute the statistical weight of each
    row.  If 'None' or omitted, unit weights are used.

    'number_of_bins' -- If specified, the number of bins to use in the
    histogram; otherwise, chosen automatically.

    'range' -- If specified, the range to use for the histogram.
    Otherwise, chosen automatically.

    returns -- The projected histogram."""

    # Process the expression.
    expression = hep.expr.asExpression(expression)
    expr_type = expression.type
    if expr_type not in (int, long, float):
        expr_type = float
    expression = hep.expr.compile(expression)
    values = []

    # Process the expression for weights, if given.
    if weight is not None:
        weight_expression = hep.expr.asExpression(weight, compile=True)
        weights = []
    else:
        weights = None

    # Grab all the values that match the selection.
    if selection:
        selected_table = table.select(selection)
    else:
        selected_table = table

    # Compute values, and weights if necessary.
    for row in selected_table:
        values.append(expr_type(expression.evaluate(row)))
        if weight is not None:
            weights.append(float(weight_expression.evaluate(row)))

    # Make the histogram.
    histogram = hep.hist.autoHistogram1D(
        values, number_of_bins, range, weights=weights)
    histogram.axis.name = str(expression)

    if over:
        iseries(histogram, **style)
    elif plot:
        iplot(histogram, **style)
        
    return histogram


def iproject(table, expression, selection=None, weight=None,
             numbers_of_bins=None, ranges=None, plot=True, over=False,
             **style):
    """Project a histogram from a table.

    Accumulates 'expression' evaluated on each row of 'table' into a new
    histogram.  Plots the histogram in the display window.

    'selection' -- If specified, an expression to select rows to include
    in the projection.  Only rows for whicah the expression evaluates to
    a true value are included.

    'weight' -- An expression to compute the statistical weight of each
    row.  If 'None' or omitted, unit weights are used.

    'numbers_of_bins' -- If specified, the number of bins to use in the
    histogram; otherwise, chosen automatically.

    'ranges' -- If specified, the range to use for the histogram.
    Otherwise, chosen automatically.

    returns -- The projected histogram."""

    expression = hep.expr.asExpression(expression)
    if isinstance(expression, hep.expr.Tuple):
        expressions = expression.subexprs
    else:
        expressions = (expression, )

    def compile(expression):
        expression = hep.expr.asExpression(expression)
        expr_type = expression.type
        # FIXME: Why would we need this?
        # if expr_type not in (int, long, float):
        #     expr_type = float
        return hep.expr.compile(expression)

    # Process the expressions.
    expressions = map(compile, expressions)
    values = []
    # Process the expression for weights, if given.
    if weight is not None:
        weight_expression = compile(weight)
        weights = []
    else:
        weights = None

    # Grab all the values that match the selection.
    if selection:
        rows = table.select(selection)
    else:
        rows = iter(table)

    # Compute values, and weights if necessary.
    for row in rows:
        values.append([ e.evaluate(row) for e in expressions ])
        if weight is not None:
            weights.append(float(weight_expression.evaluate(row)))

    # Make the histogram.
    histogram = hep.hist.autoHistogram(
        values, numbers_of_bins, ranges, weights=weights)
    for axis, expression in zip(histogram.axes, expressions):
        axis.name = str(expression)

    if over:
        iseries(histogram, **style)
    elif plot:
        iplot(histogram, **style)

    return histogram


def idump(rows, *expressions):
    """Print values from a table.

    'rows' -- A table or other iterable that returns rows.

    '*expressions' -- One or more expressions.

    Prints the values of each of '*expressions' for each row in 'rows',
    in a tabular format.  Each output line is preceded by the index of
    the row."""

    expressions = map(hep.expr.asExpression, expressions)
    first = True
    for row in rows:
        if first:
            try:
                table = row["_table"]
            except:
                pass
            else:
                expressions = map(table.compile, expressions)
            first = False
        values = map(lambda e: e.evaluate(row), expressions)
        values = map(lambda v: "%8s" % str(v), values)
        print " ".join(values)


def icram(file):
    """Cram names from a file into the global namespace of '__main__'.

    'file' -- A Root or HBOOK file object.

    Loads histograms and tables from 'file' and adds them into the
    global namespace under their same names."""

    main_module = sys.modules["__main__"]
    for name in file.keys():
        try:
            object = file.get(name)
        except:
            pass
        else:
            if hasattr(main_module, name):
                print "replacing '%s'" % name
            setattr(main_module, name, object)


# FIXME: This function should go away, eventually.

def ireload():
    """Reload interactive PyHEP."""

    execfile(os.path.join(hep.config.base_dir, "hep", "interactive.py"),
             globals(), globals())



