//----------------------------------------------------------------------
//
// PyRow.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>
#include <algorithm>
#include <memory>

#include "PyRow.hh"
#include "PyRowObject.hh"
#include "PyTable.hh"
#include "python.hh"

using namespace Py;
using namespace table;

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

Ref<String> 
PyRow_index_key = String::InternFromString("_index");

Ref<String> 
PyRow_table_key = String::InternFromString("_table");

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyRow::PyRow(PyTable* table,
	     int index)
  : table_(Ref<PyTable>::create(table)),
    index_(index),
    read_(false),
    row_(NULL)
{
  assert(table_ != NULL);
}


PyRow::~PyRow()
{
  if (row_ != NULL) 
    table_->returnRow(row_);
}


Row*
PyRow::getRow()
  const
{
  if (row_ == NULL)
    row_ = table_->getRow(index_);
  return row_;
}


Object*
PyRow::getColumn(Object* key,
		 Object* default_value,
		 PyObject* exception)
{
  // Use interned strings to look up names in tables.
  Ref<String> key_str = key->Str();
  internInPlace(key_str);

  // Try to find a column by that name.
  ColumnType type;
  int column_index = table_->findColumn(key_str, type);
  if (column_index != -1) 
    // It's a column.  Return the corresponding column value.
    return getColumn(type, column_index);

  // Is it the special name for the index or table?
  if (PyRow_index_key->Compare(key))
    return Int::FromLong(index_);
  if (PyRow_table_key->Compare(key))
    RETURN_NEW_REF(Object, table_);

  // Couldn't find a match for this name.
  if (default_value != NULL) 
    RETURN_NEW_REF(Object, default_value);
  else if (exception != NULL)
    throw Exception(exception, "%s", key_str->AsString());
  else
    return NULL;
}


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

namespace {

PyObject*
tp_new(PyTypeObject* type,
       Tuple* args,
       Dict* kw_args)
try {
  // Parse arguments.
  PyTable* table;
  int index;
  args->ParseTuple("O!i", &PyTable::type, &table, &index);
  
  return PyRow::New(table, index, type);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyRow* self)
try {
  // Destroy the row.
  self->~PyRow();
  self->ob_type->tp_free(self);
}
catch (Exception) {
}


int
tp_compare(PyRow* self,
	   PyObject* other)
try {
  if (! PyRow::Check(other))
    return -1;
  PyRow* other_row = (PyRow*) other;
  return (self->table_ == other_row->table_ 
	  && self->index_ == other_row->index_)
    ? 0 : -1;
}
catch (Exception) {
  return -1;
}


PyObject*
tp_str(PyRow* self)
try {
  return String::FromFormat("<Row at %p>", (void*) self);
}
catch (Exception) {
  return NULL;
}


}  // anonumous namespace

PyTypeObject
PyRow::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Row",                                // tp_name
  sizeof(PyRow),                        // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  (cmpfunc) tp_compare,                 // tp_compare
  (reprfunc) tp_str,                    // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  NULL,                                 // tp_as_mapping
  NULL,                                 // tp_hash
  NULL,                                 // tp_call
  (reprfunc) tp_str,                    // tp_str
  NULL,                                 // tp_getattro
  NULL,                                 // tp_setattro
  NULL,                                 // tp_as_buffer
  Py_TPFLAGS_DEFAULT 
  | Py_TPFLAGS_BASETYPE,                // tp_flags
  NULL,                                 // tp_doc
  NULL,                                 // tp_traverse
  NULL,                                 // tp_clear
  NULL,                                 // tp_richcompare
  0,                                    // tp_weaklistoffset
  NULL,                                 // tp_iter
  NULL,                                 // tp_iternext
  NULL,                                 // tp_methods
  NULL,                                 // tp_members
  NULL,                                 // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) tp_new,                     // tp_new
};

