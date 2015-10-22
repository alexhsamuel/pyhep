#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.draw import *
import struct

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

_record_type_codes = {
    "EMR_ABORTPATH":                    68,
    "EMR_ANGLEARC":                     41,
    "EMR_ARC":                          45,
    "EMR_ARCTO":                        55,
    "EMR_BEGINPATH":                    59,
    "EMR_BITBLT":                       76,
    "EMR_CHORD":                        46,
    "EMR_CLOSEFIGURE":                  61,
    "EMR_CREATEBRUSHINDIRECT":          39,
    "EMR_CREATEDIBPATTERNBRUSHPT":      94,
    "EMR_CREATEMONOBRUSH":              93,
    "EMR_CREATEPALETTE":                49,
    "EMR_CREATEPEN":                    38,
    "EMR_DELETEOBJECT":                 40,
    "EMR_ELLIPSE":                      42,
    "EMR_ENDPATH":                      60,
    "EMR_EOF":                          14,
    "EMR_EXCLUDECLIPRECT":              29,
    "EMR_EXTCREATEFONTINDIRECTW":       82,
    "EMR_EXTCREATEPEN":                 95,
    "EMR_EXTFLOODFILL":                 53,
    "EMR_EXTSELECTCLIPRGN":             75,
    "EMR_EXTTEXTOUTA":                  83,
    "EMR_EXTTEXTOUTW":                  84,
    "EMR_FILLPATH":                     62,
    "EMR_FILLRGN":                      71,
    "EMR_FLATTENPATH":                  65,
    "EMR_FRAMERGN":                     72,
    "EMR_GDICOMMENT":                   70,
    "EMR_HEADER":                        1,
    "EMR_INTERSECTCLIPRECT":            30,
    "EMR_INVERTRGN":                    73,
    "EMR_LINETO":                       54,
    "EMR_MASKBLT":                      78,
    "EMR_MODIFYWORLDTRANSFORM":         36,
    "EMR_MOVETOEX":                     27,
    "EMR_OFFSETCLIPRGN":                26,
    "EMR_PAINTRGN":                     74,
    "EMR_PIE":                          47,
    "EMR_PLGBLT":                       79,
    "EMR_POLYBEZIER":                    2,
    "EMR_POLYBEZIER16":                 85,
    "EMR_POLYBEZIERTO":                  5,
    "EMR_POLYBEZIERTO16":               88,
    "EMR_POLYDRAW":                     56,
    "EMR_POLYDRAW16":                   92,
    "EMR_POLYGON":                       3,
    "EMR_POLYGON16":                    86,
    "EMR_POLYLINE":                      4,
    "EMR_POLYLINE16":                   87,
    "EMR_POLYLINETO":                    6,
    "EMR_POLYLINETO16":                 89,
    "EMR_POLYPOLYGON":                   8,
    "EMR_POLYPOLYGON16":                91,
    "EMR_POLYPOLYLINE":                  7,
    "EMR_POLYPOLYLINE16":               90,
    "EMR_POLYTEXTOUTA":                 96,
    "EMR_POLYTEXTOUTW":                 97,
    "EMR_REALIZEPALETTE":               52,
    "EMR_RECTANGLE":                    43,
    "EMR_RESIZEPALETTE":                51,
    "EMR_RESTOREDC":                    34,
    "EMR_ROUNDRECT":                    44,
    "EMR_SAVEDC":                       33,
    "EMR_SCALEVIEWPORTEXTEX":           31,
    "EMR_SCALEWINDOWEXTEX":             32,
    "EMR_SELECTCLIPPATH":               67,
    "EMR_SELECTOBJECT":                 37,
    "EMR_SELECTPALETTE":                48,
    "EMR_SETARCDIRECTION":              57,
    "EMR_SETBKCOLOR":                   25,
    "EMR_SETBKMODE":                    18,
    "EMR_SETBRUSHORGEX":                13,
    "EMR_SETCOLORADJUSTMENT":           23,
    "EMR_SETDIBITSTODEVICE":            80,
    "EMR_SETMAPMODE":                   17,
    "EMR_SETMAPPERFLAGS":               16,
    "EMR_SETMETARGN":                   28,
    "EMR_SETMITERLIMIT":                58,
    "EMR_SETPALETTEENTRIES":            50,
    "EMR_SETPIXELV":                    15,
    "EMR_SETPOLYFILLMODE":              19,
    "EMR_SETROP2":                      20,
    "EMR_SETSTRETCHBLTMODE":            21,
    "EMR_SETTEXTALIGN":                 22,
    "EMR_SETTEXTCOLOR":                 24,
    "EMR_SETVIEWPORTEXTEX":             11,
    "EMR_SETVIEWPORTORGEX":             12,
    "EMR_SETWINDOWEXTEX":                9,
    "EMR_SETWINDOWORGEX":               10,
    "EMR_SETWORLDTRANSFORM":            35,
    "EMR_STRETCHBLT":                   77,
    "EMR_STRETCHDIBITS":                81,
    "EMR_STROKEANDFILLPATH":            63,
    "EMR_STROKEPATH":                   64,
    "EMR_WIDENPATH":                    66,
}


