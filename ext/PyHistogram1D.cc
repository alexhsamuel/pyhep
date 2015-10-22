//----------------------------------------------------------------------
//
// PyHistogram1D.cc
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Extension classes for one-dimensional histograms.

   This module provides Python extension classes for one-dimensional
   histograms.  Different axis types are supported via the polymorphic
   'BinnedAxis' class.  Different types for bin contents are supported
   via the polymorphic 'HistogramBins' class.

   Use the function 'Histogram1D' to create an instance of the
   appropriate extension type, given the axis and bin types.  If no
   extension type is available, this raises 'NotImplementedError'.
*/

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <cassert>
#include <cmath>
#include <memory>
#include <vector>

#include "python.hh"
#include "PyHist.hh"
#include "PyHistogram1D.hh"

using namespace Py;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

/* Unwrap an argument that may be either a value or a one-element sequence.

   A histogram object generally accepts a sequence of values for
   coordinates or bin numbers; the number of elements in the sequence
   must be equal to the number of dimensions of the histogram.
   One-dimensional histograms also accept a bare value (not the element
   of a sequence) as a convenience.  This function is used for
   implementing that. 

   'arg' is a bin number or coordinate argument value, which may be
   either a numerical value or a one-element sequence containing the
   numerical value.  Unpack the sequence, if necessary, and return a new
   reference to the value.  If the sequence doesn't contain a single
   element, raise 'ValueError' using 'arg_name' to describe the
   argument.
*/

inline Object*
unwrap1D(Object* arg,
	 const char* arg_name)
{
  if (Tuple::Check(arg) || List::Check(arg)) {
    Sequence* seq = cast<Sequence>(arg);
    if (seq->Size() == 1) 
      return seq->GetItem(0);
    else
      throw Exception(PyExc_ValueError, 
		      "%s must be a single value", arg_name);
  }
  else
    return newRef(arg);
}


/* Acccumulate 'coordinate' into 'histogram' with 'weight'.

   If 'weight' is NULL, unit weight is used.  
*/

inline void
accumulate(PyHistogram1D* histogram,
	   Object* coordinate,
	   Object* weight)
{
  // Is 'coordinate' 'None'?  If so, skip the accumulation.
  if (coordinate == Py_None)
    return;

  // Find the index of the bin into which to accumulate.
  unsigned index = 
    histogram->mapNumber(histogram->mapCoordinate(coordinate));
  // Accumulate.
  histogram->bins_->accumulate(index, weight);
  ++histogram->number_of_samples_;
}


}  // anonymous namespace

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyHistogram1D::PyHistogram1D(Object* axis,
			     Object* bin_type,
			     ErrorModel error_model)
  : // Store the Python axis object.
    axis_obj_(newRef(axis)),
    // Construct an axis object to handle Python coordinate objects.
    axis_(makeBinnedAxis(axis)),
    // Store the bin type.
    bin_type_(newRef(bin_type)),
    // Zero the number of entries.
    number_of_samples_(0),
    // Create a dictionary for additional attributes.
    dict_(Dict::New())
{
  // Construct a bins object to store bin values and handle Python value
  // objects.
  int number_of_bins = axis_->number_of_bins_ + 2;
  bins_.reset(makeHistogramBins(bin_type, number_of_bins, error_model));

  // Also store the axis in a sequence, for access with the 'axes' member.
  axes_ = Tuple::New(1, axis);
}


PyHistogram1D::~PyHistogram1D()
{
}


inline unsigned
PyHistogram1D::mapNumber(BinNumber bin_number)
{
  const int num_bins = axis_->number_of_bins_;
  if (bin_number == BINNUMBER_UNDERFLOW)
    return 0;
  else if (bin_number == BINNUMBER_OVERFLOW)
    return num_bins + 1;
  else if (bin_number >= 0 && bin_number < num_bins)
    return bin_number + 1;
  else 
    throw Exception(PyExc_IndexError, 
		    "invalid bin number %d", bin_number);
}


inline BinNumber
PyHistogram1D::mapCoordinate(Object* coordinate)
{
  Ref<Object> coordinate_obj = unwrap1D(coordinate, "coordinate");
  return axis_->map(coordinate_obj);
}


inline BinNumber
PyHistogram1D::parseBinNumber(Object* arg)
{
  Ref<Object> bin_number_obj = unwrap1D(arg, "bin_number");
  return axis_->parseBinNumber(bin_number_obj);
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
  Object* axis;
  Object* bin_type;
  const char* error_model_name;
  args->ParseTuple("(O)Os", &axis, &bin_type, &error_model_name);
  ErrorModel error_model = errorModelFromString(error_model_name);
  if (error_model == ERROR_MODEL_INVALID)
    throw Exception(PyExc_ValueError, "unknown error model '%s'", 
		    error_model_name);

  // Create the object.
  return PyHistogram1D::New(axis, bin_type, error_model);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyHistogram1D* self)
try {
  // Perform C++ destruction.
  self->~PyHistogram1D();
  // Free memory for the object.
  self->ob_type->tp_free(self);
}
catch (Exception) {
}


