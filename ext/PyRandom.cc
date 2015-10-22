//----------------------------------------------------------------------
//
// PyRandom.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>
#include <algorithm>

#include "PyRandom.hh"
#include "python.hh"
#include "random.hh"

using namespace Py;

//----------------------------------------------------------------------
// Python type
//----------------------------------------------------------------------

namespace {

PyObject*
tp_new(PyTypeObject* type,
       Arg* args,
       Dict* kw_args)
try {
  // Parse arguments.
  long seed;
  if (args->Size() == 0)
    // No argument; generate seed automatically.
    seed = 0;
  else {
    args->ParseTuple("|i", &seed);
    if (seed <= 0)
      throw Exception(PyExc_ValueError, "seed must be positive");
  }

  // Create the object.
  return PyShuffledLEcuyerRandom::New(seed);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyShuffledLEcuyerRandom* self)
try {
  // Perform C++ deallocation.
  self->~PyShuffledLEcuyerRandom();
  // Free memory for the Python object.
  self->ob_type->tp_free(self);
}
catch (Exception) {
}


PyObject*
tp_repr(PyShuffledLEcuyerRandom* self)
try {
  return String::FromFormat
    ("<ShuffledLEcuyerRandom at %p>", (void*) self);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_random(PyShuffledLEcuyerRandom* self,
	      Arg* args)
try {
  args->ParseTuple("");

  return Float::FromDouble(self->random_.random());
}
catch (Exception) {
  return NULL;
}


PyObject*
method_seed(PyShuffledLEcuyerRandom* self,
	    Arg* args)
try {
  // Parse arguments.
  long seed;
  if (args->Size() == 0)
    // No argument; generate seed automatically.
    seed = 0;
  else {
    args->ParseTuple("|i", &seed);
    if (seed <= 0)
      throw Exception(PyExc_ValueError, "seed must be positive");
  }

  self->random_.initialize(seed);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "random", (PyCFunction) method_random, METH_VARARGS, NULL },
  { "seed", (PyCFunction) method_seed, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


}  // anonymous namespace

PyTypeObject
PyShuffledLEcuyerRandom::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "ShuffledLEcuyerRandom",              // tp_name
  sizeof(PyShuffledLEcuyerRandom),      // tp_size
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
  NULL,                                 // tp_call
  (reprfunc) tp_repr,                   // tp_str
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
  NULL,                                 // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) tp_new,                     // tp_new
  NULL,                                 // tp_free
  NULL,                                 // tp_is_gc,
  NULL,                                 // tp_bases
  NULL,                                 // tp_mro,
  NULL,                                 // tp_cache,
  NULL,                                 // tp_subclasses,
  NULL,                                 // tp_weaklist,
};