# Map from font family to font name, weight, and italic flag.
font_map = {
    "Courier":              ("Courier New",     400, 0),
    "Courier-Bold":         ("Courier New",     700, 0),
    "Courier-Oblique":      ("Courier New",     400, 1),
    "Helvetica":            ("Helvetica",       400, 0),
    "Helvetica-Bold":       ("Helvetica",       700, 0),
    "Helvetica-Oblique":    ("Helvetica",       400, 1),
    "Times":                ("Times New Roman", 400, 0),
    "Times-Bold":           ("Times New Roman", 700, 0),
    "Times-Italic":         ("Times New Roman", 400, 1),
    "Symbol":               ("Symbol",          400, 0),
    "Symbol-Italic":        ("Symbol",          400, 1),
    }


symbol_map = {
    "alpha":        (None, u"\u03b1"),
    "beta":         (None, u"\u03b2"),
    "gamma":        (None, u"\u03b3"),
    "delta":        (None, u"\u03b4"),
    "epsilon":      (None, u"\u03b5"),
    "zeta":         (None, u"\u03b6"),
    "eta":          (None, u"\u03b7"),
    "theta":        (None, u"\u03b8"),
    "iota":         (None, u"\u03b9"),
    "kappa":        (None, u"\u03ba"),
    "lambda":       (None, u"\u03bb"),
    "mu":           (None, u"\u03bc"),
    "nu":           (None, u"\u03bd"),
    "xi":           (None, u"\u03be"),
    "omicron":      (None, u"\u03bf"),
    "pi":           (None, u"\u03c0"),
    "rho":          (None, u"\u03c1"),
    "varsigma":     (None, u"\u03c2"),
    "sigma":        (None, u"\u03c3"),
    "tau":          (None, u"\u03c4"),
    "upsilon":      (None, u"\u03c5"),
    "phi":          ("Symbol", u"\u0066"),
    "chi":          (None, u"\u03c7"),
    "psi":          (None, u"\u03c8"),
    "omega":        (None, u"\u03c9"),

    "Alpha":        (None, u"\u0391"),
    "Beta":         (None, u"\u0392"),
    "Gamma":        (None, u"\u0393"),
    "Delta":        (None, u"\u0394"),
    "Epsilon":      (None, u"\u0395"),
    "Zeta":         (None, u"\u0396"),
    "Eta":          (None, u"\u0397"),
    "Theta":        (None, u"\u0398"),
    "Iota":         (None, u"\u0399"),
    "Kappa":        (None, u"\u039a"),
    "Lambda":       (None, u"\u039b"),
    "Mu":           (None, u"\u039c"),
    "Nu":           (None, u"\u039d"),
    "Xi":           (None, u"\u039e"),
    "Omicron":      (None, u"\u039f"),
    "Pi":           (None, u"\u03a0"),
    "Rho":          (None, u"\u03a1"),
    "Sigma":        (None, u"\u03a3"),
    "Tau":          (None, u"\u03a4"),
    "Upsilon":      (None, u"\u03a5"),
    "Phi":          (None, u"\u03a6"),
    "Chi":          (None, u"\u03a7"),
    "Psi":          (None, u"\u03a8"),
    "Omega":        (None, u"\u03a9"),

    "vartheta":     ("Symbol", u"\u004a"),
    "varphi":       ("Symbol", u"\u006a"),
    "varpi":        ("Symbol", u"\u0076"),
    "Varupsilon":   ("Symbol", u"\u00a1"),

    "Im":           ("Symbol", u"\u00c1"),
    "Re":           ("Symbol", u"\u00c2"),
    "approx":       ("Symbol", u"\u00bb"),
    "ast":          ("Symbol", u"\u002a"),
    "bullet":       (None, u"\u00b7"),
    "cdot":         (None, u"\u00b7"),
    "dagger":       (None, u"\u2020"),
    "ddagger":      (None, u"\u2021"),
    "degree":       (None, u"\u00b0"),
    "del":          (None, u"\u2202"),
    "div":          (None, u"\u00f7"),
    "downarrow":    (None, u"\u2193"),
    "equiv":        (None, u"\u2261"),
    "emdash":       (None, u"\u2014"),
    "endash":       (None, u"\u2013"),
    "geq":          (None, u"\u2265"),
    "hyphen":       (None, u"\u002d"),
    "infty":        (None, u"\u221e"),
    "left'":        (None, u"\u2018"),
    "left\"":       (None, u"\u201c"),
    "leftarrow":    (None, u"\u2190"),
    "leq":          (None, u"\u2264"),
    "minus":        (None, u"\u2212"),
    "prime":        (None, u"\u2032"),
    "nabla":        ("Symbol", u"\u00d1"),
    "neq":          (None, u"\u2260"),
    "pm":           (None, u"\u00b1"),
    "propto":       ("Symbol", u"\u00b5"),
    "right'":       (None, u"\u2019"),
    "right\"":      (None, u"\u201d"),
    "rightarrow":   (None, u"\u2192"),
    "sim":          (None, "~"),
    "times":        (None, u"\u00d7"),
    "uparrow":      (None, u"\u2191"),
}


