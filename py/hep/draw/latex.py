#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

from   __init__ import *
from   fonts import *

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

math_rm_font = "Times"
math_it_font = "Times-Italic"


# Text-mode escapes that are printed literally.
literal_escapes = [ "\\#", "\\%", "\\\\", "\\{", "\\}", "\\&", "\\$", ]


# Math-mode spacing escapes mapped to a faction of the standard space
# width. 
math_spacing_escapes = {
    "\\,": 0.4,
    "\\:": 0.6,
    "\\;": 0.8,
    "\\ ": 1.0,
    }


# Math-mode escapes to be printed literally in roman text.
math_roman_escapes = (
    "\\arccos",
    "\\arcsin",
    "\\arctan",
    "\\arg",
    "\\cos",
    "\\cosh",
    "\\cot",
    "\\coth",
    "\\csc",
    "\\deg",
    "\\det",
    "\\dim",
    "\\exp",
    "\\gcd",
    "\\hom",
    "\\inf",
    "\\ker",
    "\\lg",
    "\\lim",
    "\\liminf",
    "\\limsup",
    "\\ln",
    "\\log",
    "\\max",
    "\\min",
    "\\Pr",
    "\\sec",
    "\\sin",
    "\\sinh",
    "\\sup"
    "\\tan",
    "\\tanh",
    )


# Characters that should be displayed as symbols in math mode.  
math_symbols = {
    "-":              "minus",
    }


# Characters that should be displayed in italics in math mode.
math_italic_chars = "abcdefghijklmnopqrstuvwxyz" \
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


# Map math-mode escapes to symbol names and whether to display them in
# italics. 
math_symbol_escapes = {
    "\\alpha":        ("alpha", True),
    "\\beta":         ("beta", True),
    "\\gamma":        ("gamma", True),
    "\\delta":        ("delta", True),
    "\\epsilon":      ("epsilon", True),
    "\\zeta":         ("zeta", True),
    "\\eta":          ("eta", True),
    "\\theta":        ("theta", True),
    "\\vartheta":     ("vartheta", True),
    "\\iota":         ("iota", True),
    "\\kappa":        ("kappa", True),
    "\\lambda":       ("lambda", True),
    "\\mu":           ("mu", True),
    "\\nu":           ("nu", True),
    "\\xi":           ("xi", True),
    "\\omicron":      ("omicron", True),
    "\\pi":           ("pi", True),
    "\\varpi":        ("varpi", True),
    "\\rho":          ("rho", True),
    "\\varsigma":     ("varsigma", True),
    "\\sigma":        ("sigma", True),
    "\\tau":          ("tau", True),
    "\\upsilon":      ("upsilon", True),
    "\\phi":          ("phi", True),
    "\\varphi":       ("varphi", True),
    "\\chi":          ("chi", True),
    "\\psi":          ("psi", True),
    "\\omega":        ("omega", True),

    "\\Alpha":        ("Alpha", True),
    "\\Beta":         ("Beta", True),
    "\\Gamma":        ("Gamma", True),
    "\\Delta":        ("Delta", True),
    "\\Epsilon":      ("Epsilon", True),
    "\\Zeta":         ("Zeta", True),
    "\\Eta":          ("Eta", True),
    "\\Theta":        ("Theta", True),
    "\\Iota":         ("Iota", True),
    "\\Kappa":        ("Kappa", True),
    "\\Lambda":       ("Lambda", True),
    "\\Mu":           ("Mu", True),
    "\\Nu":           ("Nu", True),
    "\\Xi":           ("Xi", True),
    "\\Omicron":      ("Omicron", True),
    "\\Pi":           ("Pi", True),
    "\\Rho":          ("Rho", True),
    "\\Sigma":        ("Sigma", True),
    "\\Tau":          ("Tau", True),
    "\\Upsilon":      ("Varupsilon", True),
    "\\Phi":          ("Phi", True),
    "\\Chi":          ("Chi", True),
    "\\Psi":          ("Psi", True),
    "\\Omega":        ("Omega", True),

    "\\Im":           ("Im", False),
    "\\Re":           ("Re", False),
    "\\approx":       ("approx", False),
    "\\ast":          ("ast", False),
    "\\bullet":       ("bullet", False),
    "\\cdot":         ("cdot", False),
    "\\dagger":       ("dagger", False),
    "\\ddagger":      ("ddagger", False),
    "\\degree":       ("degree", False),
    "\\del":          ("del", False),
    "\\div":          ("div", False),
    "\\downarrow":    ("downarrow", False),
    "\\equiv":        ("equiv", False),
    "\\geq":          ("geq", False),
    "\\infty":        ("infty", False),
    "\\leftarrow":    ("leftarrow", False),
    "\\leq":          ("leq", False),
    "\\nabla":        ("nabla", False),
    "\\neq":          ("neq", False),
    "\\pm":           ("pm", False),
    "\\prime":        ("prime", False),
    "\\propto":       ("propto", False),
    "\\rightarrow":   ("rightarrow", False),
    "\\sim":          ("sim", False),
    "\\times":        ("times", False),
    "\\uparrow":      ("uparrow", False),
}


