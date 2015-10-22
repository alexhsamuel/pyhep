#-----------------------------------------------------------------------
#
# module hep.table
#
# Copyright 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Data tables."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   __future__ import generators

from   hep.bool import *
import hep.expr
import hep.expr.op
from   hep.ext import Iterator, RowObject, RowDict, Table
from   hep.ext import table_create, table_open 
import hep.fs
from   hep.xml_util import *
import operator
import os
import sys
import weakref

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

# The file extension to use for table files.
extension = ".table"

# For each column type, the Python type used to represent values, and
# the number of bytes the value occupies in the table.
_type_info = {
    "int8":         (int,        1),
    "int16":        (int,        2),
    "int32":        (int,        4),
    "float32":      (float,      4),
    "float64":      (float,      8),
    "complex64":    (complex,    8),
    "complex128":   (complex,   16),
    }

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class CachedExpression(hep.expr.Expression):
    """An expression whose value is cached for each row in a table.

    A 'CachedExpression' instance may be used only for one particular
    table.  For each row in the table, the value of the underlying
    expression is evaluated the first time the 'CachedExpression' is
    evaluated for that row.  On subsequent evaluations, the cached value
    is returned."""

    type = property(lambda self: self.subexprs[0].type)
    subexpr_types = property(hep.expr.Expression._get_subexpr_types)


    def __init__(self, mask, values, expression):
        """Create a new cached expression.

        'mask' -- An array of boolean values, indexed by row index,
        specifying whether the expression has been evaluated for that
        row.

        'values' -- An array of values, indexed by row index, containing
        cached values for rows in the table.  Elements in the array are
        considered valid only if the corresponding element in 'mask' is
        'True'.

        'expression' -- The underlying expression to evaluate."""

        self.cache = mask, values
        self.subexprs = (expression, )


    def __repr__(self):
        return "CachedExpression(%s)" % repr(self.subexprs[0])


    def __str__(self):
        return "cached[%s]" % str(self.subexprs[0])


    def evaluate(self, symbols):
        index = symbols["_index"]
        mask, values = self.cache
        # Do we have a cached value for this row?
        if index < len(mask) and mask[index]:
            # Yes.  Return it.
            return values[index]
        elif index < len(mask):
            # No.  Evaluate the underlying expression.
            value = self.subexprs[0].evaluate(symbols)
            # Set the result in the cache.
            mask[index] = True
            values[index] = value
            # Return the result.
            return value
        else:
            return self.subexprs[0].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, CachedExpression) \
               and self.cache == other.cache \
               and self.subexprs == other.subexprs


    def copy(self, copy_fn=lambda t: t.copy()):
        mask, values = self.cache
        return CachedExpression(
            mask, values, copy_fn(self.subexprs[0]))



#-----------------------------------------------------------------------

class Column:
    """A column in a schema."""

    def __init__(self, name, type, **attributes):
        self.__dict__.update(attributes)
        if type not in _type_info:
            raise ValueError, "invalid type '%s'" % type
        self.name = name
        self.type = type

        
    def __repr__(self):
        return "Column(%r, %r)" % (self.name, self.type)


    Python_type = property(lambda self: _type_info[self.type][0])


    size = property(lambda self: _type_info[self.type][1])



#-----------------------------------------------------------------------

class Schema(dict):
    """A table schema.

    A schema is composed of columns, each of which has a type.  The type
    is represented by a string; supported column types are '"int8"',
    '"int16"', '"int32"', '"float32"', '"float64"', '"complex64"',
    '"complex128"'.

    """

    def __init__(self, **columns):
        """Create a new schema.

        '**columns' specifies names and corresponding types of columns.  If
        none are specified, the schema is initially empty.  Additional
        columns may be added with the 'addColumn' method."""
        
        self.columns = []
        for name, type in columns.items():
            self.addColumn(name, type)


    def __repr__(self):
        return "Schema(%s)" % ", ".join(
            [ "%s=%r" % (c.name, c.type) for c in self.columns ])


    def addColumn(self, name, type, **attributes):
        """Add a column to the schema.

        'name' -- The column name; it must be unique.

        'type' -- A string specifying the column type."""

        # Do not allow a column to be added with the same name as
        # an existing column.
        if name in self:
            raise ValueError, "name '%s' is already assigned" % name

        if type in _type_info.keys():
            column = Column(name, type, **attributes)
            self.columns.append(column)
            self[name] = column
            return column
        else:
            raise ValueError, "unknown column type '%s'" % type



