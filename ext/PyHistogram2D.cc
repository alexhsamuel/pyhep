//----------------------------------------------------------------------
//
// PyHistogram2D.cc
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Extension classes for two-dimensional histogams.

   This module provides a templated Python extension class for
   two-dimensional histograms.  Different axis types are supported via
   the polymorphic 'BinnedAxis' class.  Different types for bin contents
   are supported via the polymorphic 'HistogramBins' class.
*/

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <cassert>
#include <memory>

#include "python.hh"
#include "PyHist.hh"
#include "PyHistogram2D.hh"

using namespace Py;

//----------------------------------------------------------------------
// Method definitions
//----------------------------------------------------------------------

PyHistogram2D::PyHistogram2D(Object* x_axis,
			     Object* y_axis,
			     Object* bin_type,
			     ErrorModel error_model)
  : // Store the axes in a tuple, ready for member access.
    axes_(Tuple::New(2, x_axis, y_axis)),
    // Construct axis objects to handle Python coordinates.
    x_axis_(makeBinnedAxis(x_axis)),
    y_axis_(makeBinnedAxis(y_axis)),
    // Store the bin type.
    bin_type_(newRef(bin_type)),
    // Zero the number of entries.
    number_of_samples_(0),
    // Create a dictionary for additional attributes.
    dict_(Dict::New())
{
  
  // Allocate space for bins.
  int num_bins = 
    (x_axis_->number_of_bins_ + 2) * (y_axis_->number_of_bins_ + 2);
  bins_.reset(makeHistogramBins(bin_type, num_bins, error_model));
}


PyHistogram2D::~PyHistogram2D()
{
}


inline unsigned
PyHistogram2D::mapNumbers(BinNumbers bin_numbers)
{
  int x;
  const int num_x_bins = x_axis_->number_of_bins_;
  if (bin_numbers.x_ == BINNUMBER_UNDERFLOW)
    x = 0;
  else if (bin_numbers.x_ == BINNUMBER_OVERFLOW)
    x = num_x_bins + 1;
  else if (bin_numbers.x_ >= 0 && bin_numbers.x_ < num_x_bins)
    x = bin_numbers.x_ + 1;
  else 
    throw Exception(PyExc_IndexError, 
		    "invalid X bin number %d", bin_numbers.x_);

  int y;
  const int num_y_bins = y_axis_->number_of_bins_;
  if (bin_numbers.y_ == BINNUMBER_UNDERFLOW)
    y = 0;
  else if (bin_numbers.y_ == BINNUMBER_OVERFLOW)
    y = num_y_bins + 1;
  else if (bin_numbers.y_ >= 0 && bin_numbers.y_ < num_y_bins)
    y = bin_numbers.y_ + 1;
  else 
    throw Exception(PyExc_IndexError, 
		    "invalid Y bin number %d", bin_numbers.y_);

  return (unsigned) (y * (num_x_bins + 2) + x);
}


inline PyHistogram2D::BinNumbers
PyHistogram2D::mapCoordinates(Object* arg)
{
  Ref<Object> x_arg;
  Ref<Object> y_arg;
  Sequence* coordinates = cast<Sequence>(arg);
  coordinates->split(x_arg, y_arg);
  // Get the individual bin numbers from the axes.
  BinNumber x = x_axis_->map(x_arg);
  BinNumber y = y_axis_->map(y_arg);

  return BinNumbers(x, y);
}


inline PyHistogram2D::BinNumbers 
PyHistogram2D::parseBinNumbers(Object* arg)
{
  Ref<Object> x_arg;
  Ref<Object> y_arg;
  Sequence* bin_numbers = cast<Sequence>(arg);
  bin_numbers->split(x_arg, y_arg);
  // Get the individual bin numbers from the axes.
  BinNumber x = x_axis_->parseBinNumber(x_arg);
  BinNumber y = y_axis_->parseBinNumber(y_arg);
  return BinNumbers(x, y);
}


//----------------------------------------------------------------------
// Python type support
//----------------------------------------------------------------------

