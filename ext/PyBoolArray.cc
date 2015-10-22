//----------------------------------------------------------------------
//
// PyBoolArray.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <cstring>
#include <string>

#include "PyBoolArray.hh"
#include "python.hh"

using namespace Py;

//----------------------------------------------------------------------
// forward declarations
//----------------------------------------------------------------------

namespace {
  PyObject* function_unpickle(PyObject* self, Arg* args);
}

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyBoolArray::PyBoolArray(int length)
  : length_(length)
{
  // Compute the number of unsigned chars required to store this many
  // bits.  
  assert(sizeof(unsigned char) == 1);
  int num_bytes = getAllocation();
  // Allocate room.
  bits_ = new unsigned char[num_bytes];
  // Zero the bits.
  clear();
}


PyBoolArray::~PyBoolArray()
{
  assert(bits_ != NULL);
  delete [] bits_;
}


void
PyBoolArray::Register(Module* module)
{
  // Construct a function object for the unpickling function.
  static PyMethodDef unpickle_def = {
    "unpickle", (PyCFunction) &function_unpickle, METH_VARARGS, NULL
  };
  Ref<Object> unpickle_function = newCFunction(&unpickle_def, NULL);
  // Add the unpickling function to the module.
  Ref<Dict> module_dict = module->GetDict();
  module_dict->SetItemString(unpickle_def.ml_name, unpickle_function);
  // Register it with 'copy_reg' as an unpickling-safe constructor.
  Ref<Object> constructor = import("copy_reg", "constructor");
  Ref<Object> result = cast<Callable>(constructor)->CallFunctionObjArgs
    ((PyObject*) unpickle_function, NULL);
  // Store it for later use.
  unpickle_function_ = unpickle_function;
}


Ref<Object>
PyBoolArray::unpickle_function_;


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
  int length;
  args->ParseTuple("i", &length);

  return PyBoolArray::New(length);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyBoolArray* self)
try {
  // Perform C++ deallocation.
  self->~PyBoolArray();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
}


PyObject*
tp_str(PyBoolArray* self)
try {
  return String::FromFormat("BoolArray(%d, ...)", self->length_);
}
catch (Exception) {
  return NULL;
}


PyObject*
method___reduce__(PyBoolArray* self)
try {
  // Construct the arguments to the unpickling function that will be
  // used when unpickling this instance.  The tuple contains the length
  // of the array and a bit-encoded string of array elements.
  Ref<Tuple> result = 
    buildValue("O(is#)", 
	       (PyObject*) PyBoolArray::unpickle_function_, 
	       self->length_, 
	       (const char*) self->bits_, self->getAllocation()); 
  // That's it.
  return result.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
method_buffer_info(PyBoolArray* self)
try {
  return Py_BuildValue("(ll)", (long) self->bits_, self->length_);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_clear(PyBoolArray* self)
try {
  self->clear();
  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "__reduce__", (PyCFunction) method___reduce__, METH_NOARGS, NULL },
  { "buffer_info", (PyCFunction) method_buffer_info, METH_NOARGS, NULL },
  { "clear", (PyCFunction) method_clear, METH_NOARGS, NULL },
  { NULL, NULL, 0, NULL }
};


int 
sq_length(PyBoolArray* self)
try {
  return self->length_;
}
catch (Exception) {
  return -1;
}


PyObject*
sq_item(PyBoolArray* self,
	int index)
try {
  self->checkIndex(index);

  if (self->get(index))
    RETURN_TRUE;
  else
    RETURN_FALSE;
}
catch (Exception) {
  return NULL;
}


int
sq_ass_item(PyBoolArray* self,
	    int index,
	    Object* value)
try {
  self->checkIndex(index);

  self->set(index, value->IsTrue());
  return 0;
}
catch (Exception) {
  return -1;
}


PySequenceMethods
tp_as_sequence = {
  (inquiry) sq_length,                  // sq_length
  (binaryfunc) NULL,                    // sq_concat
  (intargfunc) NULL,                    // sq_repeat
  (intargfunc) sq_item,                 // sq_item
  (intintargfunc) NULL,                 // sq_slice
  (intobjargproc) sq_ass_item,          // sq_ass_item
  (intintobjargproc) NULL,              // sq_ass_slice
  (objobjproc) NULL,                    // sq_contains
  (binaryfunc) NULL,                    // sq_inplace_concat
  (intargfunc) NULL,                    // sq_inplace_repeat
};


PyObject*
function_unpickle(PyObject* self,
		  Arg* args)
try {
  // The pickle state contains the length of the array, and a
  // bit-encoded string containing the elements of the array.
  int length;
  const char* bits;
  int bits_length;
  args->ParseTuple("is#", &length, &bits, &bits_length);

  // Construct the array.
  Ref<PyBoolArray> result = PyBoolArray::New(length);
  // Make sure the state string is of the right length.
  if ((int) result->getAllocation() != bits_length)
    throw Exception(PyExc_ValueError, 
		    "bit string must be of length %d", 
		    result->getAllocation());
  // Blit in the state.
  memcpy((char*) result->bits_, bits, bits_length);

  return result.release();
}
catch (Exception) {
  return NULL;
}


}  // anonymous namespace


PyTypeObject
PyBoolArray::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "BoolArray",                          // tp_name
  sizeof(PyBoolArray),                  // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  (reprfunc) tp_str,                    // tp_repr
  NULL,                                 // tp_as_number
  &tp_as_sequence,                      // tp_as_sequence
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
  NULL,                                 // tp_clearurn
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
};


