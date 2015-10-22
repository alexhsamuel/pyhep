//----------------------------------------------------------------------
//
// PyRowObject.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python class for object representation of a row in a PyTable table.  

A 'PyRowObject' provides an object representation of a row, i.e. an
object whose attributes are named for columns in the table and whose
corresponding values are the values in the row.
*/

#ifndef PYROWOBJECT_HH
#define PYROWOBJECT_HH

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <Python.h>

#include "PyRow.hh"
#include "python.hh"
#include "table.hh"

//----------------------------------------------------------------------
// Python types
//----------------------------------------------------------------------

struct PyRowObject
  : public PyRow
{
  static PyTypeObject type;
  static PyRowObject* New(PyTable* table, int index, 
			  PyTypeObject* type=&type);
  static bool Check(PyObject* object);

  PyRowObject(PyTable* table, int index);
  ~PyRowObject();

};


inline PyRowObject* 
PyRowObject::New(PyTable* table,
		 int index,
		 PyTypeObject* type)
{
  // Construct the Python object for the row.
  PyRowObject* result = (PyRowObject*) Py::allocate(type);
  // Perform C++ construction.
  try {
    new(result) PyRowObject(table, index);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }
  // All done.
  return result;
}


inline bool
PyRowObject::Check(PyObject* object)
{
  return ((Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------

#endif  // #ifndef PYROWOBJECT_HH
