#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division
from __future__ import generators

import cPickle
import hep
import hep.config
from   hep import modified
from   hep.fn import enumerate
from   hep.num import constrain, sum
from   math import *
import os.path

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Color(object):
    """A color.

    Components are stored in the 'red', 'green', and 'blue' attributes.
    Each ranges between 0 and 1."""

    def __init__(self, red, green, blue):
        if red < 0 or green < 0 or blue < 0:
            raise ValueError, "components must be positive"
        self.red = constrain(red, 0, 1)
        self.green = constrain(green, 0, 1)
        self.blue = constrain(blue, 0, 1)


    def __repr__(self):
        return "Color(%f, %f, %f)" % (self.red, self.green, self.blue)


    def __cmp__(self, other):
        return not (isinstance(other, Color) 
                    and self.red == other.red
                    and self.green == other.green
                    and self.blue == other.blue)


    def __add__(self, other):
        return Color(self.red + other.red,
                     self.green + other.green,
                     self.blue + other.blue)


    def __sub__(self, other):
        return Color(self.red - other.red,
                     self.green - other.green,
                     self.blue - other.blue)


    def __mul__(self, scale):
        return Color(self.red * scale,
                     self.green * scale,
                     self.blue * scale)


#-----------------------------------------------------------------------

class Transformation:
    """A two-dimensional affine transformation.

    A transformation is represented by a (2 by 3) matrix of six
    components.  The translation maps a two-dimensional point (x, y) to
    another point (u, v) via

        (u, v)t = ((c0, c1, c2), (c3, c4, c5)) . (x, y, 1)t

    where t denotes matrix transposition and . denotes matrix
    multiplication.

    The transformation has the additional attribute 'scale', which is
    the scale factor of the transformation averaged over directions."""

    def __init__(self, sx, sy, dx, dy):
        self.sx = sx
        self.sy = sy
        self.dx = dx
        self.dy = dy


    def __repr__(self):
        return "Transformation(%f, %f, %f, %f)" \
               % (self.sx, self.sy, self.dx, self.dy)


    def __call__(self, point):
        """Apply the transformation to 'point'.

        'point' -- A sequence of two values."""

        x, y = point
        return x * self.sx + self.dx, y * self.sy + self.dy


    def __mul__(self, other):
        """Compose transformations.

        'other' -- Another transformation.

        returns -- The composed transformation."""

        return Transformation(
            self.sx * other.sx,
            self.sy * other.sy,
            self.dx + self.sx * other.dx,
            self.dy + self.sy * other.dy)



#-----------------------------------------------------------------------

# Constructors for particular transformations.


def Identity():
    """The identity transformation."""

    return Transformation(1, 1, 0, 0)


def Translation(dx, dy):
    """A translation transformation."""

    return Transformation(1, 1, dx, dy)


def Scale(sx, sy):
    """A scaling transformation.

    'sx', 'sy' -- Scale factors in the x and y directions,
    respectively."""

    return Transformation(sx, sy, 0, 0)


def MapRegion(region0, region1):
    """A transformation that maps rectangular 'region1' to 'region0'.

    'region0', 'region1' -- Four-element sequences specifying the
    corners of the range and domain rectangles, respectively."""

    x0, y0, u0, v0 = region0
    x1, y1, u1, v1 = region1
    # Translate the 'region1' coordinates to the origin, apply a scale
    # factor, and then translate into 'region0'.
    return Translation(x0, y0) \
           * Scale((u0 - x0) / (u1 - x1), (v0 - y0) / (v1 - y1)) \
           * Translation(-x1, -y1)


#-----------------------------------------------------------------------

class Figure(modified.Modified):
    """Base class for drawable figures.

    The 'style' attribute is a dictionary of style settings for drawing
    this figure (and subfigures, if any)."""

    # A 'Figure' subclass should have a '_render' method that takes a
    # transformation and a style dictionary.


    def __init__(self, style):
        self.style = modified.Dict(style)
        modified.Modified.__init__(self, modified=True)
        self.watch_modified = [ self.style, ]


    def __getitem__(self, key):
        return self.style[key]


    def get(self, key, default=None):
        return self.style.get(key, default)


    def __setitem__(self, key, value):
        self.style[key] = value


    def __delitem__(self, key):
        del self.style[key]
        


#-----------------------------------------------------------------------