#-----------------------------------------------------------------------

class Chain(object):
    """A table formed by chaining several tables together."""

    def __init__(self, *tables):
        """Construct a chained table.

        '*tables' -- The tables to chain together."""
        
        self.tables = tables


    def __get_rows(self):
        for table in self.tables:
            for row in table.rows:
                yield row

    rows = property(__get_rows)


    def select(self, expression):
        for table in self.tables:
            for row in table.select(expression):
                yield row


    def __len__(self):
        return reduce(operator.add, map(len, self.tables), 0)


    def __getitem__(self, index):
        index = int(index)
        if index < 0:
            return IndexError, index
        for table in self.tables:
            if index < len(table):
                return table[index]
            else:
                index -= len(table)
        return IndexError, index



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def expand(table, expression):
    """Helper to expand 'expression' for this 'table'."""

    expand_subexpr = lambda e: expand(table, e)

    expression = expression.copy(expand_subexpr)
    expression = hep.expr.op._expandAll(expression)

    if isinstance(expression, hep.expr.Symbol):
        name = expression.symbol_name
        if name == "_index":
            expression = hep.expr.Symbol("_index", int)
        elif name in ("_row", "_table"):
            expression = hep.expr.Symbol(name, None)
        elif name in table.schema:
            value = table.schema[name]
            if isinstance(value, Column):
                expression = hep.expr.Symbol(name, _type_info[value.type][0])
            elif isinstance(value, Expression):
                expression = expand_subexpr(value.expression)
            else:
                raise NotImplementedError
        else:
            pass
            # raise KeyError, name

    # Now optimize the result.
    expression = hep.expr.op.optimize(expression)

    return expression


def cacheExpand(table, expr):
    """Fix up 'expr' to use cached values stored in 'table'.

    'table' -- A table with a 'cached_expressions' attribute.

    returns -- A copy of 'expr', with itself and its subexpressions
    wrapped in 'CachedExpression's if a cached is available in
    'table'.""" 

    subexpr_expand = lambda e: cacheExpand(table, e)

    if isinstance(expr, CachedExpression):
        return expr

    elif expr in table.expression_cache:
        # Get the cache arrays.
        mask, values = table.expression_cache[expr]
        # Copy the expression, caching subexpressions as necessary.
        expr = expr.copy(subexpr_expand)
        # Wrap the expression to use the cached value.  If no cache
        # value is present, use the underlying expression.
        return CachedExpression(mask, values, expr)

    else:
        # No cache for this expression.  However, its subexpressions may
        # be cached.
        return expr.copy(subexpr_expand)


def compile(table, expr):
    """Compile 'expr' for 'table'.

    Compiles expression 'expr', but first expands it appropriately for
    this table."""

    # Expand 'Symbol' expressions for this table.
    expr = expand(table, expr)
    # Replace expressions with accessors to cached values.
    expr = cacheExpand(table, expr)
    # Compile the expression.
    expr = hep.expr.compile(expr)
    return expr


def checkSchema(table_schema, schema):
    """Check schema consistency.

    Check that 'schema', an arbitrary 'Schema' object, is consistent
    with 'table_schema', a 'Schema' object representing columns in a
    table."""

    table_schema_columns = \
        dict([ (col.name, col) for col in table_schema.columns ])

    # Loop over columns in the schema.
    for column in schema.columns:
        name = column.name
        try:
            table_column = table_schema_columns[name]
            del table_schema_columns[name]
        except KeyError:
            raise RuntimeError, \
                  "column '%s' in schema is not in table" % name
        # Make sure the types match.
        if column.type != table_column.type:
            raise RuntimeError, \
                  "column '%s' with type %s in schema is type %s in table" \
                  % (name, column.type, table_column.type)

    # Make sure there aren't any unmatched columns left in
    # 'table_schema'.
    if table_schema_columns:
        column = table_schema_columns[table_schema_columns.keys()[0]]
        raise RuntimeError, \
              "umatched column '%s' in table" % column.name


