#-----------------------------------------------------------------------
#
# module hep.expr.classes
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Base expression classes for the expression library."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   __future__ import division
import hep
from   hep.bool import *
from   hep.fn import *
import inspect
import math
import operator
import types

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Expression(object):
    """Base class for expression objects.

    An instance of an 'Expression' subclass represents an mathematical
    expression.  Generally, the expression is a single arithmetic or
    other operation, whose arguments may in turn be other 'Expression'
    instances (i.e. subexpressions).

    These attributes are provided:

    'type' -- A Python type object, which represents the type of the
    result of evaluating the expression.  If the type varies or is not
    known, the type is 'None'.
    """

    subexprs = ()
    subexpr_types = ()


    def _get_type_from_subexprs(self):
        return self.subexpr_types[0]


    def _get_subexpr_types(self):
        return [ e.type for e in self.subexprs ]


    def _get_coerced_subexpr_types(self):
        coerced_type = coerceExprTypes(self.subexprs)
        return len(self.subexprs) * (coerced_type, )


    def evaluate(self, symbols):
        """Evaluate the expression.

        'symbols' -- A map containing values of symbolic names.  Keys in
        the map are names of symbols, and values are their corresponding
        values.

        returns -- The result of evaluating the expression."""
        
        raise NotImplementedError


    def __call__(self, **symbols):
        """Evaluate the expression.

        '**symbols' -- Values of symbolc names, as keyword arguments.

        returns -- The result of evaluating the expression."""

        return self.evaluate(symbols)


    def __asExpression(self, other):
        """Make sure 'other' is an expression."""

        if isinstance(other, Expression):
            return other
        else:
            return Constant(other)


    def _hash(self):
        return hash(self.__class__.__name__) ^ hashSubexprs(self)


    def __hash__(self):
        return self._hash()



#-----------------------------------------------------------------------

class Cast(Expression):

    def __init__(self, type, expression):
        self.type = type
        self.subexprs = (expression, )


    subexpr_types = property(Expression._get_subexpr_types)


    def __repr__(self):
        type_name = getattr(self.type, "__name__", str(self.type))
        return "Cast(%s, %s)" \
               % (type_name, repr(self.subexprs[0]))


    def __str__(self):
        if self.type is None:
            return str(self.subexprs[0])
        else:
            return "%s(%s)" % (self.type.__name__, str(self.subexprs[0]))


    def evaluate(self, symbols):
        value = self.subexprs[0].evaluate(symbols)
        if self.type is None:
            return value
        else:
            return self.type(value)


    def __eq__(self, other):
        return isinstance(other, Cast) \
               and other.type == self.type \
               and compareSubexprs(other, self)


    def _hash(self):
        return hash("Cast") ^ hash(self.type) ^ hash(self.subexprs[0])


    def copy(self, copy_fn=lambda e: e.copy()):
        return Cast(self.type, copy_fn(self.subexprs[0]))
    


#-----------------------------------------------------------------------

class Constant(Expression):

    def __init__(self, value):
        self.value = value


    def __get_type(self):
        value_type = type(self.value)
        if value_type in (int, float, bool):
            return value_type
        else:
            return None

    type = property(__get_type)
    subexpr_types = ()


    def __repr__(self):
        return "Constant(%s)" % repr(self.value)


    def __str__(self):
        if type(self.value) == str:
            return repr(self.value)
        else:
            return str(self.value)


    def evaluate(self, symbols):
        return self.value


    def __eq__(self, other):
        return isinstance(other, Constant) \
               and self.value == other.value


    def _hash(self):
        try:
            # Attempt to hash the constant.
            constant_hash = hash(self.value)
        except TypeError:
            # Some are unhashable.  Use its ID instead.
            constant_hash = id(self.value)
        return constant_hash ^ hash("Constant")


    def copy(self, copy_fn=None):
        return Constant(self.value)



#-----------------------------------------------------------------------

