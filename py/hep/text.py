#--------------------------------------------------*- coding: Latin1 -*-
#
# text.py
#
# Copyright 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Text-related functions."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

import hep.fn
from   math import log10
import re
import sys

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def pad(text, width, pad_character=" "):
    """Pad 'text' to a field of 'width' characters.

    'width' -- The desired size of the padded field.  If negative, the
    text is left-justified in the field; if positive, the text is
    right-justified.

    'pad_character' -- The character to use for padding.

    returns -- The padded text.  If the lenght of 'text' is greater than
    'width', returns 'text'."""

    length = len(text)
    if width < 0 and length < -width:
        return text + (-width - length) * pad_character
    elif width > 0 and length < width:
        return (width - length) * pad_character + text
    else:
        return text


def center(text, width=72, pad_character=" "):
    """Center 'text' in a field.

    Like 'pad', but centers 'text' in the field."""

    length = len(text)
    prefix = (width - length) // 2
    suffix = width - prefix - length
    return (prefix * " ") + text + (suffix * " ")


def indent(text, indentation, width=None, pad_character=" "):
    """Indent 'text', and optionally right-pad it to 'width'."""

    text = pad_character * indentation + text
    length = len(text)
    if width is None or length >= width:
        return text
    else:
        return text + pad_character * (width - length)


def abbreviator(max_length):
    """Return a function that abbreviates text to 'max_length' characters.

    If the text is too long, the abbreviate function will truncate it
    and append "...".
    """
    
    def abbreviate(text):
        if len(text) <= max_length:
            return text
        else:
            return text[: max_length - 3] + "..."

    return abbreviate


def buildDictFromParagraphs(input, separator, parser=None):
    separator = re.compile(separator)

    key = None
    result = {}

    def finish():
        if key is not None:
            result[key] = parser(buffer)

    for line in input:
        match = separator.match(line)
        if match is not None:
            finish()
            key = match.group(1).strip()
            buffer = []

        elif key is not None:
            buffer.append(line)

    finish()

    return result


def percent(numerator, denominator, decimal_places=2):
    """Format 'numerator / denominator' as a percentage."""

    if denominator == 0:
        fraction = 0
    else:
        fraction = 100 * numerator / denominator
    if hasattr(fraction, "uncertainty"):
        return "(%*.*f ± %*.*f)%%" \
               % (4 + decimal_places, decimal_places,
                  float(fraction),
                  3 + decimal_places, decimal_places,
                  fraction.uncertainty)
    else:
        return "%*.*f%%" \
               % (4 + decimal_places, decimal_places, fraction)


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
        result = ("%%.%dE" % (significant_digits - 1)) % number
    elif abs(number) < 1:
        # For other numbers, figure out the required precision.
        scale = int(log10(abs(number)))
        result = ("%%.%df" % (significant_digits - scale)) % number
    else:
        # For other numbers, figure out the required precision.
        scale = int(log10(abs(number)))
        result = ("%%.%df" % (significant_digits - scale - 1)) % number
    # Trim off trailing zeros to the right of the decimal point.
    while result[-1] == '0':
        result = result[:-1]
    # Don't end with a decimal point.
    if result[-1] == '.':
        result = result[:-1]

    return result


#-----------------------------------------------------------------------

def writeDictAsHeader(dictionary, write=sys.stdout.write,
                      label_indent=None):
    if label_indent:
        label_format = "%%-%ds: " % label_indent
    else:
        label_format = "%s: "
    for key in dictionary:
        label = label_format % key
        value = repr(dictionary[key])
        write(label + value + "\n")


def readDictAsHeader(lines):
    result = {}
    for line in lines:
        key, value = line.split(":", 1)
        result[key.strip()] = eval(value)
    return result


