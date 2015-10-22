#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import fonts
from   hep.draw import *
import re

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

# Map from font names to PostScript font family names.
font_map = {
    "Courier":                  "Courier",
    "Courier-Bold":             "Courier-Bold",
    "Courier-Oblique":          "Courier-Oblique",
    "Helvetica":                "Helvetica",
    "Helvetica-Bold":           "Helvetica-Bold",
    "Helvetica-Oblique":        "Helvetica-Oblique",
    "Symbol":                   "Symbol",
    "Symbol-Italic":            "Symbol",
    "Times":                    "Times-Roman",
    "Times-Bold":               "Times-Bold",
    "Times-Italic":             "Times-Italic",
    }


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def drawMarker(shape, x, y, size, f):
    """Draw a marker.

    Draw marker 'shape' at '(x, y)' with 'size' by writing PostScript to
    file 'f'."""

    size /= 2
    if shape == "filled dot":
        f.write("newpath ")
        f.write("%f %f %f 0 360 arc " % (x, y, size))
        f.write("closepath fill\n")
    elif shape == "empty dot":
        f.write("newpath ")
        f.write("%f %f %f 0 360 arc " % (x, y, size))
        f.write("closepath stroke\n")
    elif shape == "filled square":
        size /= sqrt(2)
        f.write("newpath ")
        f.write("%f %f moveto " % (x + size, y + size))
        f.write("%f %f lineto " % (x - size, y + size))
        f.write("%f %f lineto " % (x - size, y - size))
        f.write("%f %f lineto " % (x + size, y - size))
        f.write("closepath fill\n")
    elif shape == "empty square":
        size /= sqrt(2)
        f.write("% empty square\n")
        f.write("newpath ")
        f.write("%f %f moveto " % (x + size, y + size))
        f.write("%f %f lineto " % (x - size, y + size))
        f.write("%f %f lineto " % (x - size, y - size))
        f.write("%f %f lineto " % (x + size, y - size))
        f.write("closepath stroke\n")
    elif shape == "filled diamond":
        f.write("newpath ")
        f.write("%f %f moveto " % (x + size, y))
        f.write("%f %f lineto " % (x, y + size))
        f.write("%f %f lineto " % (x - size, y))
        f.write("%f %f lineto " % (x, y - size))
        f.write("closepath fill\n")
    elif shape == "empty diamond":
        f.write("newpath ")
        f.write("%f %f moveto " % (x + size, y))
        f.write("%f %f lineto " % (x, y + size))
        f.write("%f %f lineto " % (x - size, y))
        f.write("%f %f lineto " % (x, y - size))
        f.write("closepath stroke\n")
    elif shape == "*":
        dx = 0.866025 * size
        dy = 0.5 * size
        f.write("newpath %f %f moveto " % (x,      y - size))
        f.write("%f %f lineto stroke "  % (x,      y + size))
        f.write("newpath %f %f moveto " % (x - dx, y - dy))
        f.write("%f %f lineto stroke "  % (x + dx, y + dy))
        f.write("newpath %f %f moveto " % (x - dx, y + dy))
        f.write("%f %f lineto stroke\n" % (x + dx, y - dy))
    elif shape == "+":
        f.write("newpath %f %f moveto " % (x - size, y))
        f.write("%f %f lineto stroke "  % (x + size, y))
        f.write("newpath %f %f moveto " % (x,        y - size))
        f.write("%f %f lineto stroke\n" % (x,        y + size))
    elif shape == "X":
        d = 0.707107 * size
        f.write("newpath %f %f moveto " % (x - d,  y - d))
        f.write("%f %f lineto stroke "  % (x + d,  y + d))
        f.write("newpath %f %f moveto " % (x - d,  y + d))
        f.write("%f %f lineto stroke\n" % (x + d,  y - d))
    else:
        raise NotImplementedError, "marker shape '%s'" % shape


