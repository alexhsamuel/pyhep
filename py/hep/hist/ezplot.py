#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep
from   hep import enumerate
from   hep.draw import *
import hep.draw.postscript
from   hep.fn import *
import hep.hist
import hep.hist.plot

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

hues = [ 0.40, 0.00, 0.68, 0.08, 0.56, 0.20, 0.92, 0.36 ]

black = Gray(0)
dark_gray = Gray(0.5)
light_gray = Gray(0.8)

red = Color(0.7, 0.0, 0.3)
blue = Color(0.0, 0.2, 0.7)

data_colors = [ black, red, blue, dark_gray ]

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Gallery(object):
    """An arrangement of figures onto multiple pages.

    A 'Gallery' is a collection of pages, each containing one or more
    figures in a brick layout.  Each page may have a title, displayed in
    as a left-justified header.

    Add figures to a gallery using the 'show' method or the '<<'
    operator.  Figures are placed in consecutive cells of the brick
    layout.  Once a page is full, a new page is created for the next
    figure.  The 'nextPage' method forces a new page.

    The 'toPSFile' method will write the entire gallery to a
    multiple-page PostScript file.

    The 'pages' attribute contains the pages in the gallery.  Each is a
    'HeaderLayout' containing a 'BrickLayout'."""


    def __init__(self, columns, page_size="letter", title=None,
                 **style):
        self.columns = columns
        self.page_size = parsePageSize(page_size)
        self.title = title
        self.style = style

        width, height = self.page_size

        self.pages = []
        self.position = (0, 0)


    def show(self, figure):
        col, row = self.position

        # Is this the first figure on a new page?
        if col == 0 and row == 0:
            # Yes.  Create the page.
            layout = BrickLayout(
                self.columns, header=self.title, **self.style)
            self.pages.append(layout)
        else:
            # Get the current page's layout.
            layout = self.pages[-1]

        # Set the figure in the layout.
        layout[col, row] = figure

        # Advance to the next position.
        col += 1
        if col == self.columns[row]:
            col = 0
            row += 1
            if row == len(self.columns):
                row = 0
        self.position = (col, row)


    def __lshift__(self, figure):
        self.show(figure)

    
    def nextPage(self, columns=None, title=None):
        if columns is not None:
            self.columns = columns
        if title is not None:
            self.title = title
        self.position = (0, 0)


    def toPSFile(self, path):
        ps_file = hep.draw.postscript.PSFile(
            path, page_size=self.page_size)
        map(ps_file.render, self.pages)
            


#-----------------------------------------------------------------------

class AutoGallery(Gallery):
    """A gallery of figures generated from a multidimensional array.

    The gallery is filled by the 'generate' method with figures from an
    array of one or more dimensions.  The first two dimensions are
    arranged in the columns and rows of each page (or just the rows, if
    the array is only one-dimeinsional).  Subsequent dimensions are
    arranged onto multiple pages."""
    

    def __init__(self, *series, **kw_args):
        """Create an automatic gallery.

        '*series' -- Specification of the dimensions of the array of
        figures, and the values in these dimensions.  Each element
        represens a dimension, and is a series of values in that
        dimension.

        For example, for the series

            '(1, 2), ("x", "y", "z"), ("plus", "minus")'

        the columns on each page correspond to '1' and '2'; the rows
        correspond to '"x"', '"y"', and '"z"'; and the pages correspond
        to '"plus"' and '"minus"'.

        """

        if len(series) == 0:
            raise "no series specified"
        elif len(series) == 1:
            cols = 1
            rows = len(series[0])
        else:
            cols = len(series[0])
            rows = len(series[1])
        Gallery.__init__(self, rows * (cols, ), **kw_args)
        self.series = series


    def generate(self, get_figure, get_title=None):
        """Generate figures in the gallery.

        'get_figure' -- The function to produce each figure.  It is
        called with one positional argument per dimension of the array.

        'get_title' -- A function to produce the title of each page.  It
        is called with one positional argument per dimension of the
        array, except for the first two dimensions.  It should return a
        string.""" 

        for page_items in combinations_r(*self.series[2 :]):
            if get_title:
                title = get_title(*page_items)
            else:
                title = ", ".join([ str(i) for i in page_items ])
            self.nextPage(title=title)

            for fig_items in combinations_r(*self.series[: 2]):
                self << get_figure(*(fig_items + page_items))

        

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def simple1D(histogram, **style):
    plot = hep.hist.plot.Plot(1, **style)

    plot.append(
        histogram,
        bins="skyline",
        errors=True,
        fill_color=Gray(0.8),
        error_hatch_pitch=0.0005,
        error_hatch_thickness=0.00004,
        error_hatch_color=black,
        **style)

    return plot


def points1D(histogram, **style):
    plot = hep.hist.plot.Plot(1, **style)

    if histogram.axis.number_of_bins < 20:
        marker = "filled dot"
        cross = True
    else:
        marker = None
        cross = True

    plot.append(
        histogram,
        bins="points",
        errors=True,
        marker=marker,
        cross=cross,
        **style)

    return plot