class Layout(Figure):

    header = modified.Property("title")
    footer = modified.Property("footer")
    figures = modified.Property("figures")


    def __init__(self, style):
        self.header = hep.popkey(style, "header", None)
        self.footer = hep.popkey(style, "footer", None)
        Figure.__init__(self, style)


    def _render(self, renderer, region):
        import latex

        header = self.header
        footer = self.footer
        style = self.style
        font_size = style.get("font_size", 10 * point)

        # Adjust the region according to the style parameters.
        x0, y0, x1, y1 = adjustRegionForStyle(region, style)
        # Render header and footer, if any, adjusting the region.
        if header is not None:
            latex.render(renderer, (x0, y1), header, style, (0, 1))
            y1 -= 1.5 * font_size
        if footer is not None:
            latex.render(renderer, (x0, y0), header, style, (0, 0))
            y0 += 1.5 * font_size

        # Return the adjusted region.  A subclass should lay out its
        # contents inside this region.
        return x0, y0, x1, y1


    def append(self, figure):
        try:
            indices = self.indices
        except AttributeError:
            indices = range(len(self.figures))
            self.indices = indices
        try:
            index = indices.pop(0)
        except IndexError:
            raise IndexError, "layout is full"
        else:
            self.figures[index] = figure



#-----------------------------------------------------------------------

class SplitLayout(Layout):

    orientation = modified.Property("orientation")
    fraction = modified.Property("fraction")

    def __init__(self, orientation="vertical",
                 figure0=None, figure1=None, fraction=0.5, **style):
        orientation = str(orientation)
        if orientation not in ("vertical", "horizontal"):
            raise ValueError, "unknown orientation %r" % orientation
        fraction = float(fraction)
        if fraction < 0 or fraction > 1:
            raise ValueError, "'fraction' must be be between 0 and 1"

        self.figures = modified.List([ figure0, figure1 ])
        self.orientation = orientation
        self.fraction = fraction
        Layout.__init__(self, style)


    def _render(self, renderer, region):
        # Perform base-class rendering and setup.
        x0, y0, x1, y1 = Layout._render(self, renderer, region)

        style = self.style
        
        if self.orientation == "vertical":
            # Split vertically.
            x = x0 + (x1 - x0) * self.fraction
            if self.figures[0] is not None:
                self.figures[0]._render(renderer, (x0, y0, x, y1))
            if self.figures[1] is not None:
                self.figures[1]._render(renderer, (x, y0, x1, y1))
        else:
            # Split horizontally; 'figures[0]' goes on top.
            y = y0 + (y1 - y0) * (1 - self.fraction)
            if self.figures[0] is not None:
                self.figures[0]._render(renderer, (x0, y, x1, y1))
            if self.figures[1] is not None:
                self.figures[1]._render(renderer, (x0, y0, x1, y))



#-----------------------------------------------------------------------

class BrickLayout(Layout):
    """Figure layout using rows of "bricks".

    Elements in the layout are arranged in rows.  Each row may have a
    different number of elements.  Each row has the same height, and all
    items in the row have the same width and height."""


    rows = modified.Property("rows")

    
    def __init__(self, rows, **style):
        """Create a layout.

        For example,

          'BrickLayout((2, 2, 1))'

        creates a layout of three rows with two cells in the top and
        center rows and one cell in the bottom row.

        'rows' -- A sequence of rows.  Each row is a sequence of numbers
        specifying how many cells in each row.  The number of rows is
        the length of the sequence."""

        rows = map(int, rows)
        num_figures = sum(rows)

        self.rows = modified.List(rows)
        self.figures = modified.List(num_figures * ( None, ))
        Layout.__init__(self, style)
        self.watch_modified.append(self.figures)


    def __coordinateToIndex(self, coordinates):
        col, row = map(int, coordinates)
        if row > len(self.rows):
            raise IndexError, "invalid row %d" % row
        if col > self.rows[row]:
            raise IndexError, "invalid column %d" % col
        return sum(self.rows[: row]) + col


    def __getitem__(self, coordinates):
        """Get an item in the layout.

        'coordinates' -- The '(column, row)' of the element to get."""

        return self.figures[self.__coordinateToIndex(coordinates)]
    

    def __setitem__(self, coordinates, value):
        """Set an item in the layout.

        'coordinates' -- The '(column, row)' of the element to set.

        'value' -- A figure to place at that location, or 'None'."""

        self.figures[self.__coordinateToIndex(coordinates)] = value


    def _render(self, renderer, region):
        # Perform base-class rendering and setup.
        region = Layout._render(self, renderer, region)

        style = self.style
        margin = style.get("margin", 0)

        dx = region[0]
        dy = region[1]

        rows = self.rows
        num_rows = len(rows)
        figures = iter(self.figures)

        sy = region[3] - region[1] - margin * (num_rows - 1)
        for r, row in enumerate(rows):
            r = num_rows - 1 - r
            y0 = dy + sy * r / num_rows + r * margin
            y1 = dy + sy * (r + 1) / num_rows + r * margin
            sx = region[2] - region[0] - margin * (row - 1)
            for c in range(row):
                figure = figures.next()
                if figure is None:
                    continue
                x0 = dx + sx * c / row + c * margin
                x1 = dx + sx * (c + 1) / row + c * margin
                figure._render(renderer, (x0, y0, x1, y1))



