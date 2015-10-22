#-----------------------------------------------------------------------
#
# xwindow.py
#
# Copyright (C) 2005 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""X11 window for rendering figures."""

#-----------------------------------------------------------------------
# includes
#-----------------------------------------------------------------------

from __future__ import division

import hep.config
from   hep.draw import *
from   hep.draw import fonts
import hep.ext
import traceback

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

# Map from font family font file name.
font_map = {
    "Courier":              "ucrr8a",
    "Courier-Bold":         "ucrb8a",
    "Courier-Oblique":      "ucrro8a",
    "Helvetica":            "uhvr8a",
    "Helvetica-Bold":       "uhvb8a",
    "Helvetica-Oblique":    "uhvr08a",
    "Times":                "utmr8a",
    "Times-Bold":           "utmb8a",
    "Times-Italic":         "utmri8a",
    "Symbol":               "usyr",
    "Symbol-Italic":        "usyr",
    }

    
# Map from a symbol names to the font and Unicode character point to use
# to display it.  Font choices are for use with "Times" font only.  Some
# of the code points are a little bizarre; they simply determined
# empirically to get something that works.
symbol_map = {
    "alpha":        ("Symbol", u"\u03b1"),
    "beta":         ("Symbol", u"\u03b2"),
    "gamma":        ("Symbol", u"\u03b3"),
    "delta":        ("Symbol", u"\u03b4"),
    "epsilon":      ("Symbol", u"\u03b5"),
    "zeta":         ("Symbol", u"\u03b6"),
    "eta":          ("Symbol", u"\u03b7"),
    "theta":        ("Symbol", u"\u03b8"),
    "vartheta":     ("Symbol", u"\u03d1"),
    "iota":         ("Symbol", u"\u03b9"),
    "kappa":        ("Symbol", u"\u03ba"),
    "lambda":       ("Symbol", u"\u03bb"),
    "mu":           ("Symbol", u"\u00b5"),
    "nu":           ("Symbol", u"\u03bd"),
    "xi":           ("Symbol", u"\u03be"),
    "omicron":      ("Symbol", u"\u03bf"),
    "pi":           ("Symbol", u"\u03c0"),
    "rho":          ("Symbol", u"\u03c1"),
    "varsigma":     ("Symbol", u"\u03c2"),
    "sigma":        ("Symbol", u"\u03c3"),
    "tau":          ("Symbol", u"\u03c4"),
    "upsilon":      ("Symbol", u"\u03c5"),
    "phi":          ("Symbol", u"\u03c6"),
    "varphi":       ("Symbol", u"\u03d5"),
    "chi":          ("Symbol", u"\u03c7"),
    "psi":          ("Symbol", u"\u03c8"),
    "omega":        ("Symbol", u"\u03c9"),
    "varpi":        ("Symbol", u"\u03d6"),

    "Alpha":        ("Symbol", u"\u0391"),
    "Beta":         ("Symbol", u"\u0392"),
    "Gamma":        ("Symbol", u"\u0393"),
    "Delta":        ("Symbol", u"\u2206"),
    "Epsilon":      ("Symbol", u"\u0395"),
    "Zeta":         ("Symbol", u"\u0396"),
    "Eta":          ("Symbol", u"\u0397"),
    "Theta":        ("Symbol", u"\u0398"),
    "Iota":         ("Symbol", u"\u0399"),
    "Kappa":        ("Symbol", u"\u039a"),
    "Lambda":       ("Symbol", u"\u039b"),
    "Mu":           ("Symbol", u"\u039c"),
    "Nu":           ("Symbol", u"\u039d"),
    "Xi":           ("Symbol", u"\u039e"),
    "Omicron":      ("Symbol", u"\u039f"),
    "Pi":           ("Symbol", u"\u03a0"),
    "Rho":          ("Symbol", u"\u03a1"),
    "Sigma":        ("Symbol", u"\u03a3"),
    "Tau":          ("Symbol", u"\u03a4"),
    "Upsilon":      ("Symbol", u"\u03a5"),
    "Varupsilon":   ("Symbol", u"\u03d2"),
    "Phi":          ("Symbol", u"\u03a6"),
    "Chi":          ("Symbol", u"\u03a7"),
    "Psi":          ("Symbol", u"\u03a8"),
    "Omega":        ("Symbol", u"\u2126"),

    "Im":           ("Symbol", u"\u2111"),
    "Re":           ("Symbol", u"\u211c"),
    "approx":       ("Symbol", u"\u2248"),
    "ast":          ("Symbol", u"\u2217"),
    "bullet":       ("Symbol", u"\u2022"),
    "cdot":         (None, u"\u00b7"),
    "dagger":       (None, u"\u2020"),
    "ddagger":      (None, u"\u2021"),
    "degree":       (None, u"\u00b0"),
    "del":          ("Symbol", u"\u2202"),
    "div":          (None, u"\u00f7"),
    "downarrow":    ("Symbol", u"\u2193"),
    "emdash":       (None, u"\u2014"),
    "endash":       (None, u"\u2013"),
    "equiv":        ("Symbol", u"\u2261"),
    "geq":          ("Symbol", u"\u2265"),
    "hyphen":       (None, u"\u002d"),
    "infty":        ("Symbol", u"\u221e"),
    "left'":        (None, u"\u2018"),
    "left\"":       (None, u"\u201c"),
    "leftarrow":    ("Symbol", u"\u2190"),
    "leq":          ("Symbol", u"\u2264"),
    "minus":        ("Symbol", u"\u2212"),
    "nabla":        ("Symbol", u"\u2207"),
    "neq":          ("Symbol", u"\u2260"),
    "pm":           (None, u"\u00b1"),
    "prime":        ("Symbol", u"\u2032"),
    "propto":       ("Symbol", u"\u221d"),
    "right'":       (None, u"\u2019"),
    "right\"":      (None, u"\u201d"),
    "rightarrow":   ("Symbol", u"\u2192"),
    "sim":          ("Symbol", u"\u223c"),
    "times":        (None, u"\u00d7"),
    "uparrow":      ("Symbol", u"\u2191"),
}


