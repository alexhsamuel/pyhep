#--------------------------------------------------*- coding: Latin1 -*-
#
# latex.py
#
# Copyright 2005 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Tools for generating LaTeX source."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import division

from   hep.fn import enumerate
import hep.num
from   math import *
import random
import re

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def escape(text):
    # FIXME
    return text


def _magnitude(value):
    """Return the order-of-magnitude of 'value'."""

    if value == 0:
        return -1000
    else:
        return int(floor(log10(abs(value))))


def _makeTag():
    """Return a random alphabetic tag string."""

    # Construct a string of five random upper-case letters.  There are
    # about 12 million such strings.
    return "".join(
        [ chr(random.randint(ord("A"), ord("Z"))) for i in range(5) ])


def _undefine(command):
    """Generate code to undefine 'command'."""

    assert command.startswith("\\")
    return "\\let%s\\undefined\n" % command


#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Column:
    """Base class for table columns."""


    def __init__(self, title):
        self.title = title
        self.rows = []
        

    def append(self, value):
        self.rows.append(value)


    def generateSetup(self, table):
        return ""
    

    def generateTitle(self):
        return self.title


    def generateRow(self, index):
        raise NotImplementedError


    def generateCleanup(self):
        return ""



#-----------------------------------------------------------------------

class TextColumn(Column):
    """Basic table column.

    The value of each cell is simply the LaTeX source to place in the
    cell."""
    

    def __init__(self, title, alignment="left", title_alignment=None):
        """Construct a basic table column.

        'alignment' -- The column alignment; one of '"left"',
        '"center"', or '"right"'."""

        if alignment not in ("left", "center", "right"):
            raise ValueError, "unknown alignment %r" % alignment
        if title_alignment not in (None, "left", "center", "right"):
            raise ValueError, "unknown title alignment %r" \
                  % title_alignment
        Column.__init__(self, title)
        self.alignment = alignment
        self.title_alignment = title_alignment
        self.specification = alignment[0]
        

    def generateTitle(self):
        if self.title_alignment is None:
            return self.title
        else:
            return "\\multicolumn{1}{%s}{%s}" \
                   % (self.title_alignment[0], self.title)
    

    def generateRow(self, row_index):
        return self.rows[row_index]



#-----------------------------------------------------------------------

class PatternColumn(Column):
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


    # All cells should be the same width, so this shouldn't matter.
    specification = "c"


    def __init__(self, title, pattern):
        """Create a column with 'pattern'."""

        Column.__init__(self, title)

        # Split the pattern into alternating fixed text and patterns.
        parts = re.split("\|([<->][^|]+)\|", pattern)
        # There should be an odd number of parts, beginning and ending
        # with fixed text.
        assert len(parts) % 2 == 1
        # Divide the parts into fixed text and patterns.
        self.fixed = [ parts[i] for i in range(0, len(parts), 2) ]
        patterns = [ parts[i] for i in range(1, len(parts), 2) ]
        # Each pattern should start with an alingment character.
        for pattern in patterns:
            if pattern[0] not in "<->":
                raise ValueError, \
                      "pattern %r doesn't missing alignment character" \
                      % pattern[0]
        # Split off alignment characters.
        self.patterns = [ (p[0], p[1 :]) for p in patterns ]

        tag = _makeTag()
        # Construct a name for the cell formatting command.
        self.format_command = "\\" + tag
        

    def append(self, values):
        # Make sure the number of values is correct.
        if len(values) != len(self.patterns):
            raise ValueError, "%d values specified for %d patterns" \
                  % (len(values), len(self.patterns))
        # Store them.
        Column.append(self, values)


    def generateSetup(self, table):
        num_patterns = len(self.patterns)

        # Build the lengths for the patterns.
        setup = ""
        lengths = []
        for pattern in self.patterns:
            length, length_setup = table._lengthFromPattern(pattern)
            lengths.append[length]
            setup += length_setup
        # Build the cell formatting command.
        setup += "\\newcommand{%s}[%d]{" \
                 % (self.format_command, num_patterns)
        for i in xrange(num_patterns):
            setup += self.fixed[i]
            alignment, pattern = self.patterns[i]
            length = lengths[i]
            alignment_char = { "<": "l", "-": "s", ">": "r" }[alignment]
            setup += "\\makebox[%s][%s]{#%d}" \
                     % (length, alignment_char, i + 1)
        setup += self.fixed[-1]
        setup += "}\n"

        return setup


    def generateTitle(self):
        return "\\multicolumn{1}{c}{%s}" % self.title
    

    def generateRow(self, row_index):
        values = self.rows[row_index]
        # Use the formatting command.
        return self.format_command \
               + "".join([ "{%s}" % v for v in values ]) 