#-----------------------------------------------------------------------

class GridLayout(BrickLayout):
    """A grid layout with evenly-spaced cells.

    This is merely a specialization of 'BrickLayout' with an equal
    number of columns in each row."""
    

    def __init__(self, num_columns, num_rows, **style):
        """Create an empty layout with 'num_columns' and 'num_rows'."""

        columns = num_rows * [num_columns]
        BrickLayout.__init__(self, columns, **style)



#-----------------------------------------------------------------------

class TextFigure(Figure):

    text = modified.Property("text")


    def __init__(self, text="", **style):
        self.text = text
        Figure.__init__(self, style)


    def _render(self, renderer, region):
        import latex        

        text = self.text
        style = self.style
        font_family = style.get("font", "Times")
        font_size = style.get("font_size", 10 * point)
        color = style.get("color", black)
        leading = style.get("leading", 1.2 * font_size)
        tab_width = style.get("tab_width", 10 * font_size)

        region = adjustRegionForStyle(region, style)
        x0 = region[0]

        y = region[3] - leading
        for line in text.split("\n"):
            x = x0
            for tab_part in line.split("\t"):
                latex.render(renderer, (x, y), tab_part, style, (0, 0))
                x += tab_width
            y -= leading
        


#-----------------------------------------------------------------------

class Canvas(modified.List):
    """A container for drawing figures.

    The canvas has its own coordinate system, specified by a rectangular
    range of coordinate values it displays.

    If the 'aspect' style is specified, the coordinate area is
    constrained to the specified aspect ratio when rendered."""


    region = modified.Property("region")

    watch_modified = property(lambda self: tuple(self) + (self.style, ))


    def __init__(self, region, **style):
        if len(region) != 4:
            raise TypeError, "region must have four elements"
        self.region = region
        self.style = modified.Dict(style)
        modified.List.__init__(self)


    def _render(self, renderer, region):
        style = self.style
        # Adjust the region according to the style parameters.
        region = adjustRegionForStyle(region, style)

        # Build the transformation to our coordinates.
        transformation = MapRegion(region, self.region)
        # Render contents.
        for figure in self:
            figure._draw(renderer, transformation, **style)



#-----------------------------------------------------------------------

class Line(Figure):
    """A line composed of continuous line segments.

    The line color, dash pattern, and thickness are specified by the
    '"color"', '"dash"', and '"thickness"' styles, respectively.  The
    dash pattern should be a sequence of lengths for alternating "on"
    and "off" segments."""


    def __init__(self, points, **style):
        self.points = modified.List(points)
        Figure.__init__(self, style)
        self.watch_modified.append(self.points)


    def _draw(self, renderer, transformation, **style):
        style.update(self.style)

        points = map(transformation, self.points)

        renderer.color = style.get("color", black)
        renderer.thickness = style.get("thickness", 0.75 * point)
        renderer.dash = style.get("dash", None)
        renderer.line(points)



#-----------------------------------------------------------------------

class Polygon(Figure):
    """An arbitrary filled polygon.

    The polygon is filled with a solid color specified by the '"color"'
    style.""" 

    def __init__(self, points, **style):
        self.points = modified.List(points)
        Figure.__init__(self, style)
        self.watch_modified.append(self.points)


    def _draw(self, renderer, transformation, **style):
        style.update(self.style)

        points = map(transformation, self.points)
        renderer.color = style.get("color", black)
        renderer.polygon(points)
        


#-----------------------------------------------------------------------