# The screen size in pixels.
screen_pixels = None

# The screen size in physical units.
screen_size = None

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def drawMarker(win, x, y, shape, size):
    if shape == "filled dot":
        win.drawCircle(x, y, size / 2, True)
    elif shape == "empty dot":
        win.drawCircle(x, y, size / 2, False)
    elif shape == "filled square":
        x0 = x - size * 0.35
        y0 = y - size * 0.35
        x1 = x + size * 0.35
        y1 = y + size * 0.35
        win.drawPolygon(((x0, y0), (x0, y1), (x1, y1), (x1, y0)))
    elif shape == "empty square":
        x0 = x - size * 0.35
        y0 = y - size * 0.35
        x1 = x + size * 0.35
        y1 = y + size * 0.35
        win.drawLine(((x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)))
    elif shape == "filled diamond":
        s = size / 2
        win.drawPolygon(
            ((x - s, y), (x, y - s), (x + s, y), (x, y + s)))
    elif shape == "empty diamond":
        s = size / 2
        win.drawLine(
            ((x - s, y), (x, y - s), (x + s, y), (x, y + s), (x - s, y)))
    elif shape == "*":
        s = size / 2
        x0 = x - s * 0.87
        x1 = x + s * 0.87
        y0 = y - s * 0.50
        y1 = y + s * 0.50
        win.drawLine(((x, y - s), (x, y + s)))
        win.drawLine(((x0, y0), (x1, y1)))
        win.drawLine(((x0, y1), (x1, y0)))
    elif shape == "+":
        s = size / 2
        win.drawLine(((x - s, y), (x + s, y)))
        win.drawLine(((x, y - s), (x, y + s)))
    elif shape == "X":
        d = (size / 2) / 1.414
        win.drawLine(((x - d, y - d), (x + d, y + d)))
        win.drawLine(((x + d, y - d), (x - d, y + d)))
    else:
        raise NotImplementedError, "marker shape '%s'" % shape