class Symbol(Expression):
    """A free variable in an expression.

    A symbol is a placeholder for a value that is provided at evaluation
    time, i.e. a free variable.  Like a Python variable, the symbol's
    type may be unspecified; or, a Python type may be specified to fix
    the symbol's type."""
    

    no_symbol = hep.Token()


    def __init__(self, symbol_name, type=None):
        """Create a free variable expression.

        When the expression is evaluated, the symbol table is checked
        for a symbol named 'symbol_name'.  The symbol expression
        evaluates to the value of that symbol in the symbol table.

        'symbol_name' -- The name to look up in the symbol table.

        'type' -- The type of the symbol, or 'None' if unspecified."""
        
        self.symbol_name = intern(str(symbol_name))
        self.type = type


    subexpr_types = ()


    def __repr__(self):
        type_name = getattr(self.type, "__name__", str(self.type))
        return "Symbol('%s', %s)" % (self.symbol_name, type_name)


    def __str__(self):
        return self.symbol_name


    def evaluate(self, symbols):
        value = symbols.get(self.symbol_name, self.no_symbol)
        if value is self.no_symbol:
            raise KeyError, "no symbol '%s'" % self.symbol_name
        # If a type is specified, make sure the value in the symbol table
        # is of that type.
        if self.type is not None \
           and self.type != type(value):
            try:
                value = self.type(value)
            except TypeError:
                raise TypeError, "symbol value '%s' is not type '%s'" \
                      % (repr(value), self.type.__name__)
        return value


    def __eq__(self, other):
        return isinstance(other, Symbol) \
               and self.symbol_name == other.symbol_name


    def _hash(self):
        return hash(self.symbol_name) ^ hash("Symbol")


    def copy(self, copy_fn=None):
        copy = Symbol(self.symbol_name, self.type)
        copy.__dict__.update(self.__dict__)
        return copy



#-----------------------------------------------------------------------