def parseSloppily(text):
    """Sloppily parse 'text' into Python data.

    Comma-delimited sequences are converted to lists (with elements
    converted recursively).  Otherwise,
    this function attempts to convert 'text' to the following data
    types, in order: 'int', 'long', 'float', 'str'."""

    text = text.strip()
    if "," in text:
        parts = text.split(",")
        # Does each part include a colon?
        if hep.fn.firstIndex(parts, lambda p: ":" not in p) == -1:
            # Yes.  Handle it as a dictionary.
            return dict([ map(parseSloppily, part.split(":", 1))
                          for part in parts ])
        else:
            # No.  Just a list.
            return map(parseSloppily, filter(None, parts))
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return long(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return str(text)


def formatSloppily(data):
    """Inverse operation of 'parseSloppily'."""

    if isinstance(data, str) or isinstance(data, unicode):
        return data
    elif hasattr(data, "get") and hasattr(data, "keys"):
        # Write it as a comma-separted list, with colons separating keys
        # and values.
        return ", ".join(
            [ "%s: %s" % (formatSloppily(k), formatSloppily(data[k]))
              for k in data.keys() ])
    elif hasattr(data, "__len__"):
        # Write it as a comma-separated sequence.
        return ", ".join(map(formatSloppily, data))
    else:
        return str(data)


def writeHeaders(map, write=sys.stdout.write):
    """Write a dictionary in a format similar to email headers.

    The keys and values are formatted with 'formatSloppily'.

    'write' -- The 'write' function for writing the headers.  It is
    called once for each key in 'map'."""

    for key in map:
        write("%s: %s\n" % (key, formatSloppily(map[key])))


def readHeaders(lines):
    """Parse headers similar to email headers.

    This function is the inverse of 'writeHeaders'.  Header tags (keys)
    and contents (values) are parsed using 'parseSloppily'.

    'lines' -- An iterable over lines.

    returns -- A dictionary of header contents."""

    result = {}
    for line in lines:
        if line[0] == "#":
            continue
        if line.strip() == "":
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = parseSloppily(value)
    return result


#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Column:
    """Base class for table columns."""


    width = 0


    def __init__(self, title):
        self.title = title
        self.rows = []
        

    def append(self, value):
        self.rows.append(value)


    def generateTitle(self):
        return self.title


    def generateRow(self, index):
        raise NotImplementedError



#-----------------------------------------------------------------------

class LineColumn(Column):

    width = 1

    def __init__(self):
        Column.__init__(self, "")


    def generateRow(self, index):
        return "|"
    


#-----------------------------------------------------------------------

class TextColumn(Column):
    """Basic table column.

    The value of each cell is the text to place in the cell."""
    

    def __init__(self, title, alignment="left"):
        """Construct a basic table column.

        'alignment' -- The column alignment; one of '"left"',
        '"center"', or '"right"'."""

        if alignment not in ("left", "center", "right"):
            raise ValueError, "unknown alignment %r" % alignment
        Column.__init__(self, title)
        self.alignment = alignment
        self.width = len(title)
        

    def append(self, text):
        # Keep track of the widest cell.
        self.width = max(self.width, len(text))
        # Store them.
        Column.append(self, text)


    def generateRow(self, row_index):
        text = self.rows[row_index]
        if self.alignment == "left":
            return pad(text, -self.width)
        elif self.alignment == "right":
            return pad(text, self.width)
        elif self.alignment == "center":
            return text.center(self.width)



#-----------------------------------------------------------------------

class PatternColumn(TextColumn):
    """Table column with cells made from a fixed-width pattern.

    The column is specified by a pattern, which is composed of sections
    of fixed text and zero or more fixed-width slots.  The value for
    each cell should be a tuple of strings, with as many elements as
    their are slots in the pattern.  Corresponding elements are inserted
    into slots in the pattern.  The width of the slot is the same in
    each cell.

    The pattern is composed of LaTeX source, with slots surrounded by
    vertical bars ("|").  The text outside the slots is included in each
    cell.  The first character of a slot is an alignment character, one
    of "<", "-", or ">", specifying that the contents of the slot should
    be left-aligned, justified, or right-aliged, respectively.  The
    remainder in the slot is LaTeX source, whose width (when formatted)
    is used as the width of the slot.  For example, if the slot is
    '"|<XXXXX|"', the contents of the slot will be left-aligned, and the
    slot will be as wide as the string "XXXXX" when formatted.

    For example, here is a pattern for a page number and total number of
    pages, leaving space for three digits: '"page |>000| of |>000|"'.
    """


    def __init__(self, title, pattern, alignment="left"):
        """Create a column with 'pattern'."""

        TextColumn.__init__(self, title, alignment)
        self.pattern = pattern


    def append(self, values):
        # Format the values.
        text = self.pattern % tuple(values)
        # Store them.
        TextColumn.append(self, text)



#-----------------------------------------------------------------------

class NumberColumn(PatternColumn):
    """A column for displaying numbers."""


    def __init__(self, title, decimal_places, exponent=None):
        """Create a new column for numbers.

        Values are rounded to the specified number of 'decimal_places'.
        The 'exponent' is factored out of the value in each cell.  For
        example, if the exponent is -3 and one decimal place is used,
        the value 0.62357 will be displayed as 623.6 x 10^-3.  If
        instead exponent is '"%"', it will be displayed as 62.4%.

        'decimal_places' -- The number of digits after the decimal point
        to show.  

        'exponent' -- A common power-of-ten exponent for values.  Can be
        an integer, '"%"' to show percentages, or 'None'."""

        if exponent is None:
            pattern = "%%.%df" % decimal_places
            self.scale = 1
        elif exponent == "%":
            pattern = "%%.%df%%%%" % decimal_places
            self.scale = 100
        elif isinstance(exponent, int):
            pattern = "%%.%df x10^%d" % (decimal_places, exponent)
            self.scale = 10.0 ** (-exponent)
        else:
            raise ValueError, "unrecognized exponent %r" % exponent

        PatternColumn.__init__(self, title, pattern, "right")


    def append(self, number):
        text = self.pattern % (number * self.scale)
        TextColumn.append(self, text)



#-----------------------------------------------------------------------

class StatisticColumn(PatternColumn):
    """A column for displaying statistic objects.

    A statistic has an 'uncertainty' attribute containing statistical
    uncertainty.  See the class 'hep.num.Statistic'."""


    def __init__(self, title, value_digits, uncertainty_digits,
                 exponent=None):
        """Create a new column for statistics.

        Values and uncertainties are rounded to the specified number of
        digits after the decimal point.  The 'exponent' is factored out
        of the value in each cell.  See 'NumberColumn' for examples.

        'value_digits' -- The number of digits after the decimal point
        to show for the value.

        'uncertainty_digits' -- The number of digits after the decimal
        point to show for the uncertainty.

        'exponent' -- A common power-of-ten exponent for values.  Can be
        an integer, '"%"' to show percentages, or 'None'."""

        if exponent is None:
            pattern = \
                "%%.%df ± %%.%df" % (value_digits, uncertainty_digits)
            self.scale = 1
        elif exponent == "%":
            pattern = "(%%.%df ± %%.%df)%%%%" \
                      % (value_digits, uncertainty_digits)
            self.scale = 100
        elif isinstance(exponent, int):
            pattern = "(%%.%df  ± %%.%df)x10^%d" \
                      % (value_digits, uncertainty_digits, exponent)
            self.scale = 10.0 ** (-exponent)
        else:
            raise ValueError, "unrecognized exponent %r" % exponent

        PatternColumn.__init__(self, title, pattern, "right")

        
    def append(self, number):
        try:
            uncertainty = number.uncertainty
        except:
            value = number
            uncertainty = 0
        else:
            value = float(number)
        scale = self.scale
        text = self.pattern % (value * scale, uncertainty * scale)
        self.width = max(self.width, len(text))
        Column.append(self, text)



#-----------------------------------------------------------------------

class Table:
    """A LaTeX table.

    To generate LaTeX for a table, create a 'Table' instance, add rows
    with the 'append' method, and then call 'generate' for the LaTeX
    source.""" 

    gutter = " "


    def __init__(self, *columns):
        """Create a table.

        '*columns' -- Instances of subclasses of 'Column'."""

        if len(columns) == 0:
            raise ValueError, "specify at least one column"
        self.elements = list(columns)
        self.columns = [ c for c in columns if isinstance(c, Column) ]


    def append(self, *row):
        """Append a row to the table.

        '*row' -- A sequence of values.  There must be one for each
        column."""

        if len(row) != len(self.columns):
            raise ValueError, "row has %d values for %d columns" \
                  % (len(row), len(self.columns))
        # Distribute the values in the row to the columns.
        for column, value in zip(self.columns, row):
            column.append(value)


    def generate(self):
        """Return the formatted table."""

        # All columns should have the same number of rows.
        num_rows = len(self.columns[0].rows)
        for column in self.columns:
            assert len(column.rows) == num_rows

        # Write the header.
        def generateTitle(element):
            if isinstance(element, Column):
                return element.title.center(element.width)
            else:
                return " " * len(element)

        titles = self.gutter.join(
            [ generateTitle(e) for e in self.elements ])
        result = titles + "\n" + len(titles) * "-" + "\n"

        # Write the rows.
        def generateCell(element, r):
            if isinstance(element, Column):
                return element.generateRow(r)
            else:
                return element

        for r in xrange(num_rows):
            line = self.gutter.join(
                [ generateCell(e, r) for e in self.elements ])
            result += line + "\n"

        # End the table.
        result += "\n"

        return result