PyObject*
tp_repr(PyHistogram1D* self)
try {
  Ref<String> axis_repr = self->axis_obj_->Repr();
  Type* bin_type = cast<Type>(self->bin_type_);
  return String::FromFormat
    ("Histogram(%s, bin_type=%s, error_model='%s')", 
     axis_repr->AsString(), bin_type->GetName(),
     errorModelAsString(self->bins_->getErrorModel()));
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
  PyHistogram1D* histogram;
  Object* scale;
  if (PyHistogram1D::Check(arg1)) {
    histogram = (PyHistogram1D*) arg1;
    scale = arg2;
  }
  else if (PyHistogram1D::Check(arg2)) {
    histogram = (PyHistogram1D*) arg2;
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
nb_lshift(PyHistogram1D* self,
	  Object* other)
try {
  accumulate(self, other, NULL);
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
method_accumulate(PyHistogram1D* self,
		  Arg* args)
try {
  // Parse arguments.
  Object* coordinate;
  Object* weight = NULL;
  args->ParseTuple("O|O", &coordinate, &weight);

  accumulate(self, coordinate, weight);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_getBinContent(PyHistogram1D* self,
		     Object* bin_number)
try {
  unsigned index = self->mapNumber(self->parseBinNumber(bin_number));
  return self->bins_->getBinContent(index);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_getBinRange(PyHistogram1D* self,
		   Object* bin_number_arg)
try {
  BinNumber bin_number = self->parseBinNumber(bin_number_arg);
  // Construct the range.
  Ref<Object> range = self->axis_->getBinRange(bin_number);
  // Wrap the range in a one-element tuple.
  return Tuple::New(1, range);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_getBinError(PyHistogram1D* self,
		   Object* bin_number)
try {
  unsigned index = self->mapNumber(self->parseBinNumber(bin_number));
  return self->bins_->getBinError(index);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_map(PyHistogram1D* self,
	   Object* coordinate)
try {
  // Find the bin number cooresponding to 'coordinate'.
  BinNumber bin_number = self->mapCoordinate(coordinate);
  if (bin_number == BINNUMBER_NONE)
    throw Exception(PyExc_ValueError, "invalid 'None' coordinate");
  // Construct the bin number object.
  Ref<Object> bin_number_obj = makeBinNumberObject(bin_number);
  // Wrap it in a one-element tuple.
  return Tuple::New(1, bin_number_obj);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_setBinContent(PyHistogram1D* self,
		     Arg* args)
try {
  // Parse arguments.
  Object* bin_number;
  Object* value;
  args->ParseTuple("OO", &bin_number, &value);
  unsigned index = self->mapNumber(self->parseBinNumber(bin_number));

  self->bins_->setBinContent(index, value);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_setBinError(PyHistogram1D* self,
		   Arg* args)
try {
  // Parse arguments.
  Object* bin_number;
  Object* value;
  args->ParseTuple("OO", &bin_number, &value);
  unsigned index = self->mapNumber(self->parseBinNumber(bin_number));

  self->bins_->setBinError(index, value);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


/* FIXME: Write this function.  */
#if 0
PyObject*
method_update(PyHistogram1D* self,
	      Arg* args)
try {
  // Parse arguments.
  Object* histogram;
  double scale = 1;
  args->ParseTuple("O|d", &histogram, &scale);
  
  

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}
#endif


char* 
doc_setBinContent =
"Set the weight contained in a bin."
""
"'bin_numbers' -- A sequence of bin numbers for the axes of the"
"histogram.";

PyMethodDef
tp_methods[] = {
  { "accumulate", (PyCFunction) method_accumulate, METH_VARARGS, NULL },
  { "getBinContent", (PyCFunction) method_getBinContent, METH_O, NULL },
  { "getBinError", (PyCFunction) method_getBinError, METH_O, NULL },
  { "getBinRange", (PyCFunction) method_getBinRange, METH_O, NULL },
  { "map", (PyCFunction) method_map, METH_O, NULL },
  { "setBinContent", (PyCFunction) method_setBinContent, METH_VARARGS, doc_setBinContent },
  { "setBinError", (PyCFunction) method_setBinError, METH_VARARGS, NULL },
#if 0
  { "update", (PyCFunction) method_update, METH_VARARGS, NULL }
#endif
  { NULL, NULL, 0, NULL }
};


struct PyMemberDef
tp_members[] = {
  { "axis", T_OBJECT, offsetof(PyHistogram1D, axis_obj_), 0, NULL },
  { "axes", T_OBJECT, offsetof(PyHistogram1D, axes_), 0, NULL },
  { "bin_type", T_OBJECT, offsetof(PyHistogram1D, bin_type_), 0, NULL },
  { "number_of_samples", T_INT, 
    offsetof(PyHistogram1D, number_of_samples_), 0, NULL },
  { NULL, 0, 0, 0, NULL }
};


PyObject*
get___dict__(PyHistogram1D* self)
try {
  RETURN_NEW_REF(Object, self->dict_);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_dimensions(PyHistogram1D* self)
try {
  // This is a one-dimensional histogram.
  return Int::FromLong(1);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_error_model(PyHistogram1D* self)
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
PyHistogram1D::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Histogram1D",                        // tp_name
  sizeof(PyHistogram1D),                // tp_size
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
  NULL,                                 // tp_clear
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
  offsetof(PyHistogram1D, dict_),       // tp_dictoffset
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