#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class _AggRenderer(object):

    max_font_size = 0.2


    def __init__(self):
        # Initialize state.
        self.color = Color(0, 0, 0)
        self.__current_font = None
        self.font = ("Times", 10 * point)
        self.dash = None
        self.thickness = 1 * point


    def __set_color(self, color):
        self.renderer.color = (color.red, color.green, color.blue)
        self.__color = color


    color = property(lambda self: self.__color, __set_color)


    def __set_font(self, font):
        font_name, font_size = font
        if font_size > self.max_font_size:
            raise ValueError, "font size %f is too large" % font_size

        font_size *= self.scale * self.screen_scale[1]
        if (font_name, font_size) != self.__current_font:
            self.__font = font
            self.__current_font = (font_name, font_size)

            font_file_name = font_map[font_name]
            font_path = os.path.join(
                hep.config.data_dir, "fonts", font_file_name + ".pfb")
            if font_name == "Symbol-Italic":
                oblique_shear = 0.167
            else:
                oblique_shear = 0
            self.renderer.font = (font_path, font_size, oblique_shear)


    font = property(lambda self: self.__font, __set_font)


    def __set_dash(self, dash):
        if dash is not None:
            scale = self.scale \
                    * (self.screen_scale[0] + self.screen_scale[1]) / 2
            dash = [ d * scale for d in dash ]
        self.renderer.dash = dash
        self.__dash = dash


    dash = property(lambda self: self.__dash, __set_dash)


    def __set_thickness(self, thickness):
        screen_scale = (self.screen_scale[0] + self.screen_scale[1]) / 2
        self.renderer.thickness = self.scale * screen_scale * thickness
        self.__thickness = thickness


    thickness = property(lambda self: self.__thickness, __set_thickness)


    def line(self, points):
        points = map(self.map_to_pixels, points)
        self.renderer.drawLine(points)


    def polygon(self, points):
        points = map(self.map_to_pixels, points)
        self.renderer.drawPolygon(points)


    def text(self, position, text, alignment):
        # Convert text to Unicode.
        text = unicode(text, "latin1")
        # Position of text is already in physical units.
        x, y = position

        if alignment != (0, 0):
            x_alignment, y_alignment = alignment
            # Compute text extents.
            width, height, depth = \
                fonts.getTextExtent(text, self.font)
            # Position the start of the text.
            x -= x_alignment * width
            y -= y_alignment * height

        # Now convert to pixels.
        x, y = self.map_to_pixels((x, y))
        # Draw the text.
        self.renderer.drawText(x, y, text)


    def symbol(self, position, symbol):
        font_family, font_size = self.font
        # Look up the symbol in the symbol map.
        symbol_family, glyph = symbol_map[symbol]

        # If no font was specified, use the current font.
        if symbol_family is None:
            symbol_family = font_family
        # Otherwise, set the symbol font.
        else:
            # Determine whether the symbol should be roman or italic.
            if font_family.endswith("-Italic") \
               or font_family.endswith("-Oblique"):
                symbol_family += "-Italic"
            self.font = (symbol_family, font_size)

        # The position is already in physical units, so just convert to
        # pixels. 
        x, y = self.map_to_pixels(position)
        self.renderer.drawText(x, y, glyph)


    def marker(self, position, shape, size):
        x, y = self.map_to_pixels(position)
        size *= self.scale
        size *= (self.screen_scale[0] + self.screen_scale[1]) / 2
        self.dash = None
        self.thickness = 0.5 * point
        drawMarker(self.renderer, x, y, shape, size)




#-----------------------------------------------------------------------

