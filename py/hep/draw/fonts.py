#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

import hep.config
import os.path
import re
import sys

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class ParseError(RuntimeError):

    pass



#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

font_dir_path = os.path.join(hep.config.data_dir, "fonts")


font_map = {
    "Courier":              "ucrr8a",
    "Courier-Bold":         "ucrb8a",
    "Courier-Oblique":      "ucrro8a",
    "Helvetica":            "uhvr8a",
    "Helvetica-Bold":       "uhvb8a",
    "Helvetica-Oblique":    "uhvro8a",
    "Symbol":               "usyr",
    "Times":                "utmr8a",
    "Times-Bold":           "utmb8a",
    "Times-Italic":         "utmri8a",
    }


symbol_map = {
    "alpha":        ("Symbol", "alpha"),
    "beta":         ("Symbol", "beta"),
    "gamma":        ("Symbol", "gamma"),
    "delta":        ("Symbol", "delta"),
    "epsilon":      ("Symbol", "epsilon"),
    "zeta":         ("Symbol", "zeta"),
    "eta":          ("Symbol", "eta"),
    "theta":        ("Symbol", "theta"),
    "vartheta":     ("Symbol", "theta1"),
    "iota":         ("Symbol", "iota"),
    "kappa":        ("Symbol", "kappa"),
    "lambda":       ("Symbol", "lambda"),
    "mu":           ("Symbol", "mu"),
    "nu":           ("Symbol", "nu"),
    "xi":           ("Symbol", "xi"),
    "omicron":      ("Symbol", "omicron"),
    "pi":           ("Symbol", "pi"),
    "rho":          ("Symbol", "rho"),
    "varsigma":     ("Symbol", "sigma1"),
    "sigma":        ("Symbol", "sigma"),
    "tau":          ("Symbol", "tau"),
    "upsilon":      ("Symbol", "upsilon"),
    "phi":          ("Symbol", "phi"),
    "varphi":       ("Symbol", "phi1"),
    "chi":          ("Symbol", "chi"),
    "psi":          ("Symbol", "psi"),
    "omega":        ("Symbol", "omega"),
    "varpi":        ("Symbol", "omega1"),

    "Alpha":        ("Symbol", "Alpha"),
    "Beta":         ("Symbol", "Beta"),
    "Gamma":        ("Symbol", "Gamma"),
    "Delta":        ("Symbol", "Delta"),
    "Epsilon":      ("Symbol", "Epsilon"),
    "Zeta":         ("Symbol", "Zeta"),
    "Eta":          ("Symbol", "Eta"),
    "Theta":        ("Symbol", "Theta"),
    "Iota":         ("Symbol", "Iota"),
    "Kappa":        ("Symbol", "Kappa"),
    "Lambda":       ("Symbol", "Lambda"),
    "Mu":           ("Symbol", "Mu"),
    "Nu":           ("Symbol", "Nu"),
    "Xi":           ("Symbol", "Xi"),
    "Omicron":      ("Symbol", "Omicron"),
    "Pi":           ("Symbol", "Pi"),
    "Rho":          ("Symbol", "Rho"),
    "Sigma":        ("Symbol", "Sigma"),
    "Tau":          ("Symbol", "Tau"),
    "Upsilon":      ("Symbol", "Upsilon"),
    "Varupsilon":   ("Symbol", "Upsilon1"),
    "Phi":          ("Symbol", "Phi"),
    "Chi":          ("Symbol", "Chi"),
    "Psi":          ("Symbol", "Psi"),
    "Omega":        ("Symbol", "Omega"),

    "Im":           ("Symbol", "Ifraktur"),
    "Re":           ("Symbol", "Rfraktur"),
    "approx":       ("Symbol", "approxequal"),
    "ast":          ("Symbol", "asteriskmath"),
    "bullet":       ("Symbol", "bullet"),
    "cdot":         (None, "periodcentered"),
    "dagger":       (None, "dagger"),
    "ddagger":      (None, "daggerdbl"),
    "degree":       (None, "degree"),
    "del":          ("Symbol", "partialdiff"),
    "div":          (None, "divide"),
    "downarrow":    ("Symbol", "arrowdown"),
    "equiv":        ("Symbol", "equivalence"),
    "emdash":       (None, "emdash"),
    "endash":       (None, "endash"),
    "geq":          ("Symbol", "greaterequal"),
    "hyphen":       (None, "hyphen"),
    "infty":        ("Symbol", "infinity"),
    "left'":        (None, "quoteleft"),
    "left\"":       (None, "quotedblleft"),
    "leftarrow":    ("Symbol", "arrowleft"),
    "leq":          ("Symbol", "lessequal"),
    "minus":        ("Symbol", "minus"),
    "prime":        ("Symbol", "minute"),
    "nabla":        ("Symbol", "gradient"),
    "neq":          ("Symbol", "notequal"),
    "pm":           ("Symbol", "plusminus"),
    "propto":       ("Symbol", "proportional"),
    "right'":       (None, "quoteright"),
    "right\"":      (None, "quotedblright"),
    "rightarrow":   ("Symbol", "arrowright"),
    "sim":          ("Symbol", "similar"),
    "times":        ("Symbol", "multiply"),
    "uparrow":      ("Symbol", "arrowup"),
}


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def StrippedLineIter(lines):
    """Adapt an iterator over lines to strip lines and omit blank lines."""

    lines = iter(lines)
    while True:
        next_line = lines.next().strip()
        if next_line == "":
            continue
        yield next_line


