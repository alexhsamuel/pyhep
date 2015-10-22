//----------------------------------------------------------------------
//
// PyExpr.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Extension class for fast evaluation of expressions on rows.  */

#ifndef PYEXPR_HH
#define PYEXPR_HH

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>
#include <vector>

#include "nametable.hh"
#include "PyRow.hh"
#include "python.hh"
#include "value.hh"

//----------------------------------------------------------------------
// variables
//----------------------------------------------------------------------

/* A name table containing names of columns.

   Each symbol operation is associated with a symbol name.  Rather than
   store the symbol name with the operation, we store a name index
   obtained from this name table.

   This is used to speed up lookups of columns in table rows.  Each 
   table stores an association between name indices in this table and
   its own column indices, for quick lookup.  
*/
extern Nametable 
symbol_name_table;

//----------------------------------------------------------------------
// class definitions
//----------------------------------------------------------------------

struct Operation
{
  enum Type {
#define OPERATION(X) OP_ ## X,
#include "operations"
#undef OPERATION
    OP_LAST
  };

  Type type_;
  Value arg1_;
  Value arg2_;
  Value arg3_;
  Value arg4_;

};


struct PyExpr
  : public Py::Object
{
  static PyTypeObject type;
  static PyExpr* New();
  static bool Check(PyObject* object);
  
  PyExpr();
  ~PyExpr();

  void append(Operation::Type type, 
	      const Value& arg1=Value(), 
	      const Value& arg2=Value(),
	      const Value& arg3=Value(),
	      const Value& arg4=Value());

  Value evaluate(Py::Mapping* symbols);
  Value evaluate(Py::Mapping* symbols, bool is_row);

  Operation* operations_;
  int num_operations_;
  int len_operations_;
  Py::Ref<Py::Object> type_;
  Py::Ref<Py::String> formula_;

};


//----------------------------------------------------------------------
// inline function definitions
//----------------------------------------------------------------------

inline
PyExpr*
PyExpr::New()
{
  // Construct the Python object.
  PyExpr* result = Py::allocate<PyExpr>();
  // Perform C++ initialization.
  try {
    new(result) PyExpr();
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }

  return result;
}


inline bool
PyExpr::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern PyObject*
function_get_symbol_index(Py::Object* self, Py::Arg* args);

//----------------------------------------------------------------------

#endif  // #ifndef PYEXPR_HH