#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Renderer(object):

    def __init__(self, size, style):
        self.size = size
        self.style = style
        # These attributes note the current graphic state as we are
        # generating PostScript.
        self.current_scale = 1


    def _writeDefs(self):
        pass


    def _writePageSetup(self):
        self.file.write("%f %f scale\n" % (1 / point, 1 / point))
        self.file.write("true setstrokeadjust\n")
        # Clear out current graphics state so that it will get set again
        # on this page.
        self.__color = None
        self.__thickness = None
        self.__dash = None
        self.__font = None


    def _writePageCleanup(self):
        self.file.write("showpage\n")


    def line(self, points):
        x, y = points[0]
        self.file.write("newpath %.6f %.6f moveto " % (x, y))
        for x, y in points[1 :]:
            self.file.write("%.6f %.6f lineto " % (x, y))
        self.file.write("stroke\n")


    def polygon(self, points):
        x, y = points[0]
        self.file.write("newpath %f %f moveto " % (x, y))
        for x, y in points[1 :]:
            self.file.write("%f %f lineto " % (x, y))
        self.file.write("closepath fill\n")


    def text(self, position, text, alignment):
        # Don't map the position; text is drawn in physical units.
        x, y = position
        # Escape special characters.
        text = re.sub(r"([(\\)])", r"\\\1", text)
        # Align the text.
        x_alignment, y_alignment = alignment
        width, height, depth = fonts.getTextExtent(text, self.font)
        x -= x_alignment * width
        y -= y_alignment * height
        # Draw the text.
        self.file.write("%f %f moveto (%s) show\n" % (x, y, text))


    def symbol(self, position, symbol):
        # Don't map the position; text is drawn in physical units.
        x, y = position

        font_family, font_size = self.font
        # Determine whether the symbol should be roman or italic.
        italic = font_family.endswith("-Italic") \
                 or font_family.endswith("-Oblique")
        # Loop up the font family and PostScript glyph name for this
        # symbol. 
        symbol_family, glyph_name = fonts.symbol_map[symbol]
        if symbol_family is None:
            symbol_family = font_family
        else:
            if italic:
                symbol_family += "-Italic"
            self.font = (symbol_family, font_size)

        # Draw the symbol glyph.
        self.file.write(
            "%f %f moveto /%s glyphshow\n" % (x, y, glyph_name))


    def marker(self, position, shape, size):
        x, y = position
        drawMarker(shape, x, y, size, self.file)


    def __set_color(self, color):
        if color != self.__color:
            self.file.write(
                "%f %f %f setrgbcolor\n"
                % (color.red, color.green, color.blue))
            self.__color = color


    color = property(lambda self: self.__color, __set_color)


    def __set_thickness(self, thickness):
        if thickness != self.__thickness:
            self.file.write("%f setlinewidth\n" % thickness)
            self.__thickness = thickness


    thickness = property(lambda self: self.__tickness, __set_thickness)


    def __set_dash(self, dash):
        if dash != self.__dash:
            self.file.write("[")
            if dash is not None:
                self.file.write(" ".join(map(str, dash)))
            self.file.write("] 0 setdash\n")
            self.__dash = dash


    dash = property(lambda self: self.__dash, __set_dash)


    def __set_font(self, font_spec):
        if font_spec != self.__font:
            font_name, font_size = font_spec
            family = font_map.get(font_name, font_name)
            # Look up the font family in our font map, to determine the
            # PostScript font family name.
            self.file.write(
                "/%s findfont %f scalefont "
                % (family, font_size))
            # Since we don't have an italic symbol font, fake it by
            # applying a shearing transformation.
            if font_name == "Symbol-Italic":
                self.file.write("[ 1 0 0.167 1 0 0 ] makefont ")
            self.file.write("setfont\n")
            self.__font = font_spec

    font = property(lambda self: self.__font, __set_font)



#-----------------------------------------------------------------------

class PSFile(Renderer):
    """Renderer to a multi-page ADSC PostScript file.

    Each time 'begin' is called, a new page is created."""

    default_page_size = "letter"
    

    def __init__(self, path, page_size=None, **style):
        """Create a renderer to a PostScript file.

        'path' -- Path to the new PostScript file.

        'page_size' -- The page size, either a pair of lengths or the
        name of a standard page size.  Default the value of the class
        attribute 'default_page_size'."""

        # Use the default page size if unspecified.
        if page_size is None:
            page_size = self.default_page_size
        # Decode standard page size names.
        page_size = parsePageSize(page_size)

        # Initialize the base class.
        Renderer.__init__(self, page_size, style)
        # Page numbering starts at one.
        self.page = 1

        # Set up the file.
        self.file = file(path, "w")
        self.file.write("%!PS-Adobe-1.0\n")
        self.file.write("%%BoundingBox: " + "0 0 %d %d\n"
                        % (page_size[0] / point, page_size[1] / point))
        self.file.write("%%EndComments\n")
        self._writeDefs()
        

    def render(self, figure):
        # Initialize.
        self.file.write("%%%%Page: %d %d\n" % (self.page, self.page + 1))
        self._writePageSetup()
        # Render the figure.
        sx, sy = self.size
        region = hep.draw.adjustRegionForStyle((0, 0, sx, sy), self.style)
        figure._render(self, region)
        # Clean up.
        self._writePageCleanup()
        self.page += 1



#-----------------------------------------------------------------------

class EPSFile(Renderer):
    """A renderer to an encapsulated PostScript file.

    The 'begin' method should only be invoked once."""

    default_size = (0.08, 0.05)


    def __init__(self, path, size=None, **style):
        """Create an encapsulated PostScript renderer.

        'path' -- Path to the PostScript file.

        'size' -- The bounding box size of the figure."""

        # Use the default size if unspecified.
        if size is None:
            size = self.default_size

        self.__path = path
        self.rendered = False

        # Initialize the base class.
        Renderer.__init__(self, size, style)


    def render(self, figure):
        if self.rendered:
            raise RuntimeError, "an 'EPSFile' may only be rendered once"

        sx, sy = self.size

        # Set up the file.
        self.file = file(self.__path, "w")
        self.file.write("%!PS-Adobe-1.0 EPSF-1.0\n")
        self.file.write("%%%%BoundingBox: 0 0 %d %d\n"
                        % (sx / point, sy / point))
        self.file.write("%%EndComments\n")
        self._writeDefs()
        self._writePageSetup()
        # Render.
        region = hep.draw.adjustRegionForStyle((0, 0, sx, sy), self.style)
        figure._render(self, (0, 0, sx, sy))
        # Clean up.
        self._writePageCleanup()
        del self.file

        self.rendered = True