#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class PeekIterator(object):

    def __init__(self, iterator):
        self.__iterator = iterator
        self.peek = None
        self.is_finished = False
        self.__getNext()


    def __getNext(self):
        try:
            self.peek = self.__iterator.next()
        except StopIteration:
            self.is_finished = True
            self.peek = None


    def next(self):
        if self.is_finished:
            raise StopIteration
        else:
            element = self.peek
            self.__getNext()
            return element
        


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def isLetter(character):
    code = ord(character)
    return 65 <= code <= 90 or 97 <= code <= 122 


def tokenize(text):
    i = 0
    length = len(text)

    while i < length:
        if text[i] == "\\":
            token = text[i : i + 2]
            i += 2
            if isLetter(token[1]):
                while i < length and isLetter(text[i]):
                    token += text[i]
                    i += 1
            yield token
        elif text[i] == "%":
            i += 1
            while i < length and text[i] != "\n":
                i += 1
            i += 1
            continue
        elif text[i] in " \t\n":
            linefeeds = 0
            while i < length and text[i] in " \t\n":
                if text[i] == "\n":
                    linefeeds += 1
                i += 1
            if linefeeds > 1:
                yield "\n"
            else:
                yield " "
        elif isLetter(text[i]):
            token = ""
            while i < length and isLetter(text[i]):
                token += text[i]
                i += 1
            yield token
        else:
            token = text[i]
            i += 1
            yield token