#-----------------------------------------------------------------------

class NumberColumn(Column):
    """A column for displaying numbers."""


    # The cells are aligned with fixed-width fields.  Center the column
    # as a whole so it spaces better and centers relative to the title.
    specification = "c"


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

        # Validate arguments.
        if exponent is not None \
           and exponent != "%" \
           and not isinstance(exponent, int):
            raise ValueError, "unrecognized exponent %r" % exponent

        Column.__init__(self, title)
        self.digits = decimal_places
        self.exponent = exponent

        # Compute a scale to factor out the common exponent.
        if exponent is None:
            self.exponent_factor = 1
        elif exponent == "%":
            self.exponent_factor = 100
        else:
            self.exponent_factor = 10 ** -exponent

        # Generate the prefix for each cell entry.  
        self.prefix = ""
        # If a common exponent is used, group the value and uncertainty
        # in parentheses. 
        if exponent is not None and exponent != "%":
            self.prefix += "("

        # Generate the suffix for each cell entry.
        self.suffix = ""
        if self.exponent == "%":
            self.suffix += "\\%"
        elif self.exponent is not None:
            # For a common exponent, close the parentheses and indicate
            # the exponent.
            self.suffix += ")$\\times 10^{%d}$" % exponent

        # Construct LaTeX command names for the lengths and commands we
        # will use.
        tag = _makeTag()
        self.format_cmd = "\\" + tag

        # Keep track of the largest order of magnitude of the values in
        # the column, and whether the values are signed. 
        self.mag = 0
        self.sign = False


    def append(self, number):
        # Scale the value to factor out the common exponent.
        statistic = float(number) * self.exponent_factor
        # Append it.
        Column.append(self, statistic)

        # Keep track of the order of magnitude of the largest value and
        # error in the column.
        self.mag = max(self.mag, _magnitude(number))
        if number < 0:
            self.sign = True


    def generateSetup(self, table):
        pattern = (1 + self.mag) * "0" + "." + (self.digits) * "0"
        if self.sign:
            pattern = "+" + pattern
        pattern = "$" + pattern + "$"

        length, setup = table._lengthFromPattern(pattern)
        setup += "\\newcommand{%s}[1]" % self.format_cmd \
                 + "{\\makebox[%s][r]{$#1$}}\n" % length

        return setup


    def generateTitle(self):
        return "\\multicolumn{1}{c}{%s}" % self.title
    

    def generateRow(self, row_index):
        number = self.rows[row_index]

        return self.prefix \
               + "%s{%.*f}" % (self.format_cmd, self.digits,
                               round(number, self.digits)) \
               + self.suffix



#-----------------------------------------------------------------------

