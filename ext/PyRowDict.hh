//----------------------------------------------------------------------
//
// PyRowDict.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

#ifndef PYROWDICT_HH
#define PYROWDICT_HH

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include "PyRow.hh"

//----------------------------------------------------------------------
// class definitions
//----------------------------------------------------------------------

struct PyRowDict
  : public PyRow
{
  static PyTypeObject type;
  static PyRowDict* New(PyTable* table, int index, 
			PyTypeObject* type=&type);
  static bool Check(PyObject* object);

  PyRowDict(PyTable* table, int index);
  ~PyRowDict();

};


//----------------------------------------------------------------------
// inline function definitions
//----------------------------------------------------------------------

inline PyRowDict*
PyRowDict::New(PyTable* table,
	       int index,
	       PyTypeObject* type)
{
  // Construct the Python object.
  PyRowDict* result = (PyRowDict*) Py::allocate(type);
  // Perform C++ initialization.
  try {
    new(result) PyRowDict(table, index);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }
  // All done.
  return result;
}


inline bool
PyRowDict::Check(PyObject* object)
{
  return ((Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------

#endif  // #ifndef PYROWDICT_HH