class Window(_AggRenderer):
    """Renderer in a simple X11 window."""

    fixed_aspect = False


    def __init__(self, size, title=None):
        """Create a new window.

        'size' -- The window size, in meters."""

        global screen_pixels
        global screen_size

        if title is None:
            title = str(self)

        # Initialize X11.
        hep.ext.X11_initialize()

        # Get display geometry.
        screen_pixels, screen_size = hep.ext.X11_getScreenSize()
        # Compute conversion factor from meters to pixels.
        self.screen_scale = (screen_pixels[0] / screen_size[0],
                             screen_pixels[1] / screen_size[1])
        self.scale = 1

        # Compute the window size in pixels.
        x_scale, y_scale = self.screen_scale
        width = int(size[0] * x_scale)
        height = int(size[1] * y_scale)

        # Create a window.
        self.renderer = hep.ext.X11Window(width, height)
        # Set the window title.
        self.renderer.title = title
        self.__title = title
        # Hook up our event function.
        self.renderer.event_function = self.onEvent

        # Set up attributes.
        _AggRenderer.__init__(self)

        # Resize the window.
        self.resize(size)


    def onEvent(self, window, event, args):
        """Callback for X11 events."""

        # Make sure it's for this window.
        assert window == self.renderer

        if event == "resize":
            # Compute the new window size.
            x_size = args[0] / self.screen_scale[0]
            y_size = args[1] / self.screen_scale[1]
            # Update it.
            self.onResize((x_size, y_size))


    def onResize(self, size):
        """Update the transformation when the window size changes."""

        self.__size = size
        self.map_to_pixels = Scale(*self.screen_scale) \
                             * Scale(1, -1) \
                             * Translation(0, -size[1])


    def __get_size(self):
        return self.__size


    size = property(__get_size)


    def resize(self, size):
        """Resize the window."""

        if size[0] <= 0 or size[1] <= 0:
            raise ValueError, "window size must be positive"
        if size[0] > 1 or size[1] > 1:
            raise ValueError, "window size too large"

        # Compute the new window size in pixels.
        x_scale, y_scale = self.screen_scale
        width = int(size[0] * x_scale)
        height = int(size[1] * y_scale)
        # Resize the window.
        self.renderer.resize(width, height, self.fixed_aspect)
        # Update our state as necessary.
        self.onResize(size)


    def render(self, figure):
        # Clear the window.
        self.renderer.color = (1, 1, 1)
        x, y = self.size
        x_scale, y_scale = self.screen_scale
        x1 = x * x_scale
        y1 = y * y_scale
        self.renderer.drawPolygon(((0, 0), (x1, 0), (x1, y1), (y1, 0)))
        # Render the figure.
        figure._render(self, (0, 0, x, y))
        # Show the window contents.
        self.renderer.update()


    def __set_title(self, title):
        self.renderer.title = title
        self.__title = title


    title = property(lambda self: self.__title, __set_title)



#-----------------------------------------------------------------------