def parseAfmCharMetrics(lines):
    pattern = re.compile(
        "C (-?\d+) ; WX (\d+) ; N (\w+) ; B (-?\d+ -?\d+ -?\d+ -?\d+) ;")

    char_metrics = {}
    while True:
        line = lines.next()
        if line == "EndCharMetrics":
            return char_metrics

        match = pattern.match(line)
        if match is None:
            raise ParseError, "character line '%s'" % line

        code_point = int(match.group(1))
        width = int(match.group(2))
        glyph_name = match.group(3)
        bounding_box = tuple(map(int, match.group(4).split()))
        char_metrics[glyph_name] = (code_point, width, bounding_box)

    return char_metrics

        
def parseAfm(lines):
    lines = StrippedLineIter(lines)

    line = lines.next()
    if line != "StartFontMetrics 3.0":
        raise ParseError, "unknown file format"

    header = {}
    char_metrics = None
    
    for line in lines:
        parts = line.split(None, 1)
        tag = parts[0]
        if len(parts) > 1:
            data = parts[1]

        if tag == "EndFontMetrics":
            return header, char_metrics
        elif tag == "Comment":
            if "comments" in header:
                header["comments"] += "\n" + data
            else:
                header["comments"] = data
        elif tag == "StartCharMetrics":
            char_metrics = parseAfmCharMetrics(lines)
        elif tag == "StartKernData":
            # kern_data = parse_kern_data(lines)
            while line != "EndKernData":
                line = lines.next()
        elif tag == "StartComposites":
            # composites = parse_composites(lines)
            while line != "EndComposites":
                line = lines.next()
        elif tag in ("ItalicAngle", ):
            header[tag] = float(data)
        elif tag in ("IsFixedPitch", ):
            if data == "true":
                header[tag] = True
            elif data == "false":
                header[tag] = False
            else:
                raise ParseError, "unknown boolean value '%s'" % value
        elif tag in ("UnderlinePosition", "UnderlineThickness",
                     "CapHeight", "XHeight", "Descender", "Ascender", ):
            header[tag] = int(data)
        elif tag in ("FontBBox", ):
            header[tag] = tuple(map(int, data.split()))
        else:
            header[tag] = data

    raise ParseError, "missing EndFontMetrics"


#-----------------------------------------------------------------------

def getFontMetrics(family):
    # If metrics for this font are not already loaded, load them.
    if family not in getFontMetrics.cache:
        # No, we need to load them.  Construct a path to the AFM file.
        try:
            ps_font_name = font_map[family]
        except KeyError:
            raise ValueError, "unknown font family '%s'" % family
        afm_path = os.path.join(font_dir_path, ps_font_name + ".afm")
        # Check that the file is there.
        if not os.path.isfile(afm_path):
            raise ValueError, "no metrics for font family '%s'" % family
        # Load them. 
        header, glyph_map = parseAfm(file(afm_path))
        # Also construct a map indexed by code point (for encoded
        # glyphs). 
        code_map = dict([ (v[0], (k, v[1], v[2]))
                          for (k, v) in glyph_map.items()
                          if v[0] != -1 ])
        getFontMetrics.cache[family] = header, glyph_map, code_map

    return getFontMetrics.cache[family]


getFontMetrics.cache = {}


def getGlyphExtent(glyph_name, font):
    """Return extents of a rendered glyph.

    returns -- '(width, height, depth)' of 'glyph_name' rendered in
    'font' and 'size'."""

    family, size = font
    header, glyph_map, code_map = getFontMetrics(family)
    code_point, char_width, bounding_box = glyph_map[glyph_name]
    scale = size / 1000
    return char_width * scale, \
           bounding_box[3] * scale, \
           bounding_box[1] * scale


def getTextExtent(text, font):
    """Return extents of rendered text.

    returns -- '(width, height, depth)' of 'text' rendered in 'font' and
    'size'."""
    
    family, size = font
    # Get font metrics.
    header, glyph_map, code_map = getFontMetrics(family)

    width = 0
    height = 0
    depth = 0
    # Scan over the text.
    for character in text:
        # Get metrics for this character.
        try:
            glyph_name, char_width, bounding_box = \
                code_map[ord(character)]
        except KeyError:
            # FIXME
            print >> sys.stderr, \
                  "WARNING: no metrics for character %d" % ord(character)
            continue
        # Update the sizes.
        width += char_width
        height = max(bounding_box[3], height)
        depth = max(-min(bounding_box[1], 0), depth)
    # Sizes are specified as a per-mil fraction of the font size, so
    # scale appropriately.
    scale = size / 1000
    return width * scale, height * scale, depth * scale


def getSymbolExtent(symbol, font):
    """Return the extent of a symbol.

    returns -- '(width, height, depth)' of 'symbol' rendered in 'font'
    (or the appropriate corresponding symbol font) and 'size'."""

    family, size = font
    # Look up the symbol in the map.
    glyph_family, glyph_name = symbol_map[symbol]
    # If the font is 'None', that means we use the normal text font.
    if glyph_family is None:
        glyph_family = family
    # Get the extent of the symbol glyph.
    return getGlyphExtent(glyph_name, (glyph_family, size))