def compare1D(reference_hist, overlay_hist, **style):
    plot = hep.hist.plot.Plot(1, **style)

    if reference_hist is not None:
        plot.append(
            reference_hist,
            bins="skyline",
            errors=False,
            fill_color=Gray(0.8),
            line_color=None,
            thickness=0.1 * point)

    series_style = {
        "bins": "points",
        }
    if overlay_hist.axis.number_of_bins < 20:
        series_style["marker"] = "filled dot"
        series_style["cross"] = True
    elif overlay_hist.axis.number_of_bins < 50:
        series_style["marker"] = "filled dot"
        series_style["cross"] = False
    elif overlay_hist.axis.number_of_bins < 100:
        series_style["marker"] = "filled dot"
        series_style["marker_size"] = 2 * point
        series_style["cross"] = False
    else:
        series_style["marker"] = "filled dot"
        series_style["marker_size"] = 1 * point
        series_style["cross"] = False
    plot.append(overlay_hist, **series_style)

    return plot


def stacked1D(*histograms, **style):
    style.setdefault("overflow_line", False)
    style.setdefault("errors", False)

    plot = hep.hist.plot.Plot(1, **style)

    colors = style.get("colors", [ HSV(h, 0.08, 0.95) for h in hues ])
    if len(histograms) > len(colors):
        raise ValueError, "more histograms than colors"

    sums = []
    for histogram in histograms:
        if len(sums) == 0:
            sums.append(histogram)
        else:
            sums.append(sums[-1] + histogram)

    for i in range(len(sums) - 1, -1, -1):
        color = colors[i]
        histogram = sums[i]
        plot.append(
            histogram,
            bins="skyline",
            fill_color=color,
            line_color=black,
            thickness=0.1 * point)

    return plot


def curves1D(*args, **style):
    style.setdefault("errors", False)

    plot = hep.hist.plot.Plot(1, **style)

    colors = style.get("colors", [ HSV(h, 0.8, 0.4) for h in hues ])
    if len(args) > len(colors):
        raise Value, "more arguments than colors"

    for i, data in enumerate(args):
        if hep.hist.isHistogram(data):
            if data.dimensions == 1:
                bins = "skyline"
            else:
                raise TypeError, \
                      "can't plot %d-D histogram" % data.dimensions
        elif hep.hist.isFunction(data):
            bins = "curve"
        plot.append(
            data,
            bins=bins,
            fill_color=None,
            line_color=colors[i])

    return plot


def points1D(*histograms, **style):
    style.setdefault("errors", False)

    plot = hep.hist.plot.Plot(1, **style)

    colors = style.get("colors",
                       [ black ] + [ HSV(h, 0.8, 0.4) for h in hues ])
    if len(histograms) > len(colors):
        raise Value, "more histograms than colors"

    for histogram, color in zip(histograms, colors):
        plot.append(
            histogram,
            bins="points",
            marker="filled dot",
            cross=True,
            color=color)

    return plot


# multiple skylines

# multiple points (with offset)

def box(histogram, **style):
    style.setdefault("errors", False)

    plot = hep.hist.plot.Plot(2, **style)
    plot.append(
        histogram,
        bins="box",
        color=black)

    return plot


def density(histogram, **style):
    style.setdefault("errors", False)

    plot = hep.hist.plot.Plot(2, **style)
    plot.append(
        histogram,
        bins="density",
        color=black)

    return plot


def compareScatters(*scatters, **style):
    style.setdefault("overflows", False)
    style.setdefault("marker_size", 0.001)

    plot = hep.hist.plot.Plot(2, **style)

    default_colors = [ black, Color(0.8, 0, 0), Color(0, 0.2, 0.6),
                       Gray(0.7) ]
    colors = style.get("colors", default_colors)
    if len(scatters) > len(colors):
        raise Value, "more histograms than colors"

    for scatter, color in zip(scatters, colors):
        plot.append(
            scatter,
            marker="filled dot",
            color=color)

    return plot


#-----------------------------------------------------------------------

def setPresentationStyle(style):
    font_size = style.setdefault("font_size", 18 * point)

    style.setdefault("overflows", False)
    style.setdefault("left_margin", 0.024)
    style.setdefault("right_margin", 0.002)
    style.setdefault("bottom_margin", 2.8 * font_size)
    style.setdefault("top_margin", 2 * font_size)
    style.setdefault("marker", "filled dot")
    style.setdefault("marker_size", 0.002)
    style.setdefault("tick_size", 0.0015)
    style.setdefault("tick_thickness", 1 * point)


def present1D(points=None, reference=None, functions=(), **style):
    if not hasattr(functions, "__len__"):
        functions = (functions, )

    setPresentationStyle(style)
    style.setdefault("zero_line_color", Gray(0.85))
    style.setdefault("zero_line_thickness", 2 * point)
    points_errors = style.get("errors", True)
    reference_errors = style.get("errors", False)

    function_colors = style.get("colors", data_colors)

    plot = hep.hist.plot.Plot(1, **style)
    if reference is not None:
        plot.append(
            reference,
            bins="skyline",
            error_hatch_pitch=0.0015,
            error_hatch_thickness=0.0003,
            errors=reference_errors,
            fill_color=Gray(0.85),
            line_color=None)
    if points is not None:
        plot.append(
            points,
            bins="points",
            errors=points_errors,
            color=black)
    for function, color in zip(functions, function_colors):
        plot.append(
            function,
            color=color)
    
    return plot