def getTableForJoin(table, target_table):
    """Resolve the target of a table join.

    'table' -- The table from which the join is invoked.

    'target_table' -- The table being joined.  

    returns -- If 'target_table' is 'None', returns 'table'.  If
    'target_table' is a table, returns it.  If 'target_table' is a
    string, returns the table by that name in the same directory as
    'table'."""

    if target_table is None:
        return table
    elif isinstance(target_table, Table):
        return target_table
    elif isinstance(target_table, str):
        # Interpret the string as the name of a table in the same
        # directory as this one (or relative to it).
        table_dir = os.path.split(table.path)[0]
        table_path = os.path.realpath(
            os.path.join(table_dir, target_table)) + ".table"
        # Check if we already have opened this table for another join.
        if target_table in table.joined_tables:
            # Found it.
            return table.joined_tables[target_table]
        else:
            # Not there.  Open the table.
            joined_table = hep.table.open(table_path)
            # Store a referene.  That way other joins can find it, and
            # also we hold a reference, so it won't get closed.
            table.joined_tables[target_table] = joined_table
            return joined_table
    else:
        raise TypeError, "invalid join table '%s'" % repr(target_table)
        

# FIXME: This whole business is lousy.  We need a better way to manage
# all this. 

# So that we don't open tables several times, keep a cache of open
# tables. 
_open_tables = weakref.WeakValueDictionary()

def open(path, update=False, row_type=RowDict, with_metadata=True):
    # Canonicalize the path to the table.
    real_path = os.path.realpath(path)
    # Choose the mode to use when opening the table.
    # FIXME: We might always want to open for writing, so that we can
    # store metadata.
    if update:
        mode = "w"
    else:
        mode = "r"

    try:
        # If the table's already open, return it.  NOTE:  The table may
        # be open in the wrong mode!
        return _open_tables[real_path]
    except KeyError:
        # The table is not open.  Open it.
        table = table_open(real_path, mode, row_type, with_metadata)
        # Store the open table.
        _open_tables[real_path] = table
        return table


def create(path, schema, with_metadata=True):
    # Canonicalize the path to the table.
    real_path = os.path.realpath(path)
    # Make sure there isn't already an open table with this path.
    if real_path in _open_tables:
        raise RuntimeError, "table %s is already open" % path
    # Create the table.
    table = table_create(real_path, schema, with_metadata)
    # Store the open table.
    _open_tables[real_path] = table
    return table
    

def project(rows,
            projections,
            weight=None,
            handle_expr_exceptions=False):
    """Project expressions on rows in a table.

    'rows' -- An iterable object returning rows to project.

    'projections' -- A sequence of '(expression, function)' pairs.  Each
    'expression' is an expression involving columns in the row, and
    'function' is called with the value of the expression and the row
    weight computed from 'weight'.

    'weight' -- An expression for the weight of each row.  This weight
    is used when filling all expressions from a row.  If 'None', no
    weight is used when projecting rows.

    'handle_expr_exceptions' -- If true, exceptions raised during
    evaluation of expressions in 'projections' or 'weight' are handled;
    a warning is printed, and that value is skipped.

    returns -- The sum of weights of projected rows."""

    rows = iter(rows)
    try:
        # Get the first event from the iterator.
        first_row = rows.next()
    except StopIteration:
        # There are no rows to iterate over.  Simply return.
        return 0

    # If the first event has a 'table' attribute, that's the table of
    # which it's a member.  
    try:
        table = first_row.get("_table")
    except AttributeError:
        table = None

    # From 'projections', construct a list of items we have to process
    # for each event.  Each element of 'items' is a pair, containing the
    # 'evaluate' method of the compiled expression for that item, and
    # the 'accumulate' method of the corresponding histogram.
    items = []
    for projection in projections:
        # Unpack the project as an '(expression, function)' pair.
        if len(projection) == 2:
            expression, function = projection
            selection = None
        elif len(projection) == 3:
            expression, function, selection = projection
            selection = hep.expr.asExpression(selection)
        expression = hep.expr.asExpression(expression)

        if table is not None:
            # We have a table, so compile the expression for it.
            evaluate = table.compile(expression).evaluate
            if selection is None:
                select = None
            else:
                select = table.compile(selection).evaluate
        else:
            # No table; use the expression unmodified.
            evaluate = expression.evaluate
            if selection is None:
                select = None
            else:
                select = selection.evaluate
        # Store them both for quick looping.
        items.append((select, evaluate, function))

    # Use the weight expression, if given.
    if weight is not None:
        if table is not None:
            # We have a table, so compile the weight expression for it.
            evaluate_weight = table.compile(weight).evaluate
        else:
            evaluate_weight = weight.evaluate
    else:
        # No weight expression given, so use unit weight for each event.
        evaluate_weight = lambda event: 1

    # Start accumulating the sum of weights over all rows.
    total_weight = 0

    def handleException(expression, exception):
        """Maybe handle 'exception' raised while evaluating 'expression'.

        returns -- Only if the exception was handled; otherwise,
        re-raises it."""

        # Always let keyboard interrupts propagate.
        if isinstance(exception, KeyboardInterrupt):
            raise
        # Should we handle the excpetion?
        if not handle_expr_exceptions:
            # No; let the exception propagate upward.
            raise
        # Print a warning.
        print >> sys.stderr, \
              "warning: exception '%s' in expression \"%s\" in 'project'" \
              % (exception, expression)


    # Loop over the rest of the rows in in iterator.  Start with the row
    # we've already removed from the iterator.
    row = first_row
    while True:
        # Compute the weight for this row.
        try:
            weight = evaluate_weight(row)
        except Exception, exception:
            handleException(weight, exception)
            # Continue to the next row.
            continue

        # Accumulate the total weight.
        total_weight += weight

        # Loop over elements to project.
        for i in range(len(items)):
            select, evaluate, function = items[i]
            if select is not None:
                try:
                    accept = select(row)
                except Exception, exception:
                    handleException(projections[i][2], exception)
                    # Continue to the next expression.
                    continue
                if not accept:
                    continue

            try:
                value = evaluate(row)
            except Exception, exception:
                handleException(projections[i][0], exception)
                # Continue to the next expression.
                continue

            # Use this value.
            function(value, weight)
            
        # On to the next row.
        try:
            row = rows.next()
        except StopIteration:
            # No more rows.
            break

    return total_weight