class SimpleText(Figure):
    """A simple text label.

    The font, font size, and color of the text are specified by the
    '"font"', '"font_size"', and '"color"' styles, respectively.  The
    alignment, specified in the '"alignment"' style, is a pair '(ax,
    ay)', where each element is between 0 and 1."""

    position = modified.Property("position")
    text = modified.Property("text")


    def __init__(self, position, text, **style):
        self.position = tuple(position)
        self.text = text
        Figure.__init__(self, style)


    def _draw(self, renderer, transformation, **style):
        style.update(self.style)
        text = self.text
        position = transformation(self.position)

        font_family = style.get("font", "Times")
        font_size = style.get("font_size", 10 * point)
        color = style.get("color", black)
        alignment = style.get("alignment", (0, 0))

        renderer.font = (font_family, font_size)
        renderer.color = color
        renderer.text(position, text, alignment)



#-----------------------------------------------------------------------

class Symbol(Figure):
    """A mathematical or other symbol."""
    

    position = modified.Property("position")

    symbol = modified.Property("symbol")


    def __init__(self, position, symbol, **style):
        self.position = tuple(position)
        self.symbol = symbol
        Figure.__init__(self, style)


    def _draw(self, renderer, transformation, **style):
        style.update(self.style)
        symbol = self.symbol
        position = transformation(self.position)

        font_family = style.get("font", "Times")
        font_size = style.get("font_size", 10 * point)
        color = style.get("color", black)

        renderer.font = (font_family, font_size)
        renderer.color = color
        renderer.symbol(position, symbol)



#-----------------------------------------------------------------------

class Text(Figure):
    """Rendered text.

    The font family, font size, and color of the text are specified by
    the '"font"', '"font_size"', and '"color"' styles, respectively.
    The alignment, specified in the '"alignment"' style, is a pair '(ax,
    ay)', where each element is between 0 and 1."""


    position = modified.Property("position")

    text = modified.Property("text")


    def __init__(self, position, text, **style):
        self.position = tuple(position)
        self.text = text
        Figure.__init__(self, style)


    def _draw(self, renderer, transformation, **style):
        style.update(self.style)
        text = self.text
        position = transformation(self.position)

        font_family = style.get("font", "Times")
        font_size = style.get("font_size", 10 * point)
        color = style.get("color", black)
        alignment = style.get("alignment", (0, 0))

        renderer.font = (font_family, font_size)
        renderer.color = color
        import latex
        latex.render(renderer, position, text, style, alignment)



#-----------------------------------------------------------------------

class Markers(Figure):
    """A series of markers.

    A marker is drawn at each specified point.  The shape, size, and
    color of the markers are specified by the '"shape"', '"size"', and
    '"color"' styles, respectively.

    See 'marker_shapes' for valid marker shapes."""

    points = modified.Property("points")
    

    def __init__(self, points, **style):
        self.points = tuple(points)
        Figure.__init__(self, style)


    def _draw(self, renderer, transformation, **style):
        style.update(self.style)

        shape = style.get("shape", "filled dot")
        size = style.get("size", 2 * point) 
        color = style.get("color", black)
        
        renderer.color = color
        renderer.dash = None
        renderer.thickness = size / 10
        for position in  self.points:
            renderer.marker(transformation(position), shape, size)



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def Gray(level):
    """Construct a shade of gray.
    
    'level' -- The lightness, between 0 (black) and 1 (white)."""

    return Color(level, level, level)



def HSV(hue, saturation, value):
    """Construct a color from a hue, saturation, and value."""

    if saturation == 0:
        # It's gray.
        Color(value, value, value)

    temperature = hue * 6
    i = int(floor(temperature))
    f = temperature - i
    p = value * (1 - saturation)
    q = value * (1 - saturation * f)
    t = value * (1 - saturation * (1 - f))

    if i == 0:
        return Color(value, t, p)
    elif i == 1:
        return Color(q, value, p)
    elif i == 2:
        return Color(p, value, t)
    elif i == 3:
        return Color(p, q, value)
    elif i == 4:
        return Color(t, p, value)
    elif i >= 5:
        return Color(value, p, q)
    else:
        raise RuntimeError


def parsePageSize(page_size):
    """Parse a page size specification.

    'page_size' -- Either a '(width, height)' pair or the name of a
    standard page size.

    returns -- A '(width, height)' pair."""

    if page_size in page_sizes:
        return page_sizes[page_size]
    else:
        try:
            width, height = page_size
        except (TypeError, ValueError):
            raise TypeError, \
                  "'page_size' must be a (width, height) pair or the " \
                  "name of a standard page size"
        return float(width), float(height)
        