class StatisticColumn(Column):
    """A column for displaying statistic objects.

    A statistic has an 'uncertainty' attribute containing statistical
    uncertainty.  See the class 'hep.num.Statistic'."""


    # The cells are aligned with fixed-width fields.  Center the column
    # as a whole so it spaces better and centers relative to the title.
    specification = "c"


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

        # Validate arguments.
        if exponent is not None \
           and exponent != "%" \
           and not isinstance(exponent, int):
            raise ValueError, "unrecognized exponent %r" % exponent

        Column.__init__(self, title)
        self.val_digits = value_digits
        self.unc_digits = uncertainty_digits
        self.exponent = exponent

        # Compute a scale to factor out the common exponent.
        if exponent is None:
            self.exponent_factor = 1
        elif exponent == "%":
            self.exponent_factor = 100
        else:
            self.exponent_factor = 10 ** -exponent

        # Generate the prefix for each cell entry.  
        self.prefix = ""
        # If a common exponent is used, group the value and uncertainty
        # in parentheses. 
        if exponent is not None:
            self.prefix += "("

        # Generate the suffix for each cell entry.
        self.suffix = ""
        if exponent is not None:
            # For a common exponent, close the parentheses and indicate
            # the exponent.
            self.suffix += ")"
            if self.exponent == "%":
                self.suffix += "\\%"
            else:
                self.suffix += "$\\times 10^{%d}$" % exponent

        # Construct LaTeX command names for the lengths and commands we
        # will use.
        tag = _makeTag()
        self.format_cmd = "\\" + tag

        # Keep track of the largest order of magnitude of the values and
        # uncertainties in the column, and whether the values are signed.
        self.val_mag = 0
        self.unc_mag = 0
        self.sign = False

        
    def append(self, statistic):
        # Scale the value to factor out the common exponent.
        statistic = hep.num.Statistic(statistic) * self.exponent_factor
        # Append it.
        Column.append(self, statistic)

        # Keep track of the order of magnitude of the largest value and
        # error in the column.
        val_mag = _magnitude(float(statistic))
        self.val_mag = max(self.val_mag, val_mag)
        unc_mag = _magnitude(statistic.uncertainty)
        self.unc_mag = max(self.unc_mag, unc_mag)
        if statistic < 0:
            self.sign = True


    def generateSetup(self, table):
        setup = ""

        pattern = (1 + self.val_mag) * "0" \
                  + "." + (self.val_digits) * "0"
        if self.sign:
            pattern = "+" + pattern
        pattern = "$" + pattern + "$"
        val_length, length_setup = table._lengthFromPattern(pattern)
        setup += length_setup

        pattern = (1 + self.unc_mag) * "0" \
                  + "." + (self.unc_digits) * "0"
        pattern = "$" + pattern + "$"
        unc_length, length_setup = table._lengthFromPattern(pattern)
        setup += length_setup

        setup += "\\newcommand{%s}[2]" % self.format_cmd \
                 + "{\\makebox[%s][r]{$#1$} $\\pm$ \\makebox[%s][r]{$#2$}}\n" \
                 % (val_length, unc_length)

        return setup


    def generateTitle(self):
        return "\\multicolumn{1}{c}{%s}" % self.title
    

    def generateRow(self, row_index):
        statistic = self.rows[row_index]

        return self.prefix \
               + "%s{%.*f}{%.*f}" \
                 % (self.format_cmd,
                    self.val_digits,
                    round(float(statistic), self.val_digits),
                    self.unc_digits,
                    round(statistic.uncertainty, self.unc_digits)) \
               + self.suffix



#-----------------------------------------------------------------------

class Table:
    """A LaTeX table.

    To generate LaTeX for a table, create a 'Table' instance, add rows
    with the 'append' method, and then call 'generate' for the LaTeX
    source.""" 


    line_command = "\\hline"


    def __init__(self, *columns):
        """Create a table.

        '*columns' -- Instances of subclasses of 'Column'."""

        if len(columns) == 0:
            raise ValueError, "specify at least one column"
        self.columns = list(columns)


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
        """Return LaTeX source for the table."""

        # All columns should have the same number of rows.
        num_rows = len(self.columns[0].rows)
        for column in self.columns:
            assert len(column.rows) == num_rows

        # Generate setup commands.
        self.__patterns = {}
        result = "".join([ c.generateSetup(self) for c in self.columns ])
        # Start the tabular environment.
        specification = "".join(
            [ c.specification for c in self.columns ])
        result += "\\begin{tabular}{%s}\n" % specification
        # Write the header.
        result += \
            " & ".join([ c.generateTitle() for c in self.columns ]) \
            + "\\\\\n%s\n" % self.line_command
        # Write the rows.
        for r in xrange(num_rows):
            result += " & ".join(
                [ c.generateRow(r) for c in self.columns ]) \
                + "\\\\\n"
        # End the table.
        result += "\\end{tabular}\n"
        # Generate cleanup commands.
        result += "".join([ c.generateCleanup() for c in self.columns ])
        for length in self.__patterns.values():
            result += _undefine(length)

        return result


    def _lengthFromPattern(self, pattern):
        """Generate code for to create 'length', as wide as 'pattern'."""

        if pattern not in self.__patterns:
            length = "\\" + _makeTag()
            setup_commands = "\\newlength{%s}" % length \
                + "\\settowidth{%s}{%s}\n" % (length, pattern)
            self.__patterns[pattern] = length
            return length, setup_commands
        else:
            return self.__patterns[pattern], ""