namespace {

PyObject*
tp_new(PyTypeObject* type,
       Arg* args,
       Dict* kw_args)
try {
  // Parse arguments.
  Object* x_axis;
  Object* y_axis;
  Object* bin_type;
  const char* error_model_name;
  args->ParseTuple("(OO)Os", &x_axis, &y_axis, &bin_type, 
		   &error_model_name);
  ErrorModel error_model = errorModelFromString(error_model_name);
  if (error_model == ERROR_MODEL_INVALID)
    throw Exception(PyExc_ValueError, "unknown error model '%s'", 
		    error_model_name);

  // Create the object.
  return PyHistogram2D::New(x_axis, y_axis, bin_type, error_model);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyHistogram2D* self)
try {
  // Perform C++ deallocation.
  self->~PyHistogram2D();
  // Deallocate memory.
  self->ob_type->tp_free(self);
}
catch (Exception) {
}


PyObject*
tp_repr(PyHistogram2D* self)
try {
  Ref<Object> x_axis = self->axes_->GetItem(0);
  Ref<String> x_axis_repr = x_axis->Repr();
  Ref<Object> y_axis = self->axes_->GetItem(1);
  Ref<String> y_axis_repr = y_axis->Repr();
  Type* bin_type = cast<Type>(self->bin_type_);
  return String::FromFormat
    ("Histogram(%s, %s, bin_type=%s, error_model='%s')",
     x_axis_repr->AsString(), y_axis_repr->AsString(),
     bin_type->GetName(), errorModelAsString(self->bins_->getErrorModel()));
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_add(Object* arg1,
       Object* arg2)
try {
  Ref<Object> add_obj = import("hep.hist.util", "add");
  Callable* add = cast<Callable>(add_obj);
  return add->CallFunctionObjArgs(arg1, arg2, NULL);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_subtract(Object* arg1,
	    Object* arg2)
try {
  Ref<Object> add_obj = import("hep.hist.util", "add");
  Callable* add = cast<Callable>(add_obj);
  Ref<Int> negative = Int::FromLong(-1);
  return add->CallFunctionObjArgs(arg1, arg2, (Int*) negative, NULL);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_multiply(Object* arg1,
	    Object* arg2)
try {
  PyHistogram2D* histogram;
  Object* scale;
  if (PyHistogram2D::Check(arg1)) {
    histogram = (PyHistogram2D*) arg1;
    scale = arg2;
  }
  else if (PyHistogram2D::Check(arg2)) {
    histogram = (PyHistogram2D*) arg2;
    scale = arg1;
  }
  else
    // Should not occur.
    abort();

  Ref<Object> scale_obj = import("hep.hist.util", "scale");
  Callable* scale_fn = cast<Callable>(scale_obj);
  return scale_fn->CallFunctionObjArgs(histogram, scale, NULL);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_divide(Object* arg1,
	  Object* arg2)
try {
  Ref<Object> add_obj = import("hep.hist.util", "divide");
  Callable* add = cast<Callable>(add_obj);
  return add->CallFunctionObjArgs(arg1, arg2, NULL);
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_lshift(PyHistogram2D* self,
	  Object* other)
try {
  // Find the index of the bin into which to accumulate.
  unsigned index = self->mapNumbers(self->mapCoordinates(other));
  // Accumulate.
  self->bins_->accumulate(index, NULL);
  ++self->number_of_samples_;

  RETURN_NONE;
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
  NULL,                                 // nb_negative
  NULL,                                 // nb_positive
  NULL,                                 // nb_absolute
  NULL,                                 // nb_nonzero
  NULL,                                 // nb_invert
  (binaryfunc) nb_lshift,               // nb_lshift
  NULL,                                 // nb_rshift
  NULL,                                 // nb_and
  NULL,                                 // nb_xor
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
  (binaryfunc) nb_divide,               // nb_true_divide
  NULL,                                 // nb_inplace_floor_divide
  NULL,                                 // nb_inplace_true_divide
};


PyObject*
method_accumulate(PyHistogram2D* self,
		  Arg* args)
try {
  // Extract arguments.
  Object* coordinates;
  Object* weight = NULL;
  args->ParseTuple("O|O", &coordinates, &weight);

  // Find the index of the bin into which to accumulate.
  unsigned index = self->mapNumbers(self->mapCoordinates(coordinates));
  // Accumulate.
  self->bins_->accumulate(index, weight);
  ++self->number_of_samples_;

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_getBinContent(PyHistogram2D* self,
		     Object* bin_numbers_arg)
try {
  unsigned index = 
    self->mapNumbers(self->parseBinNumbers(bin_numbers_arg));
  return self->bins_->getBinContent(index);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_getBinRange(PyHistogram2D* self,
		   Object* bin_numbers_arg)
try {
  PyHistogram2D::BinNumbers bin_numbers = 
    self->parseBinNumbers(bin_numbers_arg);
  // Construct the ranges along the two axes.
  Ref<Object> x_range = self->x_axis_->getBinRange(bin_numbers.x_);
  Ref<Object> y_range = self->y_axis_->getBinRange(bin_numbers.y_);
  // Wrap them in a tuple.
  return Tuple::New(2, (Object*) x_range, (Object*) y_range);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_getBinError(PyHistogram2D* self,
		   Object* bin_numbers)
try {
  unsigned index = self->mapNumbers(self->parseBinNumbers(bin_numbers));
  return self->bins_->getBinError(index);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_map(PyHistogram2D* self,
	   Object* coordinates)
try {
  PyHistogram2D::BinNumbers bin_numbers = 
    self->mapCoordinates(coordinates);
  if (bin_numbers.x_ == BINNUMBER_NONE 
      || bin_numbers.y_ == BINNUMBER_NONE)
    throw Exception(PyExc_ValueError, "invalid 'None' coordinate");
  
  Ref<Object> x_bin_number = makeBinNumberObject(bin_numbers.x_);
  Ref<Object> y_bin_number = makeBinNumberObject(bin_numbers.y_);
  return Tuple::New(2, (Object*) x_bin_number, (Object*) y_bin_number);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_setBinContent(PyHistogram2D* self,
		     Arg* args)
try {
  Object* bin_numbers;
  Object* value;
  args->ParseTuple("OO", &bin_numbers, &value);
  unsigned index = self->mapNumbers(self->parseBinNumbers(bin_numbers));

  self->bins_->setBinContent(index, value);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_setBinError(PyHistogram2D* self,
		   Arg* args)
try {
  Object* bin_numbers;
  Object* value;
  args->ParseTuple("OO", &bin_numbers, &value);
  unsigned index = self->mapNumbers(self->parseBinNumbers(bin_numbers));

  self->bins_->setBinError(index, value);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "accumulate", (PyCFunction) method_accumulate, METH_VARARGS, NULL },
  { "getBinContent", (PyCFunction) method_getBinContent, METH_O, NULL },
  { "getBinError", (PyCFunction) method_getBinError, METH_O, NULL },
  { "getBinRange", (PyCFunction) method_getBinRange, METH_O, NULL },
  { "map", (PyCFunction) method_map, METH_O, NULL },
  { "setBinContent", (PyCFunction) method_setBinContent, METH_VARARGS, NULL },
  { "setBinError", (PyCFunction) method_setBinError, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


struct PyMemberDef
tp_members[] = {
  { "axes", T_OBJECT, offsetof(PyHistogram2D, axes_), 0, NULL },
  { "bin_type", T_OBJECT, offsetof(PyHistogram2D, bin_type_), 0, NULL },
  { "number_of_samples", T_INT, 
    offsetof(PyHistogram2D, number_of_samples_), 0, NULL },
  { NULL, 0, 0, 0, NULL }
};


PyObject*
get___dict__(PyHistogram2D* self)
try {
  RETURN_NEW_REF(Object, self->dict_);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_dimensions(PyHistogram2D* self)
try {
  // It's always two-dimensional.
  return Int::FromLong(2);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_error_model(PyHistogram2D* self)
try {
  return String::FromString
    (errorModelAsString(self->bins_->getErrorModel()));
}
catch (Exception) {
  return NULL;
}


PyGetSetDef
tp_getset[] = {
  { "__dict__", (getter) get___dict__, NULL, NULL, NULL },
  { "dimensions", (getter) get_dimensions, NULL, NULL, NULL },
  { "error_model", (getter) get_error_model, NULL, NULL, NULL },
  { NULL, NULL, NULL, NULL },
};


}  // anonymous namespace


PyTypeObject
PyHistogram2D::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Histogram2D",                        // tp_name
  sizeof(PyHistogram2D),                // tp_size
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
  (reprfunc) tp_repr,                   // tp_str
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
  tp_methods,                           // tp_methods
  tp_members,                           // tp_members
  tp_getset,                            // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  offsetof(PyHistogram2D, dict_),       // tp_dictoffset
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


