#-----------------------------------------------------------------------
#
# module hep.table.reference
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Reference implementation of an on-disk table of values.

A table is an array of values arranged into rows and columns.  Each
column has a name and a type.  All values in the column are of that
type.  A row is referenced by its (zero-offset) index.  Each row
contains a value corresponding to each column.

The column schema of the table is specified when the table is created,
and cannot afterwards be changed.  Rows may be appended to the table,
but not modified, removed, or rearranged.

Table data is stored in a file, which is automatically updated when the
table is changed."""

#----------------------------------------------------------------------
# imports
#----------------------------------------------------------------------

import cPickle
import hep.expr
import hep.expr.parse
import hep.py

#----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Row:
    """A table row.

    A row is always associated with a particular table.  

    The row satifies the map protocol, with elements corresponding to
    columns in the table.  Each key is a column name, and the
    corresponding value is the value of the column in this row.

    Do not instantiate 'Row' objects directly; obtain them from the
    'Table' or an iterator."""

    def __init__(self, table, index, row_list):
        # Remember the table and index.
        self.__table = table
        self.__index = index
        # Store column values.
        self.__columns = {}
        row_list_iter = iter(row_list)
        for column in table.schema.columns:
            self.__columns[column.name] = row_list_iter.next()


    def __getitem__(self, name):
        if name in self.__columns:
            return self.__columns[name]
        elif name in self.table.schema:
            return self.table.schema[name].expression.evaluate(self)
        else:
            raise KeyError, "no column or expression '%s'" % name


    def __setitem__(self, name, value):
        # Make sure 'name' is the name of a column in the table.  All
        # column names should already appear as keys in the dictionary.
        if name not in self.__columns:
            raise KeyError, "no column '%s'" % name
        else:
            # Proceed with changing the column value.
            self.__columns[name] = value
            

    def keys(self):
        return self.table.schema.keys()


    def values(self):
        return [ self[key] for key in self.keys() ]


    def items(self):
        return [ (key, self[key]) for key in self.keys() ]


    def asDict(self):
        """Return a new dictionary of column names and values in this row."""

        result = dict(self.items())


    table = property(lambda self: self.__table)
    """The table to which this row belongs (read-only)."""


    index = property(lambda self: self.__index)
    """The index of this row in the table (read-only)."""
    


class Iterator:
    """An iterator over rows in a table.

    Some iterators return a subset of rows in the table.

    Do not instantiate 'Iterator' directly.  Instead, use the 'rows' or
    '__iter__' method of the table to obtain an instance."""

    def __init__(self, table, selection=None):
        self.__table = table
        # If '__selection' is 'None', iterate over all rows.
        self.__selection = table._compileExpression(selection)
        # The index of the next to return.
        self.__index = 0


    def __iter__(self):
        return self


    def next(self):
        while 1:
            # Have we reached the end of the table?
            if self.__index == len(self.__table):
                # Yes.  Stop iterating.
                raise StopIteration
            # Get the next row.
            row = self.__table[self.__index]
            self.__index += 1

            # Is there a selection function?
            if self.__selection is None:
                # No.  Each row is assumed to be OK.
                selection_result = 1
            # There is a selection.  Does it have an evaluate method?
            # This is our first choice.
            elif hasattr(self.__selection, "evaluate"):
                selection_result = self.__selection.evaluate(row)
            else:
                # No evaluate method.  Call the selection itself,
                # passing the row's fields as keyword arguments.
                selection_result = self.__selection(**row)

            # If the selection returns a true value, return with this row.
            if selection_result:
                return row

            # Otherwise, loop to the next row.
            


class Table(object):
    """A connection to an on-disk table.

    The values in a table are accessed row-wise.  A 'Table' object may
    be used as a read-only sequence of rows.

    If the table is writeable, the 'append' method adds a row to the end
    of the table.  To obtain an empty, unfilled row for the table, get
    the row with index 'None'.

    These attributes may be accessed:

    'schema' -- A 'Schema' object describing the table schema.

    Do not instantiate a 'Table' directly; instead, use the 'create' and
    'open' functions."""


    def __init__(self, path, schema, row_tuples, writeable):
        self.__path = path
        self.__schema = schema
        # Construct a tuple containing an empty row.  The row's value
        # for each column is zero, coerced to the appropriate type.
        self.__empty_row_tuple = tuple(
            [ column.Python_type(0) for column in schema.columns ])
        # Copy the list of row tuples.
        self.__row_tuples = list(row_tuples)
        self.__writeable = not not writeable


    def __del__(self):
        # Write out the table, if writeable.
        if self.__writeable:
            self.__write()


    # Define the 'path' and 'schema' attributes as properties so that
    # they can be made read-only, and so that the only attributes in
    # '__dict__' are user-added.
    path = property(lambda self: self.__path)
    schema = property(lambda self: self.__schema)


    def __iter__(self):
        """Return an iterator over all rows in the table."""

        # Construct an iterator.
        return Iterator(self)


    rows = property(lambda self: Iterator(self))


    def select(self, selection):
        """Return an iterator over rows in the table.

        'selection' -- A callable that takes a table row as its
        argument; the iterator returns only rows for which this returns
        a true value.

        raises -- 'ValueError' if 'selection' is not callable."""

        selection = hep.expr.parse.asExpression(selection)
        return Iterator(self, selection)


    def __len__(self):
        """Return the number of rows in the table."""
        
        return len(self.__row_tuples)


    def __getitem__(self, index):
        """Return a row in the table.

        'index' -- The index of the row to return.

        returns -- A 'Row' object."""

        return Row(self, index, self.__row_tuples[index])


    def newRow(self, **values):
        """Create and return an empty row.

        The row is not automatically added to the table.  Fill the
        values in the row, and use the 'append' method to add it to the
        table.

        'values' -- (Optional) values with which to inialize the row, as
        keyword arguments."""

        row = Row(self, None, self.__empty_row_tuple)
        for key, value in values.items():
            row[key] = value
        return row


    def append(self, map={}, **kw_args):
        """Append a row to the table.

        raises -- 'IOError' if the table is not writeable.

        raises -- 'KeyError' if the value for a column was not
        specified, or if a value was specified for key which is not a
        column name.

        returns -- The row's index in the table.

        The 'index' attribute of 'row' is set to the row's index in the
        table."""

        # Check that the table is writeable.
        if not self.__writeable:
            raise IOError, "table is not writeable"
        # Build a dictionary containing the specified values.
        row = {}
        row.update(map)
        row.update(kw_args)
        # Obtain the index of the new row.
        index = len(self.__row_tuples)
        # Construct a tuple of the row's values.
        row_tuple = tuple([ column.Python_type(hep.remove(row, column.name))
                            for column in self.schema.columns ])
        # Make sure there aren't any columns left.
        if len(row) > 0:
            raise KeyError, row.keys()[0]
        # Store the row.
        self.__row_tuples.append(row_tuple)

        return index


    def __write(self):
        # Write out our state as a pickle.
        pickle = (
            self.schema,
            self.__row_tuples,
            hep.py.getPublicDict(self),
            )
        cPickle.dump(pickle, file(self.path, "w"), 1)


    def _compileExpression(self, expression):
        if isinstance(expression, hep.expr.Expression):
            return expression.copy(self._compileExpression)
        else:
            return expression



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def create(path, schema):
    """Create a new table.

    'path' -- The path at which to write the table file.

    'schema' -- The table schema.

    returns -- A writeable 'Table' object."""

    return Table(path, schema, [], 1)


def open(path, mode="r"):
    """Open an existing table.

    'path' -- The path to the table file.

    'mode' -- The mode with which to open the table.  If "r", the table
    is opened in read-only mode.  If "w", the table is opened to be
    writeable, and additional rows may be appended.

    returns -- A 'Table' object."""

    # Parse the mode.
    if mode == "r":
        writeable = 0
    elif mode == "w":
        writeable = 1
    else:
        raise ValueError, "unknown mode '%s'" % mode
    # Load the table data.
    pickle = cPickle.load(file(path))
    schema, row_tuples, attributes = pickle
    # Construct the table object.
    table = Table(path, schema, row_tuples, writeable)
    table.__dict__.update(attributes)
    return table

