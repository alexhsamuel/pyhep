//----------------------------------------------------------------------
//
// PyFourVector.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cmath>
#include <cstdio>

#include "PyFourVector.hh"
#include "python.hh"

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
  double t, x, y, z;
  args->ParseTuple("dddd", &t, &x, &y, &z);
  // Create the object.
  return PyFourVector::New(t, x, y, z, type);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyFourVector* self)
try {
  // Perform C++ deallocation.
  self->~PyFourVector();
  // Deallocate memory.
  self->ob_type->tp_free(self);
}
catch (Exception) {
}


PyObject*
tp_repr(PyFourVector* self)
try {
  static char buffer[128];
  snprintf(buffer, sizeof(buffer), "lab.FourVector(%f, %f, %f, %f)", 
           self->t_, self->x_, self->y_, self->z_);
  return String::FromString(buffer);
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_str(PyFourVector* self)
try {
  static char buffer[128];
  snprintf(buffer, sizeof(buffer), "(%f, %f, %f, %f) in lab", 
           self->t_, self->x_, self->y_, self->z_);
  return String::FromString(buffer);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_coordinates(PyFourVector* self)
try {
  return Py_BuildValue("(dddd)", self->t_, self->x_, self->y_, self->z_);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_norm(PyFourVector* self)
try {
  double norm_squared = self->getNormSquared();
  if (norm_squared >= 0)
    return Float::FromDouble(sqrt(norm_squared));
  else
    throw Exception(PyExc_ValueError, "math domain error");
}
catch (Exception) {
  return NULL;
}


PyGetSetDef
tp_getset[] = {
  { "coordinates", (getter) get_coordinates, NULL, NULL, NULL },
  { "norm", (getter) get_norm, NULL, NULL, NULL },
  { NULL, NULL, NULL, NULL },
};


PyObject*
nb_add(Object* arg1,
       Object* arg2)
try {
  PyFourVector* self = cast<PyFourVector>(arg1);
  PyFourVector* other = cast<PyFourVector>(arg2);
  return PyFourVector::New(self->t_ + other->t_, self->x_ + other->x_,
                           self->y_ + other->y_, self->z_ + other->z_,
                           self->ob_type);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_subtract(Object* arg1,
            Object* arg2)
try {
  PyFourVector* self = cast<PyFourVector>(arg1);
  PyFourVector* other = cast<PyFourVector>(arg2);
  return PyFourVector::New(self->t_ - other->t_, self->x_ - other->x_,
                           self->y_ - other->y_, self->z_ - other->z_,
                           self->ob_type);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_multiply(Object* arg1,
            Object* arg2)
try {
  if (! PyFourVector::Check(arg1) && PyFourVector::Check(arg2)) 
    std::swap(arg1, arg2);

  PyFourVector* self = cast<PyFourVector>(arg1);
  Ref<Float> as_float = arg2->Float();
  double c = as_float->AsDouble();
  return PyFourVector::New(self->t_ * c, self->x_ * c, 
                           self->y_ * c, self->z_ * c,
                           self->ob_type);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_divide(Object* arg1,
          Object* arg2)
try {
  PyFourVector* self = cast<PyFourVector>(arg1);
  Ref<Float> as_float = arg2->Float();
  double c = as_float->AsDouble();
  return PyFourVector::New(self->t_ / c, self->x_ / c, 
                           self->y_ / c, self->z_ / c,
                           self->ob_type);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_negative(PyFourVector* self)
try {
  return PyFourVector::New
    (-self->t_, -self->x_, -self->y_, -self->z_, self->ob_type);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_absolute(PyFourVector* self)
try {
  return Float::FromDouble(sqrt(self->getNormSquared()));
}
catch (Exception) {
  return NULL;
}


int
nb_nonzero(PyFourVector* self)
try {
  return 
    (self->t_ != 0 || self->x_ != 0 || self->y_ != 0 || self->z_ != 0)
    ? 1 : 0;
}
catch (Exception) {
  abort();
}



PyObject*
nb_xor(Object* arg1,
       Object* arg2)
try {
  PyFourVector* self = cast<PyFourVector>(arg1);
  PyFourVector* other = cast<PyFourVector>(arg2);
  return Float::FromDouble
    (self->t_ * other->t_ - self->x_ * other->x_ - self->y_ 
     * other->y_ - self->z_ * other->z_);
}
catch (Exception) {
  return NULL;
}


PyNumberMethods
tp_as_number = {
  (binaryfunc) nb_add,                  // nb_add
  (binaryfunc) nb_subtract,             // nb_subtract
  (binaryfunc) nb_multiply,             // nb_multiply
  (binaryfunc) nb_divide,               // nb_divide
  NULL,                                 // nb_remainder
  NULL,                                 // nb_divmod
  NULL,                                 // nb_power
  (unaryfunc) nb_negative,              // nb_negative
  NULL,                                 // nb_positive
  (unaryfunc) nb_absolute,              // nb_absolute
  (inquiry) nb_nonzero,                 // nb_nonzero
  NULL,                                 // nb_invert
  NULL,                                 // nb_lshift
  NULL,                                 // nb_rshift
  NULL,                                 // nb_and
  (binaryfunc) nb_xor,                  // nb_xor
  NULL,                                 // nb_or
  NULL,                                 // nb_coerce
  NULL,                                 // nb_int
  NULL,                                 // nb_long
  NULL,                                 // nb_float
  NULL,                                 // nb_oct
  NULL,                                 // nb_hex
  NULL,                                 // nb_inplace_add
  NULL,                                 // nb_inplace_subtract
  NULL,                                 // nb_inplace_multiply
  NULL,                                 // nb_inplace_divide
  NULL,                                 // nb_inplace_remainder
  NULL,                                 // nb_inplace_power
  NULL,                                 // nb_inplace_lshift
  NULL,                                 // nb_inplace_rshift
  NULL,                                 // nb_inplace_and
  NULL,                                 // nb_inplace_xor
  NULL,                                 // nb_inplace_or
  NULL,                                 // nb_floor_divide
  NULL,                                 // nb_true_divide
  NULL,                                 // nb_inplace_floor_divide
  NULL,                                 // nb_inplace_true_divide
};


}  // anonymous namespace


PyTypeObject
PyFourVector::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "FourVector",                         // tp_name
  sizeof(PyFourVector),                 // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  (reprfunc) tp_repr,                   // tp_repr
  &tp_as_number,                        // tp_as_number
  NULL,                                 // tp_as_sequence
  NULL,                                 // tp_as_mapping
  NULL,                                 // tp_hash
  NULL,                                 // tp_call
  (reprfunc) tp_str,                    // tp_str
  NULL,                                 // tp_getattro
  NULL,                                 // tp_setattro
  NULL,                                 // tp_as_buffer
  Py_TPFLAGS_DEFAULT 
  | Py_TPFLAGS_BASETYPE
  | Py_TPFLAGS_CHECKTYPES,              // tp_flags
  NULL,                                 // tp_doc
  NULL,                                 // tp_traverse
  NULL,                                 // tp_clearurn
  NULL,                                 // tp_richcompare
  0,                                    // tp_weaklistoffset
  NULL,                                 // tp_iter
  NULL,                                 // tp_iternext
  NULL,                                 // tp_methods
  NULL,                                 // tp_members
  tp_getset,                            // tp_getset
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