#-----------------------------------------------------------------------
# types
#-----------------------------------------------------------------------

class EnhancedMetafile(object):

    # Structure format for the header record.
    header_format = "<IIllllllllIIIIHHIIIllll"
    header_size = struct.calcsize(header_format)

    # Dimensions in pixels and meters of a reference display.
    reference_screen_pixels = 1024, 768
    reference_screen_size = 0.256, 0.192

    # Our virtual sizes are in meters.  GDI wants them expressed in
    # integers.  This is the scale factor we use to get adequate
    # resolution.
    window_scale_factor = 100000


    def __init__(self, path, size, virtual_size=None, description=""):
        if virtual_size is None:
            virtual_size = size

        # Initialize graphics attributes.
        self.__color = black
        self.__dash = None
        self.__font = "Times", 10
        self.__thickness = 0.0005

        # Track handles in use.  Each position contains a flag whether
        # the handle with the corresponding index is in use.  Handle
        # zero is reserved.
        self.__handles = [ True ]

        # Track handles in use.
        self.__brush_handle = None
        self.__font_handle = None
        self.__pen_handle = None

        # The displayed size of the drawing region, called the "viewport
        # size" by GDI.
        self.__size = size
        # The size of the coordinate region used when drawing, called
        # "window size" in GDI.
        self.__virtual_size = virtual_size

        # Create the file.
        self.__file = open(path, "w")
        # Track the number of records and total file size.
        self.__num_records = 0
        self.__file_size = 0
        
        # Skip past the header.  We'll write it at the end.
        self.__file.seek(self.header_size)
        self.__num_records += 1
        self.__file_size += self.header_size
        
        # Write the description, NUL-terminated and encoded in
        # little-endian UTF-16 with the endian-detection word.
        if description:
            description_buffer = (description + "\0").encode("utf_16_le")
            self.__file.write(description_buffer)
            self.__description_offset = self.header_size
            self.__description_length = len(description_buffer)
            self.__file_size += self.__description_length
        else:
            self.__description_offset = 0
            self.__description_length = 0

        # Note the file size so far, which is the size of the first
        # (i.e. header) record.
        self.__header_record_size = self.__file_size

        # Set up coordinate mapping, etc.
        self.__setUp()
        # Set up graphics stuff.
        self.__setBrush()
        self.__setFont()
        self.__setPen()

        self.rendered = False


    def __del__(self):
        # Free outstanding graphics objects.
        if self.__brush_handle:
            self.__deleteObject(self.__brush_handle)
        if self.__font_handle:
            self.__deleteObject(self.__font_handle)
        if self.__pen_handle:
            self.__deleteObject(self.__pen_handle)
        # Make sure there are no object handles referring to
        # still-allocated objects, except for the first handle, which is
        # reserved.
        assert True not in self.__handles[1 :]

        # Write the end-of-file record.
        self.__writeRecord("EMR_EOF", 0, 0, 20)
        # Write the header.
        self.__writeHeader()
        # Close the file.
        self.__file.close()


    def __set_color(self, color):
        if self.__color != color:
            self.__color = color
            self.__setBrush()
            self.__setPen()
            self.__writeRecord("EMR_SETTEXTCOLOR", self.__mapColor(color))


    color = property(lambda self: self.__color, __set_color)


    def __set_dash(self, dash):
        if self.__dash != dash:
            self.__dash = dash
            self.__setPen()


    dash = property(lambda self: self.__dash, __set_dash)


    def __set_font(self, font):
        if self.__font != font:
            self.__font = font
            self.__setFont()


    font = property(lambda self: self.__font, __set_font)


    def __set_thickness(self, thickness):
        if self.__thickness != thickness:
            self.__thickness = thickness
            self.__setPen()


    thickness = property(lambda self: self.__thickness, __set_thickness)


    def render(self, figure):
        if self.rendered:
            raise RuntimeError, \
                  "an 'EnhancedMetafile' may only be rendered once"

        # Render the figure.
        x1, y1 = self.__size
        figure._render(self, (0, 0, x1, y1))
        self.rendered = True


    def line(self, points):
        sx, sy = self.__size

        # Find the coordinates of the first point.
        px, py = self.__map(points[0])
        # Move there.
        self.__writeRecord("EMR_MOVETOEX", px, py)
        # Make a list of x and y coordinates of the remaining points.
        coordinates = \
            reduce(lambda c, p: c + self.__map(p), points[1 :], ())
        # Draw the lines.
        self.__writeRecord(
            "EMR_POLYLINETO",
            0, 0, sx, sy,
            len(coordinates) / 2, *coordinates)


    def marker(self, position, shape, size):
        x, y = self.__map(position)
        wsf = self.window_scale_factor
        size *= wsf
        wR = self.__writeRecord

        self.thickness = 0.5 * point
        self.dash = None

        if shape == "filled dot":
            r = size / 2
            wR("EMR_ELLIPSE",
               x - r, y - r, x + r, y + r)
        elif shape == "empty dot":
            r = size / 2
            wR("EMR_ARC",
               x - r, y - r, x + r, y + r,
               x - r, y,
               x - r, y)
        elif shape == "filled square":
            w = size * 0.35
            wR("EMR_RECTANGLE",
               x - w, y - w, x + w, y + w)
        elif shape == "empty square":
            w = size * 0.35
            wR("EMR_POLYLINE",
               0, 0, 0, 0,
               5,
               x - w, y - w,
               x - w, y + w,
               x + w, y + w,
               x + w, y - w,
               x - w, y - w)
        elif shape == "filled diamond":
            s = size / 2
            wR("EMR_BEGINPATH")
            wR("EMR_POLYLINE",
               0, 0, 0, 0, 
               5,
               x - s, y,
               x, y - s,
               x + s, y,
               x, y + s,
               x - s, y)
            wR("EMR_ENDPATH")
            wR("EMR_FILLPATH",
               0, 0, 0, 0)
        elif shape == "empty diamond":
            s = size / 2
            wR("EMR_POLYLINE",
               0, 0, 0, 0, 
               5,
               x - s, y,
               x, y - s,
               x + s, y,
                x, y + s,
               x - s, y)
        elif shape == "*":
            s = size / 2
            x0 = x - s * 0.87
            x1 = x + s * 0.87
            y0 = y - s * 0.50
            y1 = y + s * 0.50
            wR("EMR_POLYPOLYLINE",
               0, 0, 0, 0,
               3,
               6,
               2, 2, 2,
               x, y - s, x, y + s,
               x0, y0, x1, y1,
               x0, y1, x1, y0)
        elif shape == "+":
            s = size / 2
            wR("EMR_POLYPOLYLINE",
               0, 0, 0, 0,
               2,
               4,
               2, 2,
               x - s, y, x + s, y,
               x, y - s, x, y + s)
        elif shape == "X":
            d = (size / 2) / 1.414
            wR("EMR_POLYPOLYLINE",
               0, 0, 0, 0,
               2,
               4,
               2, 2,
               x - d, y - d, x + d, y + d,
               x + d, y - d, x - d, y + d)
        else:
            raise NotImplementedError, "marker shape '%s'" % shape
        

    def polygon(self, points):
        sx, sy = self.__size
        # Make a list of x and y coordinates of the vertices.
        coordinates = reduce(lambda c, p: c + self.__map(p), points, ())

        self.__writeRecord("EMR_BEGINPATH")
        self.__writeRecord(
            "EMR_POLYLINE",
            0, 0, sx, sy,
            len(coordinates) / 2, *coordinates)
        self.__writeRecord("EMR_ENDPATH")
        self.__writeRecord("EMR_FILLPATH", 0, 0, sx, sy)


    def symbol(self, position, symbol):
        # Don't map the position; text is drawn in physical units.
        x, y = position

        font_family, font_size = self.font
        # Determine whether the symbol should be roman or italic.
        italic = font_family.endswith("-Italic") \
                 or font_family.endswith("-Oblique")
        # Loop up the font family and PostScript glyph name for this
        # symbol. 
        symbol_family, glyph = symbol_map[symbol]
        if symbol_family is None:
            symbol_family = font_family
        else:
            if italic:
                symbol_family += "-Italic"
            self.font = (symbol_family, font_size)

        # Draw the symbol glyph.
        self.text(position, glyph, (0, 0))


    def text(self, position, text, alignment):
        # Convert text to unicode.
        if not isinstance(text, unicode):
            text = unicode(text, "latin1")

        px, py = self.__map(position)
        string_data = text.encode("utf_16_le")
        # Pad 'string_data' so it is an even number of words.
        if len(string_data) % 4 == 2:
            string_data += "\0\0"
        # Create the record.  The graphics mode is "GM_ADVANCED".
        record_data = struct.pack(
            "iiiiiffiiiiiiiiii",
            0, 0, 1, 1,                             # rclBounds
            2,                                      # iGraphicsMode
            1,                                      # exScale
            1,                                      # eyScale
            px, py,                                 # ptlReference
            len(text),                              # nChars
            76,                                     # offString
            0,                                      # fOptions
            0, 0, 0, 0,                             # rcl
            0,                                      # offDx
            ) + string_data
        self.__writeRawRecord("EMR_EXTTEXTOUTW", record_data)


    def __map(self, point):
        sf = self.window_scale_factor
        px, py = point
        return int(round(sf * px)), int(round(-sf * py))


    def __mapColor(self, color):
        return int(color.blue    * 255) << 16 \
               | int(color.green * 255) <<  8 \
               | int(color.red   * 255)


    def __getHandle(self):
        """Return an available handle."""

        # Is there an available handle?
        if not False in self.__handles:
            # No.  Use a new handle.
            handle = len(self.__handles)
            # It goes at the end.
            self.__handles.append(True)
        else:
            # Yes.  Take it.
            handle = self.__handles.index(False)
            self.__handles[handle] = True

        return handle


    def __deleteObject(self, handle):
        # Make sure the handle is markes as in use.
        assert self.__handles[handle]
        # Delete the object.
        self.__writeRecord("EMR_DELETEOBJECT", handle)
        # Mark the handle as unused.
        self.__handles[handle] = False


    def __writeRecord(self, record_type, *parameters):
        # Pack the parameters.
        format = "%di" % len(parameters)
        record_data = struct.pack(format, *parameters)
        # Write the record.
        self.__writeRawRecord(record_type, record_data)


    def __writeRawRecord(self, record_type, record_data):
        # Look up the numerical type code for this record type.
        type_code = _record_type_codes[record_type]
        # Pad to the next four-byte boundary.
        while len(record_data) % 4 > 0:
            record_data += "\0"
        # Construct the structure format for this record.
        format = "=II"
        size = struct.calcsize(format) + len(record_data)
        buffer = struct.pack(format, type_code, size) + record_data
        # Write the record.
        self.__file.write(buffer)
        self.__num_records += 1
        self.__file_size += size


    def __setUp(self):
        wsf = self.window_scale_factor
        wx, wy = self.__virtual_size
        vx, vy = self.__size
        rpx, rpy = self.reference_screen_pixels
        rsx, rsy = self.reference_screen_size
        writeRecord = self.__writeRecord

        # Set up for transparent drawing, mode "TRANSPARENT".
        writeRecord("EMR_SETBKMODE", 1)
        # Set text alignment mode to "TA_BASELINE".
        writeRecord("EMR_SETTEXTALIGN", 24)

        # Set up the coordinate mapping.  We will use a custom
        # anisotropic mapping ("MM_ANISOTROPIC").
        writeRecord("EMR_SETMAPMODE", 8)
        # Set the window coordinates, i.e. the virtual drawing region.
        writeRecord("EMR_SETWINDOWORGEX", 0, 0)
        writeRecord("EMR_SETWINDOWEXTEX", wx * wsf, wy * wsf)
        # Set the viewport coordinates, which determine how large the
        # metafile will appear when drawn.
        writeRecord("EMR_SETVIEWPORTORGEX", 0, 0)
        writeRecord("EMR_SETVIEWPORTEXTEX", wx * rpx / rsx, wy * rpy / rsy)
        

    def __setBrush(self):
        # Get a handle for the new brush.
        handle = self.__getHandle()
        # Get the brush color.
        color = self.__mapColor(self.__color)
        
        # Create a brush with style "BS_SOLID".
        self.__writeRecord(
            "EMR_CREATEBRUSHINDIRECT",
            handle,                                 # ihBrush
            0,                                      # lbStyle
            color,                                  # lbColor
            0,                                      # lbHatch
            )
        # Select the new brush.
        self.__writeRecord("EMR_SELECTOBJECT", handle)

        # Delete the old brush, if any.
        if self.__brush_handle is not None:
            self.__deleteObject(self.__brush_handle)
        # Remember the new brush handle.
        self.__brush_handle = handle


    def __setFont(self):
        wsf = self.window_scale_factor
        # Get a handle for the new font.
        handle = self.__getHandle()
        # Get the font family.
        font_family, font_size = self.__font
        # Look up the font name and and attributes.
        font_name, weight, italics = font_map[font_family]
        # Encode the font name as UTF-16.
        font_name = font_name.encode("utf_16_le")
        # Convert the font size to logical units.
        font_size *= -wsf 

        record_data = struct.pack(
            "iiiiiiBBBBBBBB64s128s64sIIII4sI10B",
            handle,                                 # ihFont
            # FIXME
            font_size,                              # lfHeight
            0,                                      # lfWidth
            0,                                      # lfEscapement
            0,                                      # lfOrientation
            weight,                                 # lfWeight
            italics,                                # lfItalic
            0,                                      # lfUnderline
            0,                                      # lfStrikeOut
            0,                                      # lfCharSet
            0,                                      # lfOutPrecision
            0,                                      # lfClipPrecision
            4,                                      # lfQuality
            2,                                      # lfPitchAndFamily
            font_name,                              # lfFaceName
            "",                                     # elfFullName
            "",                                     # elfStyle
            0,                                      # elfVersion
            0,                                      # elfStyleSize
            0,                                      # elfMatch
            0,                                      # elfReserved
            "",                                     # elfVendorId
            0,                                      # elfCulture
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,           # elfPanose
            )
        self.__writeRawRecord("EMR_EXTCREATEFONTINDIRECTW", record_data)
        # Select the new font.
        self.__writeRecord("EMR_SELECTOBJECT", handle)

        # Delete the old font, if any.
        if self.__font_handle is not None:
            self.__deleteObject(self.__font_handle)
        # Remember the new brush handle.
        self.__font_handle = handle


    def __setPen(self):
        wsf = self.window_scale_factor
        # Get a handle for the new pen.
        handle = self.__getHandle()
        # Get the pen color.
        color = self.__mapColor(self.__color)
        # Get the pen dash pattern.
        thickness = wsf * self.__thickness
        if self.__dash is None:
            pen_style = 0x10000
            dash = ()
        else:
            pen_style = 0x10007
            dash = [ wsf * v for v in self.__dash ]
            # If the line is too thin, Windows treats this as a cosmetic
            # line even if PS_GEOMETRIC is specified, and then
            # interprets the dash intervals in display units.  Make sure
            # the thickness is large enough to avoid this.
            thickness = max(30, thickness)
            # FIXME: This isn't the right threshold.  Somehow it depends
            # on the size.

        # Create the pen,
        pen_style = 0x10200  # PS_GEOMETRIC | PS_ENDCAP_FLAT
        if len(dash) > 0:
            pen_style |= 7  # PS_USERSTYLE
        self.__writeRecord(
            "EMR_EXTCREATEPEN",
            handle,                                 # ihPen
            0,                                      # offPmi
            0,                                      # cbBmi
            0,                                      # offBits
            0,                                      # cbBits
            pen_style,                              # elpPenStyle
            thickness,                              # elpWidth
            0,                                      # elpBrushStyle
            color,                                  # elpColor
            0,                                      # elpHatch
            len(dash),                              # elpNumEntries
            *dash                                   # elpStyleEntry
            )
        # Select the new pen.
        self.__writeRecord("EMR_SELECTOBJECT", handle)

        # Delete the old pen, if any.
        if self.__pen_handle is not None:
            self.__deleteObject(self.__pen_handle)
        # Remember the new pen handle.
        self.__pen_handle = handle
            


    def __writeHeader(self):
        wsf = self.window_scale_factor
        wx, wy = self.__virtual_size
        vx, vy = self.__size
        rpx, rpy = self.reference_screen_pixels
        rsx, rsy = self.reference_screen_size

        # Return to the start of the file.
        self.__file.seek(0)
        # Construct the header.
        buffer = struct.pack(
            self.header_format,                     
            _record_type_codes["EMR_HEADER"],       # iType
            self.__header_record_size,              # nSize
            0, -wy * wsf, wx * wsf, 0,              # rclBounds
            0, -vy * 100000, vx * 100000, 0,        # rclFrame
            0x464d4520,                             # dSignature
            0x10000,                                # nVersion
            self.__file_size,                       # nBytes
            self.__num_records,                     # nRecords
            len(self.__handles),                    # nHandles
            0,                                      # sReserved
            self.__description_length,              # nDescription
            self.__description_offset,              # offDescription
            0,                                      # nPalEntries
            rpx, rpy,                               # szlDevice
            rsx * 1000, rsy * 1000,                 # szlMillimeters
            )

        # Write it.
        self.__file.write(buffer)