def dumpSchema(schema, out=sys.stdout):
    """Print a summary of 'schema'."""

    print >> out, "name                             type        "
    print >> out, "---------------------------------------------"
    for column in schema.columns:
        attributes = [ "%s=%r" % (n, v)
                       for (n, v) in column.__dict__.items()
                       if n not in ("name", "type") ]
        print >> out, "%-32s %-12s %s" \
                  % (column.name, column.type, ", ".join(attributes))
    print >> out


def _columnFromDom(node, schema):
    name, attributes, subelements = parseTextElements(node)
    assert name == "column"
    schema.addColumn(
        name=attributes["name"], type=attributes["type"], **subelements)


def _schemaFromDom(node):
    assert node.nodeName == "schema"
    schema = hep.table.Schema()
    for child in node.childNodes:
        if child.nodeName == "column":
            _columnFromDom(child, schema)
        else:
            raise ParseError, \
                  "unexpected schema element '%s'" % child.nodeName
    return schema
    

def loadSchema(path):
    """Load a schema from the XML schema description at 'path'."""

    document = loadAsDom(path)
    removeWhitespaceText(document)
    if len(document.childNodes) != 1:
        raise ParseError, "document has wrong number of child nodes"
    schema_node, = document.childNodes
    if schema_node.nodeName != "schema":
        raise ParseError, "document element is not 'schema'"
    return _schemaFromDom(schema_node)


def _columnToDom(column, document):
    node = document.createElement("column")
    node.setAttribute("name", column.name)
    node.setAttribute("type", column.type)
    for key, value in column.__dict__.items():
        if not key.startswith("_") and key not in ["name", "type"]:
            node.appendChild(createElement(document, key, str(value)))
    return node


def saveSchema(schema, path):
    """Save a schema to an XML description at 'path'."""

    document = makeDomDocument()
    schema_node = document.createElement("schema")
    document.appendChild(schema_node)
    for column in schema.columns:
        schema_node.appendChild(_columnToDom(column, document))
    file(path, "w").write(document.toprettyxml(" "))


def CutIter(rows, cut):
    """Iterator adaptor that applies a 'cut' predicate.

    'rows' -- An iterable over rows.

    'cut' -- A function that takes a row as its only argument.

    yields -- Rows in 'rows' for which 'cut' returns a true value."""

    # FIXME: Compile 'cut' for table, if applicable.
    # (But what if rows are from different tables, e.g. chained?)
    for row in rows:
        if cut(row):
            yield row


def extract(rows, table, expressions):
    compiled_expressions = None
    
    for row in rows:
        if compiled_expressions is None:
            try:
                rows_table = rows.get("_table")
            except KeyError:
                compiled_expressions = expressions
            else:
                compiled_expressions = dict([
                    (n, rows_table.compile(e))
                    for n, e in expressions.items() ])

        table.append(dict([
            (n, e.evaluate(row))
            for (n, e) in compiled_expressions.items() ]))


