//----------------------------------------------------------------------
//
// PyIterator.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Table iterator class.  */

#ifndef PYITERATOR_HH
#define PYITERATOR_HH

//----------------------------------------------------------------------
// imports
//----------------------------------------------------------------------

#include "PyBoolArray.hh"
#include "PyRow.hh"
#include "python.hh"

//----------------------------------------------------------------------
// forward declarations
//----------------------------------------------------------------------

class PyTable;

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

struct PyIterator
  : public Py::Object
{
  static PyTypeObject type;
  static PyIterator* New(PyTable* table, PyObject* selection);

  PyIterator(PyTable* table, Py::Object* selection=NULL);

  // The table being iterated over.
  Py::Ref<PyTable> table_;

  // The index of the next row to consider.
  int index_;

  // The selection function, or NULL for every row.
  Py::Ref<Py::Object> selection_;

  // If the selection function is a cached expression, the mask and data
  // for that expression.
  Py::Ref<PyBoolArray> cache_mask_;
  Py::Ref<PyBoolArray> cache_data_;

};


inline PyIterator*
PyIterator::New(PyTable* table,
		PyObject* selection)
{
  // Construct the Python object for the iterator.
  PyIterator* result = Py::allocate<PyIterator>();
  // Perform C++ construction.
  try {
    new(result) PyIterator(table, (Py::Object*) selection);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }

  return result;
}


//----------------------------------------------------------------------

#endif  // #ifndef PYITERATOR_HH