def adjustRegionForStyle(region, style):
    """Adjust 'region' according to style attributes.

    The following style attributes are used, if preset in 'style':

    'border' -- The size of a blank border to place around the edge of
    the region.

    'aspect' -- The desired aspect ratio (width / height) of the
    region.

    returns -- The adjusted region.""" 

    border = style.get("border", None)
    aspect = style.get("aspect", None)
    min_aspect = style.get("min_aspect", None)
    max_aspect = style.get("max_aspect", None)
    size = style.get("size", None)

    x0, y0, x1, y1 = region

    if border is not None:
        if border < 0:
            raise ValueError, "invalid border value %f" % aspect
        # Don't let the border occupy more than half the width or
        # height. 
        border = min(border, (x1 - x0) / 4)
        border = min(border, (y1 - y0) / 4)
        # Apply the border.
        x0, y0, x1, y1 = x0 + border, y0 + border, x1 - border, y1 - border
        
    if size is not None:
        sx, sy = size
        sx = min(x1 - x0, sx)
        sy = min(y1 - y0, sy)
        x0 = (x1 + x0 - sx) / 2
        x1 = x0 + sx
        y0 = (y1 + y0 - sy) / 2
        y1 = y0 + sy

    # Impose the minimum aspect.
    if aspect is None and min_aspect is not None:
        actual_aspect = (x1 - x0) / (y1 - y0)
        if actual_aspect < min_aspect:
            aspect = min_aspect
    # Impose the maximum aspect.
    if aspect is None and max_aspect is not None:
        actual_aspect = (x1 - x0) / (y1 - y0)
        if actual_aspect > max_aspect:
            aspect = max_aspect

    if aspect is None:
        pass
    elif aspect <= 0:
        raise ValueError, "invalid aspect value %f" % aspect
    else:
        # Compute the actual rendered aspect ratio.
        r = (x1 - x0) / (y1 - y0)

        if r > aspect:
            # It's too wide; contract and center in x.
            dx = ((x1 - x0) - (y1 - y0) * aspect) / 2
            x0, y0, x1, y1 = x0 + dx, y0, x1 - dx, y1
        else:
            # It's too tall; contract and center in y.
            dy = ((y1 - y0) - (x1 - x0) / aspect) / 2
            x0, y0, x1, y1 = x0, y0 + dy, x1, y1 - dy

    return x0, y0, x1, y1


def drawRectangle(renderer, region):
    x0, y0, x1, y1 = region
    renderer.polygon(((x0, y0), (x0, y1), (x1, y1), (x1, y0)))


def drawFrame(renderer, region):
    x0, y0, x1, y1 = region
    renderer.line(((x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)))


#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

# One inch, in meters.
inch = 0.0254

# One point (1/72 in), in meters.
point = inch / 72


colors = {
    "black": Color(0.0, 0.0, 0.0),
    "blue":  Color(0.2, 0.2, 0.5),
    "green": Color(0.2, 0.6, 0.4),
    "olive": Color(0.3, 0.5, 0.1),
    "orange":Color(0.9, 0.3, 0.1),
    "purple":Color(0.5, 0.2, 0.5),
    "red":   Color(0.6, 0.0, 0.0),
    "white": Color(1.0, 1.0, 1.0),
    }


black = Color(0, 0, 0)
white = Color(1, 1, 1)


dash_patterns = {
    "solid":
    None,
    "dot":
    (1*point, 1.5*point),
    "dash":
    (4*point, 1.5*point),
    "dot-dash":
    (1*point, 1.5*point, 4*point, 1.5*point),
    "dot-dot-dash":
    (1*point, 1.5*point, 1*point, 1.5*point, 4*point, 1.5*point),
    }


marker_shapes = (
    "filled dot",
    "empty dot",
    "filled square",
    "empty square",
    "filled diamond",
    "empty diamond",
    "*",
    "+",
    "X"
    )


# Map from predefined page sizes to physical sizes.
page_sizes = {
    "A":                (8.5 * inch,    11 * inch),
    "A0":               (0.841,         1.189),
    "A1":               (0.594,         0.841),
    "A2":               (0.420,         0.594),
    "A3":               (0.297,         0.420),
    "A4":               (0.210,         0.297),
    "A5":               (0.148,         0.210),
    "A6":               (0.105,         0.148),
    "A7":               (0.074,         0.105),
    "A8":               (0.053,         0.075),
    "B":                (11 * inch,     17 * inch),
    "C":                (17 * inch,     22 * inch),
    "D":                (22 * inch,     34 * inch),
    "E":                (34 * inch,     44 * inch),
    "legal":            (8.5 * inch,    14 * inch),
    "letter":           (8.5 * inch,    11 * inch),
    }


