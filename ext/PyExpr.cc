//----------------------------------------------------------------------
//
// PyExpr.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <iostream>
#include <vector>

#include "nametable.hh"
#include "PyExpr.hh"
#include "PyRow.hh"
#include "PyTable.hh"
#include "python.hh"

using namespace Py;

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

namespace {

const char* const
operation_names[] = {
#define OPERATION(X) #X,
#include "operations"
#undef OPERATION
};


}  // anonymous namespace

//----------------------------------------------------------------------
// variables
//----------------------------------------------------------------------

Nametable 
symbol_name_table;

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

namespace {

/* The expression evaluation stack.  */
class Stack
{
public:

  Value pop();

  Value peek();

  void push(const Value& value) { stack_.push_back(value); }
  void push(long value)         { push(Value::make(value)); }
  void push(double value)       { push(Value::make(value)); }
  void push(bool value)         { push(Value::make(value)); }
  void push(Object* value)      { push(Value::make(value)); }

  bool isEmpty() const { return stack_.empty(); }

private:

  std::vector<Value> stack_;
  friend std::ostream& operator << (std::ostream& os, const Stack& st);

};


inline Value
Stack::pop()
{
  Value v = stack_.back();
  stack_.pop_back();
  return v;
}


inline Value
Stack::peek()
{
  return stack_.back();
}


inline std::ostream&
operator << (std::ostream& os, 
	     const Stack& st)
{
  for (std::vector<Value>::const_iterator iter = st.stack_.begin();
       iter != st.stack_.end();
       ++iter) {
    if (iter != st.stack_.begin())
      os << ' ';
    os << *iter;
  }

  return os;
}


//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

template<typename TYPE>
inline TYPE
max(TYPE v0, 
    TYPE v1)
{
  return (v0 > v1) ? v0 : v1;
}


template<typename TYPE>
inline TYPE
min(TYPE v0,
    TYPE v1)
{
  return (v0 > v1) ? v1 : v0;
}


inline long
abs(long v)
{
  return (v < 0) ? -v : v;
}


inline int
bit_get(char* array,
	int index)
{
  return (array[index / 8] & (1 << (index % 8))) ? 1 : 0;
}


inline void
bit_set(char* array,
	int index,
	int bit)
{
  assert(bit == 0 || bit == 1);
  if (bit == 0)
    array[index / 8] &= ~ (1 << (index % 8));
  else
    array[index / 8] |= (1 << (index % 8));
}


template<typename TYPE>
inline bool
in_range(TYPE value,
	 TYPE min,
	 TYPE max)
{
  return value >= min && value < max;
}


template<typename TYPE>
inline bool
near(TYPE value,
     TYPE central_value,
     TYPE half_interval)
{
  return abs(value - central_value) < half_interval;
}


//----------------------------------------------------------------------

void
valueFromObject(Object* object,
		Value& value)
{
  // FIXME: What should we do with bools?
  if (Int::Check(object))
    value = Value::make((long) cast<Int>(object)->AsLong());
  else if (Float::Check(object))
    value = Value::make((double) cast<Float>(object)->AsDouble());
  else 
    value = Value::make((Object*) object);
}


PyObject*
objectFromValue(const Value& value)
{
  switch (value.getType()) {
  case Value::TYPE_LONG:
    return Int::FromLong(value.cast_as_long());

  case Value::TYPE_DOUBLE:
    return Float::FromDouble(value.cast_as_double());

  case Value::TYPE_BOOL:
    return newBool(value.cast_as_bool());

  case Value::TYPE_OBJECT:
    return value.cast_as_object();

  default:
    abort();
  }
}


//----------------------------------------------------------------------

Operation::Type
getTypeByName(const char* name)
{
  for (int i = 0; i != (int) Operation::OP_LAST; ++i)
    if (strcmp(name, operation_names[i]) == 0)
      return (Operation::Type) i;

  return Operation::OP_LAST;
}


/* Convenience macros for use in 'evaluate', below.  */
#define ARG1_LONG   (op.arg1_.cast_as_long())
#define ARG2_LONG   (op.arg2_.cast_as_long())
#define ARG3_LONG   (op.arg3_.cast_as_long())
#define ARG4_LONG   (op.arg4_.cast_as_long())
#define ARG1_DOUBLE (op.arg1_.cast_as_double())
#define ARG2_DOUBLE (op.arg2_.cast_as_double())
#define ARG3_DOUBLE (op.arg3_.cast_as_double())
#define ARG4_DOUBLE (op.arg4_.cast_as_double())
#define ARG1_BOOL   (op.arg1_.cast_as_bool())
#define ARG2_BOOL   (op.arg2_.cast_as_bool())
#define ARG3_BOOL   (op.arg3_.cast_as_bool())
#define ARG4_BOOL   (op.arg4_.cast_as_bool())
#define ARG1_OBJECT (op.arg1_.cast_as_object())
#define ARG2_OBJECT (op.arg2_.cast_as_object())
#define ARG3_OBJECT (op.arg3_.cast_as_object())
#define ARG4_OBJECT (op.arg4_.cast_as_object())
#define POP_LONG    (st.pop().cast_as_long())
#define POP_DOUBLE  (st.pop().cast_as_double())
#define POP_BOOL    (st.pop().cast_as_bool())
#define POP_OBJECT  (st.pop().cast_as_object())
#define PEEK_LONG   (st.peek().cast_as_long())
#define PEEK_DOUBLE (st.peek().cast_as_double())
#define PEEK_BOOL   (st.peek().cast_as_bool())
#define PUSH(e)     st.push((e))

inline Value
getSymbolValueFromRow(Mapping* row,
		      int name_index)
{
  PyRow* row_obj = (PyRow*) row;
  std::vector<short>& column_index_map = 
    row_obj->table_->column_index_map_;
  int index;

  if (name_index < (int) column_index_map.size()
      && (index = column_index_map[name_index]) >= 0) {
    table::Row* row = row_obj->getRow();
    return row->getValue(index);
  }
  else 
    return Value();
}


/* Apply a math function to the double value at the top of the stack.

   Use this macro only in 'evaluate', below.  Pop a double value off the
   stack, apply 'FUNCTION' to it, and push the result onto the stack.
*/
#define PUSH_MATH_FN(FUNCTION)                                          \
  do {                                                                  \
    d0 = FUNCTION(POP_DOUBLE);                                          \
    if (finite(d0))                                                     \
      PUSH(d0);                                                         \
    else                                                                \
      throw Exception(PyExc_FloatingPointError,                         \
                      "floating point error in " #FUNCTION);            \
  } while (false)


Value
evaluate(const Operation* operations,
	 int num_operations,
	 Mapping* symbols,
	 bool is_row)
{
  const static bool trace = false;

  // Create a unique token, which we use to determine if 'get' returns
  // the default value.
  Ref<Object> token_class = import("hep", "Token");
  Ref<Object> token = cast<Callable>(token_class)->Call(NULL);

  // If we know that 'symbols' is a row (because 'is_row' says so), cast
  // it and fish some stuff out of it.
  PyRow* row_obj = NULL;
  std::vector<short>* column_index_map = NULL;
  int column_index_map_size = -1;
  std::vector<PyExpr*>* expr_map = NULL;
  int expr_map_size = -1;
  if (is_row) {
    row_obj = (PyRow*) symbols;
    column_index_map = &row_obj->table_->column_index_map_;
    column_index_map_size = column_index_map->size();
    expr_map = &row_obj->table_->expr_map_;
    expr_map_size = expr_map->size();
  }

  Stack st;
  int position = 0;
  while (position < num_operations) {
    const Operation& op = operations[position];
    int advance = 1;

    long l0, l1, l2;
    double d0, d1;
    bool b0, b1;

    if (trace) 
      std::cerr << st << " -- " << operation_names[op.type_] << '\n';

    try {
    switch (op.type_) {
    case Operation::OP_INVALID:
      throw Exception(PyExc_RuntimeError, "invalid operation");

    case Operation::OP_PUSH:
      PUSH(op.arg1_);
      break;

    case Operation::OP_JUMP:
      advance = 1 + ARG1_LONG;
      break;

    case Operation::OP_CONDITIONAL_JUMP:
      b0 = POP_BOOL;
      if (b0)
	advance = 1 + ARG1_LONG;
      break;

    //------------------------------------------------------------------
    // operations resulting in a 'long'

    case Operation::OP_LONG_SYMBOL:
      if (is_row) {
	static int index_name_index = symbol_name_table.find("_index");
	int name_index = ARG1_LONG;

	// Handle the name '_index' specially.
	if (name_index == index_name_index) {
	  PUSH((long) row_obj->index_);
	  break;
	}

	// Look up other names in the row.
	Value value = getSymbolValueFromRow(symbols, name_index);
	if (value.getType() != Value::TYPE_NONE) {
	  PUSH(value.cast_as_long());
	  break;
	}
      }
      {
	Ref<String> key = symbol_name_table.get(ARG1_LONG);
	Ref<Object> value = 
	  symbols->CallMethodObjArgs("get", key, (PyObject*) token, NULL);
	if (value == token)
	  throw Exception(PyExc_KeyError, "%s", key->AsString());
	PUSH(value->IntAsLong());
      }
      break;

    case Operation::OP_LONG_CAST_FROM_DOUBLE:
      d0 = POP_DOUBLE;
      if (d0 + 1 >= LONG_MAX || d0 - 1 < LONG_MIN)
	throw Exception(PyExc_OverflowError, 
			"too large to convert to long");
      PUSH((long) d0);
      break;

    case Operation::OP_LONG_CAST_FROM_BOOL:
      PUSH(POP_BOOL ? 1l : 0l);
      break;

    case Operation::OP_LONG_CAST_FROM_OBJECT:
      {
	Ref<Object> obj = POP_OBJECT;
	Ref<Int> as_int = obj->Int();
	PUSH(as_int->AsLong());
      }
      break;

    case Operation::OP_LONG_ABS:
      l0 = labs(POP_LONG);
      if (l0 < 0)
	throw Exception(PyExc_OverflowError, "too large for absolute value");
      PUSH(l0);
      break;

    case Operation::OP_LONG_NEGATE:
      l0 = POP_LONG;
      l1 = -l0;
      if (l0 < 0 && l1 < 0)
	throw Exception(PyExc_OverflowError, "too large for negation");
      PUSH(l1);
      break;

    case Operation::OP_LONG_ADD:
      l0 = POP_LONG;
      l1 = POP_LONG;
      l2 = l0 + l1;
      if ((l0 ^ l2) < 0 && (l1 ^ l2) < 0)
	throw Exception(PyExc_OverflowError, "too large for addition");
      PUSH(l2);
      break;

    case Operation::OP_LONG_SUBTRACT:
      l0 = POP_LONG;
      l1 = POP_LONG;
      l2 = l0 - l1;
      if ((l0 ^ l2) < 0 && (l2 ^ ~l1) < 0)
	throw Exception(PyExc_OverflowError, "too large for subtraction");
      PUSH(l2);
      break;

    case Operation::OP_LONG_MULTIPLY:
      // FIXME: Don't know how to test for multiplication overflows.
      PUSH(POP_LONG * POP_LONG);
      break;

    case Operation::OP_LONG_SQUARE:
      l0 = POP_LONG;
      PUSH(l0 * l0);
      break;

    case Operation::OP_LONG_FLOOR_DIVIDE:
      {
	l0 = POP_LONG;
	l1 = POP_LONG;
	// FIXME: Don't know how to test for division overflows.
	if (l1 == 0)
	  throw Exception(PyExc_ZeroDivisionError, "division by zero");
	long quotient = l0 / l1;
	// We want floor division (round toward negative infinity), not
	// truncated division (round toward zero).  So, push the
	// quotient down one if it is negative and if the remainder is
	// non-zero. 
	if (quotient < 0 && (l0 % l1) != 0)
	  --quotient;
	PUSH(quotient);
      }
      break;

    case Operation::OP_LONG_EXPONENTIATE:
      {
	l0 = POP_LONG;
	l1 = POP_LONG;
	assert(l1 >= 0);
	long result = 1l;
	while (l1-- > 0)
	  result *= l0;
	PUSH(result);
      }
      break;

    case Operation::OP_LONG_REMAINDER:
      {
	l0 = POP_LONG;
	l1 = POP_LONG;
	if (l1 == 0)
	  throw Exception(PyExc_ZeroDivisionError, 
			  "division by zero in remainder");
	long remainder = l0 % l1;
	// Python's convention is that the remainder is negative if the
	// divisor is. 
	if (remainder != 0 && l1 < 0)
	  remainder += l1;
	PUSH(remainder);
      }
      break;

    case Operation::OP_LONG_MAX:
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH(max(l0, l1));
      break;

    case Operation::OP_LONG_MIN:
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH(min(l0, l1));
      break;

    case Operation::OP_LONG_BITWISE_NOT:
      PUSH(~POP_LONG);
      break;

    case Operation::OP_LONG_BITWISE_AND:
      PUSH(POP_LONG & POP_LONG);
      break;

    case Operation::OP_LONG_BITWISE_OR:
      PUSH(POP_LONG | POP_LONG);
      break;

    case Operation::OP_LONG_BITWISE_XOR:
      PUSH(POP_LONG ^ POP_LONG);
      break;

    case Operation::OP_LONG_SHIFT_LEFT:
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH(l0 << l1);
      break;

    case Operation::OP_LONG_SHIFT_RIGHT:
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH(l0 >> l1);
      break;

    case Operation::OP_LONG_GET_BIT:
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH((l0 & (1 << l1)) != 0);
      break;

    //------------------------------------------------------------------
    // operations resulting in a 'double'

    case Operation::OP_DOUBLE_SYMBOL:
      if (is_row) {
	Value value = getSymbolValueFromRow(symbols, ARG1_LONG);
	if (value.getType() != Value::TYPE_NONE) {
	  PUSH(value.cast_as_double());
	  break;
	}
      }
      {
	Ref<String> key = symbol_name_table.get(ARG1_LONG);
	Ref<Object> value = 
	  symbols->CallMethodObjArgs("get", key, (PyObject*) token, NULL);
	if (value == token)
	  throw Exception(PyExc_KeyError, "%s", key->AsString());
	PUSH(value->FloatAsDouble());
      }
      break;

    case Operation::OP_DOUBLE_CAST_FROM_LONG: 
      PUSH((double) POP_LONG);
      break;

    case Operation::OP_DOUBLE_CAST_FROM_BOOL:
      PUSH(POP_BOOL ? 1.0 : 0.0);
      break;

    case Operation::OP_DOUBLE_CAST_FROM_OBJECT:
      {
	Ref<Object> obj = POP_OBJECT;
	Ref<Float> as_float = obj->Float();
	PUSH(as_float->AsDouble());
      }
      break;

    case Operation::OP_DOUBLE_ABS: 
      PUSH(fabs(POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_NEGATE: 
      PUSH(-POP_DOUBLE);
      break;

    case Operation::OP_DOUBLE_ADD: 
      PUSH(POP_DOUBLE + POP_DOUBLE);
      break;

    case Operation::OP_DOUBLE_SUBTRACT: 
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      PUSH(d0 - d1);
      break;

    case Operation::OP_DOUBLE_MULTIPLY: 
      PUSH(POP_DOUBLE * POP_DOUBLE);
      break;

    case Operation::OP_DOUBLE_SQUARE:
      d0 = POP_DOUBLE;
      PUSH(d0 * d0);
      break;

    case Operation::OP_DOUBLE_DIVIDE: 
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      if (d1 == 0)
	throw Exception(PyExc_ZeroDivisionError, "division by zero");
      PUSH(d0 / d1);
      break;
      
    case Operation::OP_DOUBLE_REMAINDER: 
      {
	d0 = POP_DOUBLE;
	d1 = POP_DOUBLE;
	if (d1 == 0)
	  throw Exception(PyExc_ZeroDivisionError, 
			  "division by zero in remainder");
	double remainder = fmod(d0, d1);
	if (remainder != 0 && ((d0 < 0) != (d1 < 0))) 
		remainder += d1;
	PUSH(remainder);
      }
      break;

    case Operation::OP_DOUBLE_EXPONENTIATE: 
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      if (d1 == 0)
	PUSH(1.0);
      else if (d0 == 0) {
	if (d1 < 0)
	  throw Exception(PyExc_ZeroDivisionError, 
			  "division by zero in exponentiation");
	else
	  PUSH(0.0);
      }
      else if (d0 < 0 && d1 != floor(d1))
	throw Exception(PyExc_ValueError, "domain error in exponentiation");
      else
	PUSH(pow(d0, d1));
      break;

    case Operation::OP_DOUBLE_EXP: 
      d0 = exp(POP_DOUBLE);
      if (finite(d0))
	PUSH(d0);
      else
	throw Exception(PyExc_OverflowError, "overflow in exp");
      break;
      
    case Operation::OP_DOUBLE_LOG: 
      d0 = POP_DOUBLE;
      if (d0 <= 0)
	throw Exception(PyExc_ValueError, "domain error in log");
      PUSH(log(d0));
      break;
      
    case Operation::OP_DOUBLE_SQRT: 
      PUSH_MATH_FN(sqrt);
      break;

    case Operation::OP_DOUBLE_HYPOT: 
      PUSH(hypot(POP_DOUBLE, POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_SIN: 
      PUSH(sin(POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_COS: 
      PUSH(cos(POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_TAN:  
      PUSH(tan(POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_ASIN:  
      PUSH_MATH_FN(asin);
      break;

    case Operation::OP_DOUBLE_ACOS:  
      PUSH_MATH_FN(acos);
      break;

    case Operation::OP_DOUBLE_ATAN:  
      PUSH(atan(POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_ATAN2:  
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      PUSH(atan2(d0, d1));
      break;

    case Operation::OP_DOUBLE_SINH:  
      PUSH_MATH_FN(sinh);
      break;

    case Operation::OP_DOUBLE_COSH:  
      PUSH_MATH_FN(cosh);
      break;

    case Operation::OP_DOUBLE_TANH:  
      PUSH_MATH_FN(tanh);
      break;

    case Operation::OP_DOUBLE_ASINH:  
      PUSH_MATH_FN(asinh);
      break;

    case Operation::OP_DOUBLE_ACOSH:  
      PUSH_MATH_FN(acosh);
      break;

    case Operation::OP_DOUBLE_ATANH:  
      PUSH_MATH_FN(atanh);
      break;

    case Operation::OP_DOUBLE_FLOOR:  
      PUSH(floor(POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_CEIL:  
      PUSH(ceil(POP_DOUBLE));
      break;

    case Operation::OP_DOUBLE_MAX:  
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      PUSH(max(d0, d1));
      break;

    case Operation::OP_DOUBLE_MIN:  
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      PUSH(min(d0, d1));
      break;

    case Operation::OP_DOUBLE_GAUSSIAN:
      {
	double mu = POP_DOUBLE;
	double sigma = POP_DOUBLE;
	double x = POP_DOUBLE;
	double result = (x - mu) / sigma;
	result = 0.3989422804014326779399 
	  * exp(-0.5 * result * result) / sigma;
	PUSH(result);
      }
      break;

    //------------------------------------------------------------------
    // operations resulting in a 'bool'

    case Operation::OP_BOOL_SYMBOL:
      if (is_row) {
	Value value = getSymbolValueFromRow(symbols, ARG1_LONG);
	if (value.getType() != Value::TYPE_NONE) {
	  PUSH(value.cast_as_bool());
	  break;
	}
      }
      {
	Ref<String> key = symbol_name_table.get(ARG1_LONG);
	Ref<Object> value = 
	  symbols->CallMethodObjArgs("get", key, (PyObject*) token, NULL);
	if (value == token)
	  throw Exception(PyExc_KeyError, "%s", key->AsString());
	PUSH(value->IsTrue());
      }
      break;

    case Operation::OP_BOOL_CACHE_GET:
      {
	unsigned char* mask_bits = (unsigned char*) ARG1_LONG;
	int length = ARG3_LONG;
	int index = ((PyRow*) symbols)->index_;
	// Is the index in the range of the cache, and do we have a
	// cached value for this index?
	if (index < length
	    && (mask_bits[index / 8] & (1 << (index % 8))) != 0) {
	  // Yes.  Look up the value.
	  unsigned char* value_bits = (unsigned char*) ARG2_LONG;
	  bool value = (value_bits[index / 8] & (1 << (index % 8))) != 0;
	  // Push it on to the stack.
	  PUSH(value);
	  // Skip the next bunch of operations, which would have
	  // computed the value had there been no cached value.
	  advance = 1 + ARG4_LONG;
	}
      }
      break;

    case Operation::OP_BOOL_CACHE_SET:
      {
	unsigned char* mask_bits = (unsigned char*) ARG1_LONG;
	unsigned char* value_bits = (unsigned char*) ARG2_LONG;
	int length = ARG3_LONG;
	int index = ((PyRow*) symbols)->index_;
	// Make sure we're in the range of the cache.
	if (index < length) {
	  // Set the mask bit to indicate we have a cached value for
	  // this index.
	  mask_bits[index / 8] |= (1 << (index % 8));
	  // Set the value.
	  if (PEEK_BOOL)
	    value_bits[index / 8] |= (1 << (index % 8));
	  else
	    value_bits[index / 8] &= ~(1 << (index % 8));
	}
      }
      break;

    case Operation::OP_BOOL_CAST_FROM_OBJECT:
      {
	Ref<Object> o = POP_OBJECT;
	PUSH(o->IsTrue());
      }
      break;

    case Operation::OP_BOOL_CAST_FROM_DOUBLE:
      d0 = POP_DOUBLE;
      PUSH((bool) (d0 != 0.0));
      break;

    case Operation::OP_BOOL_CAST_FROM_LONG:
      l0 = POP_LONG;
      PUSH((bool) (l0 != 0));
      break;

    case Operation::OP_BOOL_NOT:  
      PUSH(! POP_BOOL);
      break;

    case Operation::OP_BOOL_AND:  
      b0 = POP_BOOL;
      b1 = POP_BOOL;
      PUSH(b0 && b1);
      break;

    case Operation::OP_BOOL_AND_LAZY:
      // Lazy-evaluation version of "and".  This operation must be
      // placed between the two subexpressions that are to be logically
      // combined.  The argument is the number of instructions in the
      // second operation.

      // Take a look at the result of the first subexpression.
      b0 = PEEK_BOOL;
      if (b0)
	// It's true, so we have to evaluate the second subexpression.
	// Take the result off the stack.  Continue with the second
	// subexpression; the result it leaves on the stack will be the
	// result of the entire "and" expression.
	POP_BOOL;
      else
	// It's false, so the whole "and" expression is false.  Leave
	// the false result on the stack, and skip over the second
	// subexpression.
	advance = 1 + ARG1_LONG;
      break;

    case Operation::OP_BOOL_OR:  
      b0 = POP_BOOL;
      b1 = POP_BOOL;
      PUSH(b0 || b1);
      break;

    case Operation::OP_BOOL_OR_LAZY:
      // Lazy-evaluation version of "or".  This operation must be
      // placed between the two subexpressions that are to be logically
      // combined.  The argument is the number of instructions in the
      // second operation.

      // Take a look at the result of the first subexpression.
      b0 = PEEK_BOOL;
      if (b0)
	// It's true, so the whole "or" expression is true.  Leave the
	// true result on the stack, and skip over the second
	// subexpression.
	advance = 1 + ARG1_LONG;
      else
	// It's false, so we have to evaluate the second subexpression.
	// Take the result off the stack.  Continue with the second
	// subexpression; the result it leaves on the stack will be the
	// result of the entire "or" expression.
	POP_BOOL;
      break;

    case Operation::OP_BOOL_XOR:  
      b0 = POP_BOOL;
      b1 = POP_BOOL;
      PUSH((b0 && ! b1) || (! b0 && b1));
      break;

    case Operation::OP_BOOL_EQUALS_LONG:  
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH((bool) (l0 == l1));
      break;

    case Operation::OP_BOOL_LESS_THAN_LONG:  
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH((bool) (l0 < l1));
      break;

    case Operation::OP_BOOL_LESS_THAN_OR_EQUAL_LONG:  
      l0 = POP_LONG;
      l1 = POP_LONG;
      PUSH((bool) (l0 <= l1));
      break;

    case Operation::OP_BOOL_EQUALS_DOUBLE:  
      PUSH((bool) (POP_DOUBLE == POP_DOUBLE));
      break;

    case Operation::OP_BOOL_LESS_THAN_DOUBLE:  
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      PUSH((bool) (d0 < d1));
      break;

    case Operation::OP_BOOL_LESS_THAN_OR_EQUAL_DOUBLE:  
      d0 = POP_DOUBLE;
      d1 = POP_DOUBLE;
      PUSH((bool) (d0 <= d1));
      break;

    case Operation::OP_BOOL_IN_RANGE_DOUBLE:
      {
	double min = POP_DOUBLE;
	double value = POP_DOUBLE;
	double max = POP_DOUBLE;
	PUSH(value >= min && value < max);
      }
      break;

    case Operation::OP_BOOL_IN_RANGE_LONG:
      {
	long min = POP_LONG;
	long value = POP_LONG;
	long max = POP_LONG;
	PUSH(value >= min && value < max);
      }
      break;

    case Operation::OP_BOOL_NEAR_DOUBLE:
      {
	double central_value = POP_DOUBLE;
	double half_interval = POP_DOUBLE;
	double value = POP_DOUBLE;
	value -= central_value;
	PUSH(value > -half_interval && value < half_interval);
      }
      break;

    case Operation::OP_BOOL_NEAR_LONG:
      {
	long central_value = POP_LONG;
	long half_interval = POP_LONG;
	long value = POP_LONG;
	value -= central_value;
	PUSH(value > -half_interval && value < half_interval);
      }
      break;

    case Operation::OP_BOOL_EQUALS_OBJECT:  
      {
	Ref<Object> o1 = POP_OBJECT;
	Ref<Object> o2 = POP_OBJECT;
	PUSH(o1->Compare(o2));
      }
      break;

    //------------------------------------------------------------------
    // operations resulting in a Python object

    case Operation::OP_OBJECT_SYMBOL:
      if (is_row) {
	static int row_name_index = symbol_name_table.find("_row");
	static int table_name_index = symbol_name_table.find("_table");
	int name_index = ARG1_LONG;

	// Handle the name '_row' specially: return the row object.
	if (name_index == row_name_index) {
	  PUSH(row_obj);
	  break;
	}

	// Handle the name '_table' specially: return the table.
	if (name_index == table_name_index) {
	  PUSH((Py::Object*) row_obj->table_);
	  break;
	}

	// Look up other names in the row.
	Value value = getSymbolValueFromRow(symbols, name_index);
	if (value.getType() != Value::TYPE_NONE) {
	  PUSH(value.cast_as_object());
	  break;
	}
      }
      {
	Ref<String> key = symbol_name_table.get(ARG1_LONG);
	Ref<Object> value = 
	  symbols->CallMethodObjArgs("get", key, (PyObject*) token, NULL);
	if (value == token)
	  throw Exception(PyExc_KeyError, "%s", key->AsString());
	PUSH(value);
      }
      break;

    case Operation::OP_OBJECT_EXPRESSION:
      {
	Ref<Object> evaluate_obj = ARG1_OBJECT;
	Callable* evaluate = cast<Callable>(evaluate_obj);
	Ref<Object> result = 
	  evaluate->CallFunctionObjArgs(symbols, NULL);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_GET_ATTR_CONST:
      {
	Ref<Object> object = POP_OBJECT;
	Ref<Object> attr_name = ARG1_OBJECT;
	Ref<Object> result = object->GetAttr(attr_name);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_CAST_FROM_LONG:
      {
	l0 = POP_LONG;
	Ref<Int> o = Int::FromLong(l0);
	PUSH((Object*) o);
      }
      break;

    case Operation::OP_OBJECT_CAST_FROM_DOUBLE:
      {
	d0 = POP_DOUBLE;
	Ref<Float> o = Float::FromDouble(d0);
	PUSH((Object*) o);
      }
      break;

    case Operation::OP_OBJECT_CAST_FROM_BOOL:
      {
	b0 = POP_BOOL;
	Ref<Object> o = newBool(b0);
	PUSH(o);
      }
      break;

    case Operation::OP_OBJECT_SIMPLE_CALL:
      // This operation represents a call to a fixed function with
      // positional arguments only.  The function is in ARG1.  ARG2
      // contains the number of positional arguments; they are popped
      // from the stack.
      {
	Ref<Object> function_obj = POP_OBJECT;
	Callable* function = cast<Callable>(function_obj);
	int number_of_args = ARG1_LONG;
	// Construct the argument list.
	Ref<Tuple> args = Tuple::New(number_of_args);
	for (int i = 0; i < number_of_args; ++i) {
	  Ref<Object> arg = POP_OBJECT;
	  args->InitializeItem(i, arg);
	}
	// Call the function.
	Ref<Object> result = function->Call(args);
	PUSH(result);
      }
      break;

/* FIXME
    case Operation::OP_OBJECT_FUNCTION_CALL:
      {
	// The function to call and a template of argument names are
	// stored as an argument.
	Ref<Object> function_obj = ARG1_OBJECT;
	Callable* function = cast<Callable>(function_obj);
	Ref<Object> args_template_obj = ARG2_OBJECT;
	Dict* args_template = cast<Dict>(args_template_obj);
	// The argument template maps names of arguments of 'function'
	// to corresponding column indices.  Construct a parallel
	// dictionary whose values are the actual row values.
	Ref<Dict> kw_args = Dict::New();
	int iter_pos = 0;
	PyObject* name_obj;
	PyObject* column_index_obj;
	// Iterate over the dictionary, fishing out the argument names
	// and column indices.  
	while (args_template->Next(iter_pos, name_obj, column_index_obj)) {
	  String* name = cast<String>(name_obj);
	  int column_index = cast<Int>(column_index_obj)->AsLong();
	  // Look up the column value.
	  Ref<Object> value = 
	    objectFromValue(row->getRow()->getValue(column_index));
	  // Update the keyword argument dictionary.
	  kw_args->SetItem(name, value);
	}
	// Call the function.  There are no positional arguments.
	// Keyword arguments are satisfied with column values, as
	// constructed above.
	Ref<Tuple> args = Tuple::New(0);
	Ref<Object> result = function->Call(args, kw_args);
	// All done.
	PUSH(result);
      }
      break;
*/

    case Operation::OP_OBJECT_NEGATE:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> result = n1->Negative();
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_ADD:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> o2 = POP_OBJECT;
	Number* n2 = cast<Number>(o2);
	Ref<Object> result = n1->Add(n2);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_SUBTRACT:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> o2 = POP_OBJECT;
	Number* n2 = cast<Number>(o2);
	Ref<Object> result = n1->Subtract(n2);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_MULTIPLY:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> o2 = POP_OBJECT;
	Number* n2 = cast<Number>(o2);
	Ref<Object> result = n1->Multiply(n2);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_DIVIDE:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> o2 = POP_OBJECT;
	Number* n2 = cast<Number>(o2);
	Ref<Object> result = n1->TrueDivide(n2);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_FLOOR_DIVIDE:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> o2 = POP_OBJECT;
	Number* n2 = cast<Number>(o2);
	Ref<Object> result = n1->FloorDivide(n2);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_REMAINDER:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> o2 = POP_OBJECT;
	Number* n2 = cast<Number>(o2);
	Ref<Object> result = n1->Remainder(n2);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_EXPONENTIATE:
      {
	Ref<Object> o1 = POP_OBJECT;
	Number* n1 = cast<Number>(o1);
	Ref<Object> o2 = POP_OBJECT;
	Number* n2 = cast<Number>(o2);
	Ref<Object> result = n1->Power(n2);
	PUSH(result);
      }
      break;

    case Operation::OP_OBJECT_SUBSCRIPT:
      {
	Ref<Object> o1 = POP_OBJECT;
	Ref<Object> o2 = POP_OBJECT;
	Ref<Object> result = o1->GetItem(o2);
	PUSH(result);
      }
      break;

    default:
      std::cerr << "error: cannot evaluate operation type " 
		<< operation_names[op.type_] << std::endl;
      abort();
    };  // switch
    }  // try
    catch (TypeError err) {
      std::cerr 
	<< "ERROR: Type error while evaluating a compiled expression.\n"
	<< "  operation = " << operation_names[op.type_] 
	<< " at position " << position << '\n'
	<< "  stack: " << st << '\n';
      abort();
    }

    assert(advance >= 1);
    position += advance;
  }

  Value result = st.pop();
  if (! st.isEmpty()) {
    std::cerr << "ERROR: Non-empty stack after evaluating a compiled "
	      << "expression.\n";
    abort();
  }
  return result;
}


}  // anonymous namespace

//----------------------------------------------------------------------
// methods
//----------------------------------------------------------------------

PyExpr::PyExpr()
  : num_operations_(0),
    type_(newRef(None))
{
  len_operations_ = 4;
  operations_ = (Operation*) malloc(len_operations_ * sizeof(Operation));
  assert(operations_ != NULL);
}


PyExpr::~PyExpr()
{
  assert(operations_ != NULL);
  free(operations_);
}


void
PyExpr::append(Operation::Type type,
	       const Value& arg1,
	       const Value& arg2,
	       const Value& arg3,
	       const Value& arg4)
{
  if (len_operations_ == num_operations_) {
    len_operations_ *= 2;
    operations_ = (Operation*) 
      realloc(operations_, len_operations_ * sizeof(Operation));
    assert(operations_ != NULL);
  }

  operations_[num_operations_].type_ = type;
  operations_[num_operations_].arg1_ = arg1;
  operations_[num_operations_].arg2_ = arg2;
  operations_[num_operations_].arg3_ = arg3;
  operations_[num_operations_].arg4_ = arg4;
  ++num_operations_;
}


inline Value 
PyExpr::evaluate(Py::Mapping* symbols)
{
  // We can do symbol lookups much faster if we know it is a row.
  return evaluate(symbols, symbols->IsInstance(&PyRow::type));
}


inline Value 
PyExpr::evaluate(Py::Mapping* symbols,
		 bool is_row)
{
  return ::evaluate(operations_, num_operations_, symbols, is_row);
}


//----------------------------------------------------------------------
// Python type
//----------------------------------------------------------------------

namespace {

PyObject*
tp_new(PyTypeObject* type,
       Tuple* args,
       Dict* kw_args)
try {
  // Parse arguments.
  args->ParseTuple("");

  return PyExpr::New();
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyExpr* self)
try {
  // Perform C++ deallocation.
  self->~PyExpr();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
}


PyObject*
tp_call(PyExpr* self,
	Arg* args,
	Dict* kw_args)
try {
  // No positional arguments expected.
  args->ParseTuple("");
  
  Ref<Dict> symbols;
  if (kw_args == NULL)
    symbols = Dict::New();
  else
    symbols = newRef(kw_args);

  return objectFromValue(self->evaluate(symbols));
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_repr(PyExpr* self)
try {
  std::string s = "Expr(";

  for (int o = 0; o < self->num_operations_; ++o) {
    if (o > 0)
      s += ", ";

    const Operation& op = self->operations_[o];
    s += operation_names[op.type_];

    if (op.type_ == Operation::OP_LONG_SYMBOL
	|| op.type_ == Operation::OP_DOUBLE_SYMBOL
	|| op.type_ == Operation::OP_BOOL_SYMBOL
	|| op.type_ == Operation::OP_OBJECT_SYMBOL) {
      Ref<String> symbol_name = symbol_name_table.get(op.arg1_.as_long());
      s += " '";
      s += symbol_name->AsString();
      s += '\'';
    }
    else if (op.arg1_.getType() != Value::TYPE_NONE) {
      s += std::string(" ") +  op.arg1_.asString();
      if (op.arg2_.getType() != Value::TYPE_NONE) 
	s += std::string(" ") + op.arg2_.asString();
      if (op.arg3_.getType() != Value::TYPE_NONE) 
	s += std::string(" ") + op.arg3_.asString();
      if (op.arg4_.getType() != Value::TYPE_NONE) 
	s += std::string(" ") + op.arg4_.asString();
    }
  }

  s += ")";
  return String::FromString(s.c_str());
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_str(PyExpr* self)
try {
  if (self->HasAttrString("formula"))
    return self->GetAttrString("formula");
  else
    return tp_repr(self);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_append(PyExpr* self,
	      Arg* args)
try {
  String* op_name;
  Object* type;
  Object* arg1_obj = NULL;
  Object* arg2_obj = NULL;
  Object* arg3_obj = NULL;
  Object* arg4_obj = NULL;
  args->ParseTuple("SO|OOOO", 
      &op_name, &type, &arg1_obj, &arg2_obj, &arg3_obj, &arg4_obj);

  Operation::Type op_type = getTypeByName(op_name->AsString());
  if (op_type == Operation::OP_LAST)
    throw Exception(PyExc_ValueError, 
		    "unknown operation '%s'", op_name->AsString());

  Value arg1;
  if (arg1_obj != NULL)
    valueFromObject(arg1_obj, arg1);
  Value arg2;
  if (arg2_obj != NULL)
    valueFromObject(arg2_obj, arg2);
  Value arg3;
  if (arg3_obj != NULL)
    valueFromObject(arg3_obj, arg3);
  Value arg4;
  if (arg4_obj != NULL)
    valueFromObject(arg4_obj, arg4);

  self->type_ = newRef(type);
  self->append(op_type, arg1, arg2, arg3, arg4);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_evaluate(PyExpr* self,
		Arg* args)
try {
  Mapping* symbols;
  args->ParseTuple("O", &symbols);

  return objectFromValue(self->evaluate(symbols));
}
catch (Exception) {
  std::cerr << "warning: Python exception during expression evaluation\n";
  return NULL;
}
catch (...) {
  // FIXME.
  std::cerr << "warning: C++ exception during expression evaluation\n";
  return NULL;
}


PyObject*
method_extend(PyExpr* self,
	      Arg* args)
try {
  PyExpr* expr;
  args->ParseTuple("O!", &PyExpr::type, &expr);
  
  for (int i = 0; i < expr->num_operations_; ++i) {
    const Operation& op = expr->operations_[i];
    self->append(op.type_, op.arg1_, op.arg2_, op.arg3_, op.arg4_);
  }

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "append", (PyCFunction) method_append, METH_VARARGS, NULL },
  { "evaluate", (PyCFunction) method_evaluate, METH_VARARGS, NULL },
  { "extend", (PyCFunction) method_extend, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


struct PyMemberDef
tp_members[] = {
  { "formula", T_OBJECT, offsetof(PyExpr, formula_), 0, NULL },
  { NULL, 0, 0, 0, NULL }
};


PyObject*
get_length(PyExpr* self,
	   void* /* closure */)
try {
  return Int::FromLong(self->num_operations_);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_type(PyExpr* self,
	 void* /* closure */)
try {
  return newRef((Object*) self->type_);
}
catch (Exception) {
  return NULL;
}


PyGetSetDef
tp_getset[] = {
  { "length", (getter) get_length, NULL, NULL, NULL },
  { "type", (getter) get_type, NULL, NULL, NULL },
  { NULL, NULL, NULL, NULL },
};


}  // anonymous namespace


PyTypeObject
PyExpr::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Expr",                               // tp_name
  sizeof(PyExpr),                       // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  (reprfunc) tp_repr,                   // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  NULL,                                 // tp_as_mapping
  NULL,                                 // tp_hash
  (ternaryfunc) tp_call,                // tp_call
  (reprfunc) tp_str,                    // tp_str
  NULL,                                 // tp_getattro
  NULL,                                 // tp_setattro
  NULL,                                 // tp_as_buffer
  Py_TPFLAGS_DEFAULT 
  | Py_TPFLAGS_BASETYPE,                // tp_flags
  NULL,                                 // tp_doc
  NULL,                                 // tp_traverse
  NULL,                                 // tp_clearurn
  NULL,                                 // tp_richcompare
  0,                                    // tp_weaklistoffset
  NULL,                                 // tp_iter
  NULL,                                 // tp_iternext
  tp_methods,                           // tp_methods
  tp_members,                           // tp_members
  tp_getset,                            // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) tp_new,                     // tp_new
};


//----------------------------------------------------------------------
// functions
//----------------------------------------------------------------------

PyObject*
function_get_symbol_index(Object* self,
			  Arg* args)
{
  Object* name_arg;
  args->ParseTuple("O", &name_arg);

  Ref<String> name = name_arg->Str();
  int index = symbol_name_table.find(name);
  return Int::FromLong(index);
}
