//----------------------------------------------------------------------
//
// PyRowObject.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <memory>

#include "PyRow.hh"
#include "PyRowDict.hh"
#include "PyRowObject.hh"
#include "PyTable.hh"
#include "python.hh"

using namespace Py;
using namespace table;

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

Ref<String> 
PyRow_dict_attr = String::InternFromString("__dict__");

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyRowObject::PyRowObject(PyTable* table,
			 int index)
  : PyRow(table, index)
{
}


PyRowObject::~PyRowObject()
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
  
  return PyRowObject::New(table, index, type);
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_repr(PyRowObject* self)
try {
  Ref<String> table_repr = self->table_->Repr();
  return String::FromFormat("RowObject(%s, %d)", 
			    table_repr->AsString(), self->index_);
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_str(PyRowDict* self)
try {
  std::string result = "RowObject(";
  const Schema* schema = self->table_->table_->getSchema();
  for (int c = 0; c < schema->getNumColumns(); ++c) {
    const Column& column = schema->getColumn(c);
    if (c > 0)
      result += ", ";
    result += column.getName();
    result += '=';
    Ref<Object> value = self->getColumn(column.getType(), c);
    Ref<String> repr = value->Repr();
    result += repr->AsString();
  }
  result += ')';
  return String::FromString(result.c_str());
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_getattro(PyRowObject* self,
	    String* name)
try {
  // Look up the column.
  Object* result = self->getColumn(name, NULL, NULL);
  // Was it found?
  if (result != NULL)
    return result;

  // Is this a request for the '__dict__' attribute?
  if (PyRow_dict_attr->Compare(name))
    // Yes.  Return a row dictionary for this row.
    return PyRowDict::New(self->table_, self->index_);

  // Fall back to the generic get attribute implementation, to pick up
  // other attributes (as in derived types).
  return PyObject_GenericGetAttr(self, name);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_get(PyRowObject* self,
	   Arg* args)
try {
  String* name;
  Object* default_value = (Object*) Py_None;
  args->ParseTuple("S|O", &name, &default_value);

  Object* result = self->getColumn(name, NULL, NULL);
  if (result != NULL)
    return result;

  result = (Object*) PyObject_GenericGetAttr(self, name);
  if (result != NULL)
    return result;
  else
    PyErr_Clear();
  
  RETURN_NEW_REF(Object, default_value);
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "get", (PyCFunction) method_get, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


}  // anonumous namespace

PyTypeObject
PyRowObject::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "RowObject",                          // tp_name
  sizeof(PyRowObject),                  // tp_size
  0,                                    // tp_itemsize
  NULL,                                 // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  (reprfunc) tp_repr,                   // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  NULL,                                 // tp_as_mapping
  NULL,                                 // tp_hash
  NULL,                                 // tp_call
  (reprfunc) tp_str,                    // tp_str
  (getattrofunc) tp_getattro,           // tp_getattro
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
  NULL,                                 // tp_getset
  &PyRow::type,                         // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) tp_new,                     // tp_new
};