class FigureWindow(Window):
    """A window that displays a particular figure.

    The window is configured to draw a figure, and redraws the figure
    automatically when the figure's 'is_modifed' attribute is true."""

    # The window automatically re-renders 'figure' whenever it changes
    # by polling the figure's 'is_modified' attribute periodically in
    # response to idle events from the X11 event loop.  This attribute
    # specifies the polling time in seconds.

    update_polling_interval = 0.2


    def __init__(self, figure=None, window_size=(0.20, 0.13),
                 virtual_size=None):
        """Create a new window displaying 'figure'

        'figure' -- The object to draw in the window.

        'window_size' -- The size of the window, in meters.

        'virtual_size' -- The virtual size of the window contents, in
        meters.  If 'None', it tracks the 'window_size'.  """

        if virtual_size is not None:
            virtual_size = parsePageSize(virtual_size)

        # Set up our own state.
        self.__figure = figure
        self.__virtual_size = virtual_size
        self.__scale = 1
        self.do_redraw = False
        self.fixed_aspect = virtual_size is not None

        # Initialize the window.
        Window.__init__(self, window_size)

        # Ask for idle events.
        self.renderer.idle_interval = self.update_polling_interval

        self.virtual_size = virtual_size


    def __get_figure(self):
        return self.__figure


    def __set_figure(self, figure):
        self.__figure = figure
        self.onResize(self.size)
        self.do_redraw = True


    figure = property(__get_figure, __set_figure)


    def __get_virtual_size(self):
        if self.__virtual_size is None:
            return self.size
        else:
            return self.__virtual_size


    def __set_virtual_size(self, virtual_size):
        if virtual_size is not None:
            virtual_size = parsePageSize(virtual_size)
        self.__virtual_size = virtual_size
        self.fixed_aspect = virtual_size is not None
        if virtual_size is not None:
            vx, vy = virtual_size
            sx, sy = self.size
            scale = min(sx / vx, sy / vy)
            self.resize((scale * vx, scale * vy))
        else:
            self.resize(self.size)


    virtual_size = property(__get_virtual_size, __set_virtual_size)


    def __set_scale(self, scale):
        if scale == self.__scale:
            return
        self.__scale = scale
        vx, vy = self.virtual_size
        self.resize((scale * vx, scale * vy))


    scale = property(lambda self: self.__scale, __set_scale)


    def onResize(self, size):
        Window.onResize(self, size)
        virtual_size = self.virtual_size
        # Compute the scale factors to convert from the virtual display
        # size to the window size and from there to pixel coordinates.
        x_scale = size[0] / virtual_size[0]
        y_scale = size[1] / virtual_size[1]
        # Adjust the larger scale factor to preserve the aspect ratio,
        # and compute offsets to keep the display area centered in the
        # window. 
        if x_scale < y_scale:
            scale = x_scale
            dx = 0
            dy = virtual_size[1] * (y_scale - x_scale) / 2
            self.__scale = size[0] / virtual_size[0]
        else:
            scale = y_scale
            dx = virtual_size[0] * (x_scale - y_scale) / 2
            dy = 0
            self.__scale = size[1] / virtual_size[1]
        # Construct the transform to show the display area centered in
        # the window with the right aspect ratio.
        self.map_to_pixels = Translation(dx, dy) \
                             * Scale(scale, -scale) \
                             * Scale(*self.screen_scale) \
                             * Translation(0, -virtual_size[1])


    def render(self, figure):
        # Fill the window with light gray.
        self.renderer.color = (0.97, 0.97, 0.97)
        x, y = self.size
        x_scale, y_scale = self.screen_scale
        x1 = x * x_scale
        y1 = y * y_scale
        self.renderer.drawPolygon(((0, 0), (x1, 0), (x1, y1), (0, y1)))
        # Fill the display area with white.
        x, y = self.virtual_size
        x0, y0 = self.map_to_pixels((0, 0))
        x1, y1 = self.map_to_pixels((x, y))
        self.renderer.color = (1, 1, 1)
        self.renderer.drawPolygon(((x0, y0), (x1, y0), (x1, y1), (x0, y1)))
        # Render the figure.
        figure._render(self, (0, 0, x, y))
        # Show the window contents.
        self.renderer.update()


    def redraw(self):
        """Redraw the display object."""

        try:
            self.render(self.__figure)
        except Exception, e:
            traceback.print_exc()
        self.__figure.is_modified = False


    def onEvent(self, window, event, args):
        assert window == self.renderer

        if event == "idle":
            # If the 'do_redraw' flag is set, or if the figure is
            # modified, redraw the window contents.
            if self.__figure is not None \
               and (self.do_redraw or self.__figure.is_modified):
                self.do_redraw = False
                self.__figure.is_modified = False
                self.redraw()

        elif event == "resize":
            # First the base-class handler.
            Window.onEvent(self, window, event, args)
            # Force a redraw on the next idle event.
            self.do_redraw = True

        else:
            # Use the base-class handler.
            Window.onEvent(self, window, event, args)

        

#-----------------------------------------------------------------------

# The image file renderer doesn't have anything to do with X11, but it
# shares the AGG rendering implementation, so it's included here.  The
# 'imagefile' module contains the public API.

class _ImageFile(_AggRenderer):
    """In-memory renderer for writing an image file."""

    def __init__(self, size, virtual_size):
        sx, sy = size
        vx, vy = virtual_size

        self.renderer = hep.ext.ImageFile(sx, sy)

        scale_x = sx / vx
        scale_y = sy / vy
        self.size = vx, vy
        self.scale = (scale_x + scale_y) / 2
        self.screen_scale = 1, 1
        self.map_to_pixels = \
            Scale(scale_x, -scale_y) * Translation(0, -vy)

        # Set up attributes.
        _AggRenderer.__init__(self)

        # Clear the image.
        self.renderer.color = (1, 1, 1)
        self.renderer.drawPolygon(((0, 0), (sx, 0), (sx, sy), (0, sy)))


    def render(self, figure):
        sx, sy = self.size
        figure._render(self, (0, 0, sx, sy))


    def save(self, path):
        self.renderer.save(path)