def renderMath(renderer, x, y, tokens, font_size, style):
    # Handle blocks.
    if tokens.peek == "{":
        tokens.next()
        x, y = renderMathBlock(
            renderer, x, y, tokens, font_size, style)
        if tokens.next() != "}":
            raise ParseError, "missing closing }"

    # Handle superscripts.
    elif tokens.peek == "^":
        tokens.next()
        # Apply poor-man's italic correction.
        # FIXME: Do this better.
        x += 0.1 * font_size
        x, ignore_y = renderMath(
            renderer, x, y + 0.35 * font_size, tokens, 0.8 * font_size,
            style)

    # Handle subscripts.
    elif tokens.peek == "_":
        tokens.next()
        x, ignore_y = renderMath(
            renderer, x, y - 0.25 * font_size, tokens, 0.8 * font_size,
            style)

    # Handle characters that are drawn as symbols.
    elif tokens.peek in math_symbols:
        token = tokens.next()
        symbol_name = math_symbols[token]
        renderer.font = (math_rm_font, font_size)
        renderer.symbol((x, y), symbol_name)
        x += getSymbolExtent(symbol_name, renderer.font)[0]

    # Handle escapes.
    elif tokens.peek[0] == "\\":
        escape = tokens.next()

        if escape in math_spacing_escapes:
            width = math_spacing_escapes[escape]
            font = (math_rm_font, font_size)
            x += width * getTextExtent(" ", font)[0]

        # Handle escapes that are drawn as roman text.
        elif escape in math_roman_escapes:
            text = escape[1 :] + " "
            renderer.font = (math_rm_font, font_size)
            renderer.text((x, y), text, (0, 0))
            x += getTextExtent(text, renderer.font)[0]

        # Handle escapes that are drawn as symbols.
        elif escape in math_symbol_escapes:
            symbol_name, italic = math_symbol_escapes[escape]
            if italic:
                font_family = math_it_font
            else:
                font_family = math_rm_font
            renderer.font = (font_family, font_size)
            renderer.symbol((x, y), symbol_name)
            x += getSymbolExtent(symbol_name, renderer.font)[0]

        elif escape in literal_escapes:
            text = escape[1 :]
            renderer.font = (math_rm_font, font_size)
            renderer.text((x, y), text, (0, 0))
            x += getTextExtent(text, renderer.font)[0]

        else:
            raise ParseError, "unrecognized escape '%s'" % escape

    # Skip whitespace.
    elif tokens.peek in (" ", "\n", ):
        tokens.next()
        
    # Write out everything else.
    else:
        text = tokens.next()
        if isLetter(text[0]):
            # Alphabetic text is written in italics.
            font_family = math_it_font
        else:
            # Everything else in roman.
            font_family = math_rm_font
        renderer.font = (font_family, font_size)
        renderer.text((x, y), text, (0, 0))
        x += getTextExtent(text, renderer.font)[0]

    return x, y
            

def renderMathBlock(renderer, x, y, tokens, font_size, style):
    while True:
        if tokens.is_finished:
            raise ParseError, "missing closing $"
        elif tokens.peek in ("$", "}", ):
            return x, y
        else:
            x, y = renderMath(renderer, x, y, tokens, font_size, style)
    return x, y


def renderDash(renderer, x, y, tokens, font, style):
    assert tokens.peek == "-"
    tokens.next()
    if tokens.peek == "-":
        tokens.next()
        if tokens.peek == "-":
            tokens.next()
            symbol = "emdash"
        else:
            symbol = "endash"
    else:
        symbol = "hyphen"
    renderer.font = font
    renderer.symbol((x, y), symbol)
    font_family, font_size = font
    x += getSymbolExtent(symbol, font)[0]
    return x, y


def renderBraceBlock(renderer, x, y, tokens, font, style):
    token = tokens.next()
    assert token == "{"
    x, y = renderBlock(renderer, x, y, tokens, font, style)
    token = tokens.next()
    if token != "}":
        raise ParseError, "missing closing }"
    return x, y


def renderBlock(renderer, x, y, tokens, font, style):
    font_family, font_size = font

    while True:

        if tokens.is_finished or tokens.peek == "}":
            return x, y

        elif tokens.peek == "{":
            x, y, = renderBraceBlock(renderer, x, y, tokens, font, style)

        elif tokens.peek == "$":
            tokens.next()
            x, y = renderMathBlock(
                renderer, x, y, tokens, font_size, style)
            if tokens.next() != "$":
                raise ParseError, "missing closing $"

        elif tokens.peek == "-":
            x, y = renderDash(
                renderer, x, y, tokens, font, style)

        elif tokens.peek[0] == "\\":
            token = tokens.next()

            if token in literal_escapes:
                text = token[1 :]
                renderer.font = font
                renderer.text((x, y), text, (0, 0))
                x += getTextExtent(text, font)[0]
                
        else:
            token = tokens.next()
            renderer.font = font
            renderer.text((x, y), token, (0, 0))
            x += getTextExtent(token, font)[0]