class GetAttribute(Expression):

    def __init__(self, object, attribute_name):
        self.subexprs = (object, attribute_name)


    type = None
    subexpr_types = (None, None)


    def __repr__(self):
        return "GetAttribute(%s, %s)" % tuple(map(repr, self.subexprs))


    def __str__(self):
        if isinstance(self.subexprs[1], Constant):
            return "%s.%s" % (_parenthesize(self.subexprs[0]),
                              self.subexprs[1].value)
        else:
            return "getattr(%s, %s)" % tuple(map(str, self.subexprs))


    def evaluate(self, symbols):
        object = self.subexprs[0].evaluate(symbols)
        attribute_name = self.subexprs[1].evaluate(symbols)
        return getattr(object, attribute_name)


    def __eq__(self, other):
        return isinstance(other, GetAttribute) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return GetAttribute(copy_fn(self.subexprs[0]),
                            copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class Call(Expression):

    def __init__(self, function, arg_list=(), kw_args={}, type=None):
        self.function = function
        self.subexprs = tuple(arg_list)
        self.kw_args = dict(kw_args)


    def __get_type(self):
        if isinstance(self.function, Constant):
            function = self.function.value
            subexpr_type = coerceExprTypes(self.subexprs)
            if function in (int, float, bool):
                # The function is actually a type constructor, so the
                # type is known.
                return function
            elif function in (min, max):
                # The function is a built-in that returns the same type
                # as its subexpressions.
                return subexpr_type
            elif function is abs:
                if subexpr_type is complex:
                    return float
                else:
                    return subexpr_type
            elif function in math.__dict__.values():
                # The function is a math function, and returns 'float'.
                return float
            elif hasattr(function, "type"):
                return function.type

        return None


    type = property(__get_type)


    subexpr_types = property(Expression._get_subexpr_types)


    def __repr__(self):
        return "Call(%s, %s, %s)" \
               % (repr(self.function),
                  repr(self.subexprs),
                  repr(self.kw_args))


    def __str__(self):
        args = self.subexprs
        for name, value in self.kw_args.iteritems():
            args = args + ("%s=%s" % (name, str(value)), )
        if isinstance(self.function, Constant) \
           and hasattr(self.function.value, "__name__"):
            function_name = self.function.value.__name__
        else:
            function_name = str(self.function)
        return "%s(%s)" % (function_name, ", ".join(map(str, args)))


    def evaluate(self, symbols):
        function = self.function.evaluate(symbols)
        arg_list = map(lambda arg: arg.evaluate(symbols),
                       self.subexprs)
        kw_args = {}
        for name, expression in self.kw_args.iteritems():
            kw_args[name] = expression.evaluate(symbols)
            
        return apply(function, arg_list, kw_args)


    def __eq__(self, other):
        return isinstance(other, Call) \
               and self.function == other.function \
               and compareSubexprs(self, other) \
               and self.kw_args == other.kw_args


    def _hash(self):
        return hash("Call") ^ hash(self.function) ^ hashSubexprs(self) \
               ^ reduce(operator.xor, map(hash, self.kw_args.items()), 0) 


    def copy(self, copy_fn=lambda t: t.copy()):
        kw_args = {}
        for name, expression in self.kw_args.iteritems():
            kw_args[name] = copy_fn(expression)
        return Call(copy_fn(self.function),
                    map(copy_fn, self.subexprs),
                    kw_args)



#-----------------------------------------------------------------------

class Function(Expression):
    """An expression which is evaluated with a callable.

    During evaluation, the callable is passed values from the symbol
    table as its arguments.   The names of its arguments are matched to
    the names in the symbol table, and the corresponding values are
    provided.""" 


    def __init__(self, function):
        if not callable(function):
            raise ValueError, "argument must be callable"
        self.subexprs = ()
        self.function = function
        self.arg_names = tuple(inspect.getargspec(function)[0])
        self.arg_names = function.func_code.co_varnames


    type = None
    subexpr_types = ()


    def __repr__(self):
        return "Function(%s)" % repr(self.function)


    def __str__(self):
        return "%s(...)" % self.function.__name__


    def evaluate(self, symbols):
        # Match the function's argument names to values from the symbol
        # table. 
        arguments = {}
        for name in self.arg_names:
            arguments[name] = symbols[name]
        # Invoke the function.
        return self.function(**arguments)


    def __eq__(self, other):
        # FIXME: Is the comparison of functions reliable for lambdas?
        # Probably not.
        return isinstance(other.Function) \
               and self.function == other.function


    def _hash(self):
        return hash("Function") ^ hash(self.function) 


    def copy(self, copy_fn=lambda t: t.copy()):
        return Function(self.function)



#-----------------------------------------------------------------------

class Subscript(Expression):

    def __init__(self, collection, subscript):
        self.subexprs = (collection, subscript)


    type = None
    subexpr_types = (None, None)
    

    def __repr__(self):
        return "Subscript(%s, %s)" % tuple(map(repr, self.subexprs))


    def __str__(self):
        return "%s[%s]" % tuple(map(str, self.subexprs))


    def evaluate(self, symbols):
        collection = self.subexprs[0].evaluate(symbols)
        subscript = self.subexprs[1].evaluate(symbols)
        return collection[subscript]


    def __eq__(self, other):
        return isinstance(other, Subscript) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Subscript(copy_fn(self.subexprs[0]), copy_fn(self.subexprs[1]))




#-----------------------------------------------------------------------

class In(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = bool
    subexpr_types = (None, None)
    

    def __repr__(self):
        return "In(%s, %s)" % (repr(self.subexprs[0]),
                               repr(self.subexprs[1]))


    def __str__(self):
        return "%s in %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               in self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, In) and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return In(copy_fn(self.subexprs[0]), copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class And(Expression):

    def __init__(self, *subexprs):
        self.subexprs = list(subexprs)


    type = bool
    subexpr_types = property(lambda self: len(self.subexprs) * (bool, ))


    def __repr__(self):
        return "And(%s)" % (", ".join(map(repr, self.subexprs)))


    def __str__(self):
        return " and ".join(map(_parenthesize, self.subexprs))


    def evaluate(self, symbols):
        for expr in self.subexprs:
            if not expr.evaluate(symbols):
                return False
        return True


    def __eq__(self, other):
        return isinstance(other, And) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return apply(And, map(copy_fn, self.subexprs))



#-----------------------------------------------------------------------

class Or(Expression):

    def __init__(self, *subexprs):
        self.subexprs = tuple(subexprs)


    type = bool
    subexpr_types = property(lambda self: len(self.subexprs) * (bool, ))


    def __repr__(self):
        return "Or(%s)" % (", ".join(map(repr, self.subexprs)))


    def __str__(self):
        return " or ".join(map(_parenthesize, self.subexprs))


    def evaluate(self, symbols):
        for expr in self.subexprs:
            if expr.evaluate(symbols):
                return True
        return False


    def __eq__(self, other):
        return isinstance(other, Or) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return apply(Or, map(copy_fn, self.subexprs))



#-----------------------------------------------------------------------

class Not(Expression):

    def __init__(self, expr):
        self.subexprs = (expr, )


    type = bool
    subexpr_types = property(lambda self: len(self.subexprs) * (bool, ))


    def __repr__(self):
        return "Not(%s)" % repr(self.subexprs[0])


    def __str__(self):
        return "not %s" % str(self.subexprs[0])


    def evaluate(self, symbols):
        return not self.subexprs[0].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, Not) and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Not(copy_fn(self.subexprs[0]))
    


#-----------------------------------------------------------------------

class Equal(Expression):

    def __init__(self, expr1, expr2):
        if hash(expr1) <= hash(expr2):
            self.subexprs = (expr1, expr2)
        else:
            self.subexprs = (expr2, expr1)


    type = bool
    subexpr_types = property(Expression._get_coerced_subexpr_types)
    

    def __repr__(self):
        return "Equal(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s == %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               == self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, Equal) and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Equal(copy_fn(self.subexprs[0]), copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class LessThan(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = bool
    subexpr_types = property(Expression._get_coerced_subexpr_types)
    

    def __repr__(self):
        return "LessThan(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s < %s" % (_parenthesize(self.subexprs[0]),
                            _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               < self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, LessThan) \
               and self.subexprs[0] == other.subexprs[0] \
               and self.subexprs[1] == other.subexprs[1]


    def copy(self, copy_fn=lambda t: t.copy()):
        return LessThan(copy_fn(self.subexprs[0]),
                        copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class LessThanOrEqual(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = bool
    subexpr_types = property(Expression._get_coerced_subexpr_types)
    

    def __repr__(self):
        return "LessThanOrEqual(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s <= %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               <= self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, LessThanOrEqual) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return LessThanOrEqual(copy_fn(self.subexprs[0]),
                               copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class Minus(Expression):

    def __init__(self, expr):
        self.subexprs = (expr, )


    type = property(Expression._get_type_from_subexprs)
    subexpr_types = property(Expression._get_coerced_subexpr_types)


    def __repr__(self):
        return "Minus(%s)" % repr(self.subexprs[0])


    def __str__(self):
        return "-(%s)" % str(self.subexprs[0])


    def evaluate(self, symbols):
        return -self.subexprs[0].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, Minus) and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Minus(copy_fn(self.subexprs[0]))



#-----------------------------------------------------------------------

class Add(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = property(Expression._get_type_from_subexprs)
    subexpr_types = property(Expression._get_coerced_subexpr_types)


    def __repr__(self):
        return "Add(%s)" % (", ".join(map(repr, self.subexprs)))


    def __str__(self):
        return " + ".join(map(_parenthesize, self.subexprs))


    def evaluate(self, symbols):
        result = self.subexprs[0].evaluate(symbols)
        for subexpr in self.subexprs[1:]:
            result += subexpr.evaluate(symbols)
        return result


    def __eq__(self, other):
        return isinstance(other, Add) and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return apply(Add, map(copy_fn, self.subexprs))



#-----------------------------------------------------------------------

class Subtract(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = property(Expression._get_type_from_subexprs)
    subexpr_types = property(Expression._get_coerced_subexpr_types)


    def __repr__(self):
        return "Subtract(%s, %s)" % \
               (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s - %s" % (_parenthesize(self.subexprs[0]),
                            _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               - self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, Subtract) and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Subtract(copy_fn(self.subexprs[0]),
                        copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class Multiply(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = property(Expression._get_type_from_subexprs)
    subexpr_types = property(Expression._get_coerced_subexpr_types)


    def __repr__(self):
        return "Multiply(%s)" % (", ".join(map(repr, self.subexprs)))


    def __str__(self):
        return " * ".join(map(_parenthesize, self.subexprs))


    def evaluate(self, symbols):
        return reduce(
            operator.mul,
            map(lambda expr: expr.evaluate(symbols), self.subexprs),
            1)


    def __eq__(self, other):
        return isinstance(other, Multiply) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return apply(Multiply, map(copy_fn, self.subexprs))



#-----------------------------------------------------------------------

class Divide(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    def __get_type(self):
        # Obtain the type of the subexpressions.
        subexpr_type = coerceExprTypes(self.subexprs)
        if subexpr_type is int:
            # Since we're using 'future' division, the quotient of two
            # ints is a float.
            return float
        else:
            return subexpr_type


    type = property(__get_type)
    subexpr_types = property(lambda self: (self.type, self.type))


    def __repr__(self):
        return "Divide(%s, %s)" % \
               (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s / %s" % (_parenthesize(self.subexprs[0]),
                            _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               / self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, Divide) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Divide(copy_fn(self.subexprs[0]), copy_fn(self.subexprs[1]))




#-----------------------------------------------------------------------

class FloorDivide(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = property(Expression._get_type_from_subexprs)
    subexpr_types = property(Expression._get_coerced_subexpr_types)


    def __repr__(self):
        return "FloorDivide(%s, %s)" % \
               (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s // %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               // self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, FloorDivide) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return FloorDivide(copy_fn(self.subexprs[0]),
                           copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class Remainder(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = property(Expression._get_type_from_subexprs)
    subexpr_types = property(Expression._get_coerced_subexpr_types)


    def __repr__(self):
        return "Remainder(%s, %s)" % \
               (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s %% %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               % self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, Remainder) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Remainder(copy_fn(self.subexprs[0]),
                         copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class Power(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    def __get_type(self):
        mantissa, exponent = self.subexprs
        if mantissa.type is None or exponent.type is None:
            return None
        else:
            return float
        

    type = property(__get_type)


    def __get_subexpr_types(self):
        type = self.type
        return (type, type)


    subexpr_types = property(__get_subexpr_types)


    def __repr__(self):
        return "Power(%s, %s)" % \
               (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s ** %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return float(self.subexprs[0].evaluate(symbols)
                     ** self.subexprs[1].evaluate(symbols))


    def __eq__(self, other):
        return isinstance(other, Power) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Power(copy_fn(self.subexprs[0]),
                     copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class LeftShift(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = int
    subexpr_types = (int, int)


    def __repr__(self):
        return "LeftShift(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s << %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               << self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other.LeftShift) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return LeftShift(copy_fn(self.subexprs[0]),
                         copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class RightShift(Expression):

    def __init__(self, expr1, expr2):
        self.subexprs = (expr1, expr2)


    type = int
    subexpr_types = (int, int)


    def __repr__(self):
        return "RightShift(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s << %s" % (_parenthesize(self.subexprs[0]),
                             _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               >> self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other.RightShift) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return RightShift(copy_fn(self.subexprs[0]),
                          copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class BitwiseNot(Expression):

    def __init__(self, expr1):
        self.subexprs = (expr1, )
                                    

    type = int
    subexpr_types = (int, )
    

    def __repr__(self):
        return "BitwiseNot(%s)" % repr(self.subexprs[0])


    def __str__(self):
        return "~%s" % _parenthesize(self.subexprs[0])


    def evaluate(self, symbols):
        return ~self.subexprs[0].evaluate(symbols) 


    def __eq__(self, other):
        return isinstance(other.BitwiseNot) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return BitwiseNot(copy_fn(self.subexprs[0]))



#-----------------------------------------------------------------------

class BitwiseAnd(Expression):

    def __init__(self, expr1, expr2):
        if hash(expr1) < hash(expr2):
            self.subexprs = (expr1, expr2)
        else:
            self.subexprs = (expr2, expr1)
                                    

    type = int
    subexpr_types = (int, int)


    def __repr__(self):
        return "BitwiseAnd(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s & %s" % (_parenthesize(self.subexprs[0]),
                            _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               & self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other, BitwiseAnd) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return BitwiseAnd(copy_fn(self.subexprs[0]),
                          copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class BitwiseOr(Expression):

    def __init__(self, expr1, expr2):
        if hash(expr1) < hash(expr2):
            self.subexprs = (expr1, expr2)
        else:
            self.subexprs = (expr2, expr1)


    type = int
    subexpr_types = (int, int)


    def __repr__(self):
        return "BitwiseOr(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s | %s" % (_parenthesize(self.subexprs[0]),
                            _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               | self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other.BitwiseOr) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return BitwiseOr(copy_fn(self.subexprs[0]),
                         copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class BitwiseXor(Expression):

    def __init__(self, expr1, expr2):
        if hash(expr1) < hash(expr2):
            self.subexprs = (expr1, expr2)
        else:
            self.subexprs = (expr2, expr1)


    type = int
    subexpr_types = (int, int)


    def __repr__(self):
        return "BitwiseXor(%s, %s)" \
               % (repr(self.subexprs[0]), repr(self.subexprs[1]))


    def __str__(self):
        return "%s ^ %s" % (_parenthesize(self.subexprs[0]),
                            _parenthesize(self.subexprs[1]))


    def evaluate(self, symbols):
        return self.subexprs[0].evaluate(symbols) \
               ^ self.subexprs[1].evaluate(symbols)


    def __eq__(self, other):
        return isinstance(other.BitwiseXor) \
               and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return BitwiseXor(copy_fn(self.subexprs[0]),
                          copy_fn(self.subexprs[1]))



#-----------------------------------------------------------------------

class ObjectExpr(Expression):
    """An instance-valued expression with computed attributes.

    An 'ObjectExpr' is an expression whose value is an instance-like
    object.  The expression class defines attributes just as an ordinary
    class would, except that the attributes are themselves expressions.
    When an attribute is accessed in an instance of the expression
    class, the corresponding expression is evaluated."""

    def __init__(self, class_, *arguments):
        """Construct a new expression class.

        'class_' -- The class which will be instantiated by this
        expression.  

        '*arguments' -- Expression arguments to the constructor of
        'class_'."""

        self.class_ = class_
        self.subexprs = list(arguments)


    type = None
    subexpr_types = property(Expression._get_subexpr_types)


    def __repr__(self):
        return "ObjectExpr(%s, %s)" % \
               (self.class_.__module__ + "." + self.class_.__name__,
                ", ".join(map(repr, self.subexprs)))


    def __str__(self):
        return "%s(%s)" % (self.class_.__name__,
                           ", ".join(map(str, self.subexprs)))


    def evaluate(self, symbols):
        arguments = map(lambda expr: expr.evaluate(symbols),
                        self.subexprs)
        return self.class_(*arguments)


    def __eq__(self, other):
        return isinstance(other, ObjectExpr) \
               and self.class_ == other.class_ \
               and compareSubexprs(self, other)


    def _hash(self):
        return hash("ObjectExpr") ^ hash(self.class_) ^ hashSubexprs(self)


    def copy(self, copy_fn=lambda c: c.copy()):
        return ObjectExpr(self.class_, *map(copy_fn, self.subexprs))



#-----------------------------------------------------------------------

class Tuple(Expression):

    def __init__(self, *exprs):
        self.subexprs = tuple(exprs)


    type = None
    subexpr_types = property(Expression._get_subexpr_types)


    def __repr__(self):
        return "Tuple(%s)" % (", ".join(map(repr, self.subexprs)))


    def __str__(self):
        return ", ".join(map(_parenthesize, self.subexprs))


    def evaluate(self, symbols):
        return tuple([ s.evaluate(symbols) for s in self.subexprs ])


    def __eq__(self, other):
        return isinstance(other, Tuple) and compareSubexprs(self, other)


    def copy(self, copy_fn=lambda t: t.copy()):
        return Tuple(*map(copy_fn, self.subexprs))



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def _parenthesize(expr):
    if expr.__class__ \
           in (Call, Constant, GetAttribute, Symbol, Subscript):
        return str(expr)
    else:
        return "(%s)" % str(expr)


def coerceExprTypes(expr_list):
    """Return the type obtained by coercing the types of expressions.

    'expr_list' -- A sequence of expressions.

    returns -- The type obtained by coercing all the types of
    expressions in 'expr_list' together.

    raises -- 'TypeError' if the coercion fails."""

    try:
        # If any are untyped, the combined type is likewise.
        if firstIndex(expr_list, lambda e: e.type is None) != -1:
            return None
        # Generate a list containing for each expression a value whose
        # type is the same as the expression's type.
        type_list = [ expr.type(0) for expr in expr_list ]
        # Coerce these values together.
        coerced_value = reduce(lambda e1, e2: coerce(e1, e2)[0], type_list)
        # Return the type of the coerced value.
        return type(coerced_value)
    except TypeError:
        raise TypeError, "number coercion failed"
    

def _sort_subexprs(subexprs):
    subexprs = list(subexprs)
    subexprs.sort(lambda e1, e2: cmp(hash(e1), hash(e2)))
    return tuple(subexprs)


def compareSubexprs(expr1, expr2):
    subexprs1 = expr1.subexprs
    subexprs2 = expr2.subexprs
    if len(subexprs1) != len(subexprs2):
        return False
    subexprs1 = _sort_subexprs(subexprs1)
    subexprs2 = _sort_subexprs(subexprs2)
    return subexprs1 == subexprs2


def hashSubexprs(expr):
    result = 0
    for subexpr in expr.subexprs:
        result ^= hash(subexpr)
    return result

