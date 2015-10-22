//----------------------------------------------------------------------
//
// PyRow.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python extension class for a row in a PyTable table.  

A 'PyRow' object provides a mapping interface to a table row.  The map
has a key for each column in the table; the corresponding value is the
row's value for that column.  

In addition, the special '_index' element maps to the row's index in the
table, and the special '_table' element maps to the table.  
*/

#ifndef PYROW_HH
#define PYROW_HH

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>

#include "python.hh"
#include "table.hh"

//----------------------------------------------------------------------
// forward declarations
//----------------------------------------------------------------------

class PyRowObject;
class PyTable;

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

/* The name of the key by which the row's index is accessed.  */
extern Py::Ref<Py::String> PyRow_index_key;

/* The name of the key by which the row's containing table is accessed.  */
extern Py::Ref<Py::String> PyRow_table_key;

//----------------------------------------------------------------------
// class definitions
//----------------------------------------------------------------------

struct PyRow
  : public Py::Object
{
  static PyTypeObject type;
  static PyRow* New(PyTable* table, int index, PyTypeObject* type=&type);
  static bool Check(PyObject* object);
  static void Delete(PyRow* row);

  /* Construct a row object for row 'index' in 'table'.  

     The row might not be read from the table until a value is accessed.  
  */
  PyRow(PyTable* table, int index);

  ~PyRow();

  /* Return the underlying 'Row' object.  */
  table::Row* getRow() const;

  /* Return the value of column 'column_index' as a Python object.  */
  Py::Object* getColumn(table::ColumnType type, int column_index);

  /* Return the valueof a column as a Python object.  

     'default' -- The default value to return, if 'key' is not a column
     name.  If 'NULL', raise an exception instead.

     'exception' -- The exception to raise if 'key' is not a column name
     and 'default' is 'NULL'.  

     returns -- The result (or default value), or NULL if 'key' is not a
     column name and neither 'default' or 'exception' are non-NULL.  
  */
  Py::Object* getColumn(Object* key, Object* default_value, 
			PyObject* exception);

  /* The table of which this is a row.  */
  Py::Ref<PyTable> table_;

  /* The index of this row in its table, or -1 if not in a table.  */
  int index_;

  /* True if 'row_' contains the data read from the table for 'index_'.   */
  mutable bool read_;

private:

  /* Pointer to the underlying row.  

     Initially NULL, and allocated on first use by getRow.
  */
  mutable table::Row* row_;

};


//----------------------------------------------------------------------
// inline function definitions
//----------------------------------------------------------------------

inline PyRow* 
PyRow::New(PyTable* table, 
	   int index,
	   PyTypeObject* type)
{
  // Construct the Python object for the row.
  PyRow* result = (PyRow*) type->tp_alloc(type, 0);
  if (result == NULL)
    throw Py::Exception();
  // Perform C++ construction.
  try {
    new(result) PyRow(table, index);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }

  return result;
}


inline bool
PyRow::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


/* Return a Python object for the value of column 'column_index' in 'row'.

   'row' -- The row from which to extract the column value.

   'type' -- The type of column 'column_index'.

   returns -- A new reference.  
*/

inline Py::Object*
PyRow::getColumn(table::ColumnType type,
		 int column_index)
{
  Value val = getRow()->getValue(column_index);

  switch (type) {
  case table::TYPE_BOOL:
    return Py::newBool(val.as_bool());

  case table::TYPE_INT_8:
  case table::TYPE_INT_16:
  case table::TYPE_INT_32:
    return Py::Int::FromLong(val.as_long());

  case table::TYPE_FLOAT_32:
  case table::TYPE_FLOAT_64:
    return Py::Float::FromDouble(val.as_double());

  case table::TYPE_COMPLEX_64:
  case table::TYPE_COMPLEX_128:
    return Py::Complex::FromComplex(val.as_complex());

  default:
    throw Py::Exception(PyExc_NotImplementedError, 
			"unsupported column type %d", (int) type);
  }
}


inline void
PyRow::Delete(PyRow* row)
{
  // Make sure the row object is not in use.
  assert(row->GetRefCount() == 0);
  // Perform C++ deallocation.
  row->~PyRow();
  // Deallocate memory.
  PyMem_DEL(row);
}


//----------------------------------------------------------------------

#endif  // #ifndef PYROW_HH
