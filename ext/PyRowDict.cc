//----------------------------------------------------------------------
//
// PyRowDict.cc
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>
#include <algorithm>
#include <memory>
#include <string>

#include "PyRow.hh"
#include "PyRowDict.hh"
#include "PyTable.hh"
#include "python.hh"
#include "table.hh"

using namespace Py;
using namespace table;

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyRowDict::PyRowDict(PyTable* table,
		     int index)
  : PyRow(table, index)
{
}


PyRowDict::~PyRowDict()
{
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
  
  return PyRowDict::New(table, index, type);
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_repr(PyRowDict* self)
try {
  Ref<String> table_repr = self->table_->Repr();
  return String::FromFormat("RowDict(%s, %d)", 
			    table_repr->AsString(), self->index_);
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_str(PyRowDict* self)
try {
  std::string result = "{";
  const Schema* schema = self->table_->table_->getSchema();
  for (int c = 0; c < schema->getNumColumns(); ++c) {
    const Column& column = schema->getColumn(c);
    if (c > 0)
      result += ", ";
    result += '\'';
    result += column.getName();
    result += "': ";
    Ref<Object> value = self->getColumn(column.getType(), c);
    Ref<String> repr = value->Repr();
    result += repr->AsString();
  }
  result += '}';
  return String::FromString(result.c_str());
}
catch (Exception) {
  return NULL;
}


int
mp_length(PyRowDict* self)
try {
  return self->table_->table_->getSchema()->getNumColumns();
}
catch (Exception) {
  return -1;
}


PyObject*
mp_subscript(PyRowDict* self,
	     Object* key)
try {
  return self->getColumn(key, NULL, PyExc_KeyError);
}
catch (Exception) {
  return NULL;
}


PyMappingMethods
tp_as_mapping = {
  (inquiry) mp_length,                  // mp_length
  (binaryfunc) mp_subscript,            // mp_subscript
  NULL,                                 // mp_ass_subscript
};


PyObject*
method_get(PyRowDict* self,
	   Arg* args)
try {
  Object* key;
  Object* default_value = (Object*) Py_None;
  args->ParseTuple("O|O", &key, &default_value);
  
  return self->getColumn(key, default_value, NULL);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_keys(PyRowDict* self,
	    Arg* args)
try {
  args->ParseTuple("");
  
  // Use the list of keys stored in the table.
  assert(self->table_->keys_ != NULL);
  Sequence* keys = cast<Sequence>(self->table_->keys_);
  // Copy it.
  return List::New(keys);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_items(PyRowDict* self,
	     Arg* args)
try {
  args->ParseTuple("");
  
  const Schema* schema = self->table_->table_->getSchema();

  // Loop over columns, building a tuple of items.
  unsigned num_columns = schema->getNumColumns();
  Ref<Tuple> result = Tuple::New(num_columns);
  for (unsigned c = 0; c < num_columns; ++c) {
    // Get the column.
    const Column& column = schema->getColumn(c);
    const char* column_name = column.getName().c_str();
    // Construct a (key, value) pair for this item.
    Ref<Tuple> pair = 
      buildValue("sO", column_name, self->getColumn(column.getType(), c));
    // Put it in the items tuple.
    result->InitializeItem(c, pair);
  }

  return result.release();
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "get", (PyCFunction) method_get, METH_VARARGS, NULL },
  { "items", (PyCFunction) method_items, METH_VARARGS, NULL },
  { "keys", (PyCFunction) method_keys, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


#if 0
// FIXME: Provide a way to get a row object from a row dict?

PyObject*
get_as_object(PyRow* self,
	      PyObject* /* closure */)
try {
  return self->getRowAsObject();
}
catch (Exception) {
  return NULL;
}

#endif  // #if 0

PyGetSetDef
tp_getset[] = {
#if 0
  { "as_object", (getter) get_as_object, NULL, NULL, NULL },
#endif  // #if 0
  { NULL, NULL, NULL, NULL }
};


}  // anonymous namespace


PyTypeObject
PyRowDict::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "RowDict",                            // tp_name
  sizeof(PyRowDict),                    // tp_size
  0,                                    // tp_itemsize
  NULL,                                 // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  (reprfunc) tp_repr,                   // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  &tp_as_mapping,                       // tp_as_mapping
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
  tp_methods,                           // tp_methods
  NULL,                                 // tp_members
  tp_getset,                            // tp_getset
  &PyRow::type,                         // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) tp_new,                     // tp_new
};