class ExtentsRenderer:

    def __init__(self):
        self.__x_min = None
        self.__y_min = None
        self.__x_max = None
        self.__y_max = None
        self.transformation_stack = []
        self.__font = None


    def __include(self, x, y):
        if self.__x_min is None or x < self.__x_min:
            self.__x_min = x
        if self.__x_max is None or x > self.__x_max:
            self.__x_max = x
        if self.__y_min is None or y < self.__y_min:
            self.__y_min = y
        if self.__y_max is None or y > self.__y_max:
            self.__y_max = y


    def transform(self, transformation):
        self.transformation_stack.insert(0, transformation)


    def untransform(self):
        self.transformation_stack.pop(0)


    def map(self, point):
        for transformation in self.transformation_stack:
            point = transformation(point)
        return point


    def text(self, position, text, alignment):
        x, y = self.map(position)
        x_alignment, y_alignment = alignment
        width, height, depth = getTextExtent(text, self.font)
        self.__include(x - x_alignment * width,
                       y - y_alignment * height)
        self.__include(x + (1 - x_alignment) * width,
                       y + (1 - y_alignment) * height)


    def symbol(self, position, symbol):
        x, y = self.map(position)
        width, height, depth = getSymbolExtent(symbol, self.font)
        self.__include(x, y)
        self.__include(x + width, y + height)


    extents = property(lambda self: (self.__x_min, self.__y_min,
                                     self.__x_max, self.__y_max))



def render(renderer, position, text, style, alignment):
    if text == "":
        return
    
    font_family = math_rm_font
    font_size = style.get("font_size", 10 * point)
    font = (font_family, font_size)
    color = style.get("color", colors["black"])

    x, y = position
    if alignment != (0, 0):
        # Compute the extents of the text by rendering it.
        tokens = PeekIterator(tokenize(text))
        extents_renderer = ExtentsRenderer()
        renderBlock(extents_renderer, x, y, tokens, font, style)
        x0, y0, x1, y1 = extents_renderer.extents
        
        # Align text by adjusting its position.
        x_alignment, y_alignment = alignment
        # For x alignment, use the rendered width of the text.
        x -= x_alignment * (x1 - x0)
        # For y alignment, estimate the character height of the font
        # size.
        y -= y_alignment * 0.8 * font_size

    renderer.color = color
    tokens = PeekIterator(tokenize(text))
    renderBlock(renderer, x, y, tokens, font, style)

    if tokens.peek == "}":
        raise ParseError, "extra closing }"


def scientificNotation(value, decimal_places):
    if value == 0:
        return "0"
    scale = log10(abs(value))
    exponent = int(floor(scale))
    mantissa = value / 10 ** exponent
    return r"%.*f\times 10^{%d}" % (decimal_places, mantissa, exponent)


def formatStatistic(statistic, value_digits=4, error_digits=None):
    """Return a nice string representation of 'statistic'.

    returns -- LaTeX markup for 'statistic'.  Must be used in math mode."""

    if error_digits is None:
        error_digits = int(ceil(value_digits / 2)) + 1
    return r"%s\pm%s" \
           % (formatNumber(statistic, value_digits),
              formatNumber(statistic.uncertainty, error_digits))


def formatNumber(number, significant_digits=4):
    """Return a nice string representation of floating-point 'number'."""

    number = float(number)

    # If all the significant digits are to the left of the decimal
    # point (or if 'number' is an integer), use an integer
    # representation. 
    if abs(number) > (10 ** (significant_digits - 1)) \
       or int(number) == number:
        return "%d" % int(round(number))

    if abs(number) < 1e-4:
        # Format small numbers in exponential notation.
        result = scientificNotation(number, significant_digits)
    else:
        # For other numbers, figure out the required precision.
        scale = int(log10(abs(number)))
        if abs(number) < 1:
            decimal_places = significant_digits - scale
        else:
            decimal_places = significant_digits - scale - 1
        result = ("%%.%df" % decimal_places) % number
    # Don't end with a decimal point.
    if result[-1] == '.':
        result = result[:-1]

    return result


