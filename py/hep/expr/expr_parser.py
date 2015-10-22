#-----------------------------------------------------------------------
#
# module hep.expr.expr_parser
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Expression parser."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   classes import *
from   hep import ext
import parser
import symbol
import symbols
import token

#-----------------------------------------------------------------------
# exceptions
#-----------------------------------------------------------------------

class ParseError(Exception):
    pass



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def _matchSequence(pattern, sequence):
    if pattern is None:
        return 1
    elif type(pattern) not in (list, tuple):
        return pattern == sequence
    elif len(pattern) == len(sequence):
        for i in xrange(0, len(pattern)):
            if not _matchSequence(pattern[i], sequence[i]):
                return 0
        return 1
    else:
        return 0


def _parse_and(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    else:
        if terms[1] == (token.NAME, "and"):
            # Evaluate chained operations.
            return And(fromAst(terms[0]), _parse_and(val, terms[2:]))
        elif terms[1][0] == token.AMPER:
            operation = BitwiseAnd
            if len(terms) != 3:
                raise ParseError, "too many terms for bitwise and"
            return BitwiseAnd(fromAst(terms[0]), fromAst(terms[2]))
        else:
            raise NotImplementedError


def _parse_arglist(terms):
    args = []
    kw_args = {}
    for index in range(0, len(terms)):
        argument = terms[index]
        if (index % 2) == 1:
            if argument[0] != token.COMMA:
                raise ParseError, "expected comma in argument list"
            else:
                pass
        else:
            # Make sure it's an argument.
            if argument[0] != symbol.argument:
                raise ParseError, "expected argument in argument list"
            if len(argument) == 2:
                # It's a positional argument.
                args.append(fromAst(argument[1]))
            elif len(argument) == 4 and argument[2][0] == token.EQUAL:
                # It's a keyword argument.
                key = fromAst(argument[1])
                value = fromAst(argument[3])
                kw_args[key] = value
    return args, kw_args
            

def _parse_arith_expr(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif (len(terms) % 2) == 1:
        # Evaluate chained operations left-to-right.
        expr1 = _parse_arith_expr(val, terms[:-2])
        operator = fromAst(terms[-2])
        operator_token = operator[0]
        expr2 = fromAst(terms[-1])
        if operator_token == token.PLUS:
            return Add(expr1, expr2)
        elif operator_token == token.MINUS:
            return Subtract(expr1, expr2)
        else:
            raise ParseError, "unexpected operator in arith_expr"
    else:
        raise NotImplementedError


def _parse_atom(val, terms):
    if len(terms) == 1:
        type, value = terms[0]
        if type == token.NUMBER:
            return Constant(eval(value))
        elif type == token.NAME:
            return Symbol(value)
        elif type == token.STRING:
            return Constant(eval(value))
        else:
            raise ParseError, "unexpected token in atom"
    elif len(terms) == 3:
        if terms[0] == (token.LPAR, "("):
            if terms[2] != (token.RPAR, ")"):
                raise ParseError, "missing ) in atom"
            return fromAst(terms[1])
        else:
            raise ParseError, "unexpected atom"
    else:
        raise ParseError, "unexpected atom"


def _make_comparison(expr1, operator, expr2):
    if operator == "==":
        return Equal(expr1, expr2)
    elif operator == "!=":
        return Not(Equal(expr1, expr2))
    elif operator == "<":
        return LessThan(expr1, expr2)
    elif operator == "<=":
        return LessThanOrEqual(expr1, expr2)
    elif operator == ">":
        return LessThan(expr2, expr1)
    elif operator == ">=":
        return LessThanOrEqual(expr2, expr1)
    elif operator == "in":
        return In(expr1, expr2)
    elif operator == "not in":
        return Not(In(expr1, expr2))
    else:
        raise ParseError, \
              "unexpected comparison operator %s" \
              % str(operator)


def _parse_comparison(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif len(terms) in (3, 5):
        expr1 = fromAst(terms[0])
        operator1 = _parse_operator(terms[1])
        expr2 = fromAst(terms[2])
        result = _make_comparison(expr1, operator1, expr2)
        if len(terms) == 5:
            operator2 = _parse_operator(terms[3])
            expr3 = fromAst(terms[4])
            result = And(
                result, _make_comparison(expr2, operator2, expr3))
        return result
    else:
        raise ParseError, "unexpected comparison"


def _parse_expr(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif len(terms) == 3:
        if terms[1] == (token.VBAR, "|"):
            return BitwiseOr(fromAst(terms[0]), fromAst(terms[2]))
        else:
            raise ParseError, \
                  "unexpected operator %s in expr" % str(terms[1])
    else:
        raise ParseError, "unexpected expr"


_operator_patterns = {
    (symbol.comp_op, (token.EQEQUAL, None)): "==",
    (symbol.comp_op, (token.NOTEQUAL, None)): "!=",
    (symbol.comp_op, (token.LESS, None)): "<",
    (symbol.comp_op, (token.LESSEQUAL, None)): "<=",
    (symbol.comp_op, (token.GREATER, None)): ">",
    (symbol.comp_op, (token.GREATEREQUAL, None)): ">=",
    (symbol.comp_op, (token.NAME, "in")): "in",
    (symbol.comp_op, (token.NAME, "not"), (token.NAME, "in")): "not in",
    }


def _parse_operator(term):
    for pattern, operator in _operator_patterns.iteritems():
        if _matchSequence(pattern, term):
            return operator
    raise ParseError, "unexpected operator '%s'" % repr(term)
    

def _parse_eval_input(val, terms):
    return fromAst(terms[0])


def _parse_factor(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif len(terms) == 2 and terms[0] == (token.MINUS, "-"):
        operand = fromAst(terms[1])
        return Minus(operand)
    elif len(terms) == 2 and terms[0] == (token.TILDE, "~"):
        operand = fromAst(terms[1])
        return BitwiseNot(operand)
    else:
        raise ParseError, "unexpected terms in factor"


def _parse_ignore1(val, terms):
    if len(terms) != 1:
        raise ParseError, \
              "expected one subexpression (%s)" % symbol.sym_name[val]
    return fromAst(terms[0])


def _parse_not_test(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif len(terms) == 2:
        if terms[0] != (token.NAME, "not"):
            raise ParseError, "unexpected operation in not_test"
        return Not(fromAst(terms[1]))
    else:
        raise ParseError, "unexpted subexpressions in not_test"


def _parse_power(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    # Does the power expression end with an exponentiation sequence?
    elif terms[-2][0] == token.DOUBLESTAR:
        # Yes.  The mantissa might have other power stuff in it too,
        # though. 
        mantissa = _parse_power(val, terms[:-2])
        # Parse the exponent term.
        exponent = fromAst(terms[-1])
        return Power(mantissa, exponent)
    else:
        result = fromAst(terms[0])
        for trailer in terms[1:]:
            if _matchSequence(
                (symbol.trailer,
                 (token.LPAR, None),
                 None,
                 (token.RPAR, None)),
                trailer):
                # Function call.
                args, kw_args = _parse_arglist(trailer[2][1:])
                result = Call(result, args, kw_args)
            elif _matchSequence(
                (symbol.trailer,
                 (token.LSQB, None),
                 (symbol.subscriptlist, (symbol.subscript, None)),
                 (token.RSQB, None)),
                trailer):
                # Subscript.
                subscript = fromAst(trailer[2][1][1])
                result = Subscript(result, subscript)
            elif _matchSequence(
                (symbol.trailer,
                 (token.DOT, None),
                 (token.NAME, None)),
                trailer):
                # Attribute access.
                attribute_name = Constant(trailer[2][1])
                result = GetAttribute(result, attribute_name)
            else:
                raise ParseError, \
                      "unexpected subexpression in trailer in power"
        return result


def _parse_shift_expr(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif len(terms) == 3:
        expr1, operation, expr2 = map(fromAst, terms)
        if operation[0] == token.LEFTSHIFT:
            return LeftShift(expr1, expr2)
        elif operation[0] == token.RIGHTSHIFT:
            return RightShift(expr1, expr2)
        else:
            raise ParseError, "unexpected operation in shift_expr"
    else:
        raise NotImplementedError


def _parse_term(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif (len(terms) % 2) == 1:
        expr1 = fromAst(terms[0])
        operator = fromAst(terms[1])
        operator_token = operator[0]
        expr2 = _parse_term(val, terms[2:])
        if operator_token == token.STAR:
            return Multiply(expr1, expr2)
        elif operator_token == token.SLASH:
            return Divide(expr1, expr2)
        elif operator_token == token.DOUBLESLASH:
            return FloorDivide(expr1, expr2)
        elif operator_token == token.PERCENT:
            return Remainder(expr1, expr2)
        else:
            raise ParseError, "unexpected operator in term"
    else:
        raise NotImplementedError


def _parse_test(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    else:
        if terms[1] == (token.NAME, "or"):
            return Or(fromAst(terms[0]), _parse_test(val, terms[2:]))
        else:
            raise NotImplementedError


def _parse_testlist(val, terms):
    subexprs = []
    if len(terms) == 1:
        return fromAst(terms[0])
    for i, term in enumerate(terms):
        expr = fromAst(term)
        if (i % 2) == 0:
            subexprs.append(expr)
        else:
            if term[0] != token.COMMA:
                raise ParseError, "unexpected operator in termlist"
    return Tuple(*subexprs)


def _parse_token(val, terms):
    return val


def _parse_xor_expr(val, terms):
    if len(terms) == 1:
        return fromAst(terms[0])
    elif len(terms) == 3:
        if terms[1][0] == token.CIRCUMFLEX:
            return BitwiseXor(fromAst(terms[0]), fromAst(terms[2]))
        else:
            raise ParseError, \
                  "unexpected operation %s in xor_expr" % terms[1]
    else:
        raise NotImplementedError


_parse_dispatch = {
    symbol.and_expr: _parse_and,
    symbol.and_test: _parse_and,
    symbol.arith_expr: _parse_arith_expr,
    symbol.atom: _parse_atom,
    symbol.eval_input: _parse_eval_input,
    symbol.comparison: _parse_comparison,
    # symbol.comp_op: _parse_comp_op,
    symbol.expr: _parse_expr,
    symbol.factor: _parse_factor,
    symbol.not_test: _parse_not_test,
    symbol.power: _parse_power,
    symbol.shift_expr: _parse_shift_expr,
    symbol.term: _parse_term,
    symbol.test: _parse_test,
    symbol.testlist: _parse_testlist,
    symbol.xor_expr: _parse_xor_expr,

    # token.EQEQUAL: _parse_token,

    }


def _addNamesToAstList(list):
    if token.ISTERMINAL(list[0]):
        assert len(list) == 2
        return (token.tok_name[list[0]], list[1])
    else:
        return (symbol.sym_name[list[0]], ) \
               + tuple(map(_addNamesToAstList, list[1:]))


def fromAst(ast):
    val = ast[0]
    try:
        parse_fn = _parse_dispatch[val]
    except KeyError:
        if token.ISTERMINAL(val):
            return ast
        else:
            raise ParseError, "unknown symbol %s" % symbol.sym_name[val]
    else:
        return parse_fn(val, ast[1:])


def parse(expression_string):
    # To be forgiving, clean up the string a bit.
    expression_string = expression_string.replace("\n", " ").strip()
    # Now parse it.
    try:
        ast = parser.ast2tuple(parser.expr(expression_string))
    except parser.ParserError, exception:
        raise ParseError, str(exception)
    expression = fromAst(ast)

    # Perform standard substitutions.
    expression = symbols.substituteConstants(expression)

    return expression


if __name__ == "__main__":
    import sys
    expression = sys.argv[1]
    ast = parser.ast2tuple(parser.expr(expression))

    import pprint
    pprint.pprint(_addNamesToAstList(ast))
    result = fromAst(ast)

    print
    print repr(result)
    print str(result)
