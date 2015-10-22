//----------------------------------------------------------------------
//
// PyScatter.cc
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <vector>

#include "PyScatter.hh"
#include "python.hh"

using namespace Py;

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

/* Base class for scatter axis classes.

   All details of the scatter implementation specific to the coordinate
   types on the axes are encapsulated in instances of subclasses of this
   base class.  The axis class is responsible for storing values of
   coordinats along the axis, and converting these values to and from
   Python objects. 
*/

class AxisBase
{
public:

  virtual ~AxisBase() {}

  /* Extract a coordinate value from a Python object and store it.  */
  virtual void append(Object*) = 0;

  /* Return the coordinate value at 'index' as a Python object.  */
  virtual PyObject* get(int) const = 0;

  /* Return a Python pair containing the range of coordinates.  */
  virtual Tuple* getRange() const = 0;

};


//----------------------------------------------------------------------

namespace {

/* Templated implementation of a scatter axis.

   The template TYPE is the C++ type used to store coordinate values.
   The Python axis type is assumed to be the cooresponding Python type,
   ala class 'PythonType'.
*/

template<typename TYPE>
class Axis
  : public AxisBase
{
public:

  virtual ~Axis() {}

  virtual void append(Object*);
  virtual PyObject* get(int) const;
  virtual Tuple* getRange() const;

private:

  std::vector<TYPE> coordinates_;

};


template<typename TYPE>
inline void
Axis<TYPE>::append(Object* object)
{
  coordinates_.push_back(PythonType<TYPE>::fromPyObject(object));
}


template<typename TYPE>
inline PyObject*
Axis<TYPE>::get(int index)
  const
{
  return PythonType<TYPE>::asPyObject(coordinates_[index]);
}


template<typename TYPE>
inline Tuple*
Axis<TYPE>::getRange()
  const
{
  TYPE lo = TYPE(0);
  TYPE hi = TYPE(0);
  typename std::vector<TYPE>::const_iterator i = coordinates_.begin();

  // Start with the coordinates of the first point, if there is one.
  if (i != coordinates_.end()) {
    lo = *i;
    hi = lo;
  }
  // Loop over remaining points.
  for (; i != coordinates_.end(); ++i) {
    TYPE value = *i;
    if (value < lo)
      lo = value;
    if (value > hi)
      hi = value;
  }

  // Convert the results to a Python pair.
  Ref<Object> lo_obj = PythonType<TYPE>::asPyObject(lo);
  Ref<Object> hi_obj = PythonType<TYPE>::asPyObject(hi);
  return Tuple::New(2, (Object*) lo_obj, (Object*) hi_obj);
}


//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

/* Return a new unbinned axis object for a Python 'Axis' object.  */

AxisBase*
makeAxis(Object* axis)
{
  Ref<Object> type = axis->GetAttrString("type");
  
  if (type->Compare((PyObject*) &PyFloat_Type))
    return new Axis<double>;
  else if (type->Compare((PyObject*) &PyInt_Type))
    return new Axis<long>;
  else {
    // Don't know how to handle this Python type.
    Ref<String> type_name = type->Str();
    throw Exception(PyExc_NotImplementedError, 
		    "axis type '%s'", type_name->AsString());
  }
}


//----------------------------------------------------------------------
// Python type for list of points
//----------------------------------------------------------------------

/* An extension type to represent the list of points.

   The 'points' member of a scatter object returns an instance of this
   class, which represents a sequence of the points in the scatter
   plot.  Each element of the sequence is an '(x, y)' pair of
   coordinates.  

   This extension type is only instantiated by the 'points' method. 
*/

struct PyPoints 
  : public Py::Object 
{
  PyPoints(PyScatter* scatter) : scatter_(newRef(scatter)) {}
  Ref<PyScatter> scatter_;
};


void
tp_dealloc_points(PyPoints* self)
try {
  // Perform C++ deallocation.
  self->~PyPoints();
  // Deallocate memory.
  self->ob_type->tp_free(self);
}
catch (Exception) {
}


int 
sq_length_points(PyPoints* self)
try {
  return self->scatter_->num_points_;
}
catch (Exception) {
  return -1;
}


PyObject*
sq_item_points(PyPoints* self,
	       int index)
try {
  PyScatter* scatter = self->scatter_;
  int num_points = scatter->num_points_;

  // Handle negative indices.  These denote indexing from the end of the
  // sequence. 
  if (index < 0)
    index = num_points - index;
  // Check the index range.
  if (index < 0 || index >= num_points)
    throw Exception(PyExc_IndexError, "%d", index);

  // Extract the coordinates.
  Ref<Object> x = scatter->x_axis_->get(index);
  Ref<Object> y = scatter->y_axis_->get(index);
  return Tuple::New(2, (Object*) x, (Object*) y);
}
catch (Exception) {
  return NULL;
}


PySequenceMethods
tp_as_sequence_points = {
  (inquiry) sq_length_points,           // sq_length
  (binaryfunc) NULL,                    // sq_concat
  (intargfunc) NULL,                    // sq_repeat
  (intargfunc) sq_item_points,          // sq_item
  (intintargfunc) NULL,                 // sq_slice
  (intobjargproc) NULL,                 // sq_ass_item
  (intintobjargproc) NULL,              // sq_ass_slice
  (objobjproc) NULL,                    // sq_contains
  (binaryfunc) NULL,                    // sq_inplace_concat
  (intargfunc) NULL,                    // sq_inplace_repeat
};


PyTypeObject
type_points = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Points",                             // tp_name
  sizeof(PyPoints),                     // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc_points,       // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  NULL,                                 // tp_repr
  NULL,                                 // tp_as_number
  &tp_as_sequence_points,               // tp_as_sequence
  NULL,                                 // tp_as_mapping
  NULL,                                 // tp_hash
  NULL,                                 // tp_call
  NULL,                                 // tp_str
  NULL,                                 // tp_getattro
  NULL,                                 // tp_setattro
  NULL,                                 // tp_as_buffer
  Py_TPFLAGS_DEFAULT,                   // tp_flags
  NULL,                                 // tp_doc
  NULL,                                 // tp_traverse
  NULL,                                 // tp_clearurn
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
  NULL,                                 // tp_new
  NULL,                                 // tp_free
  NULL,                                 // tp_is_gc,
  NULL,                                 // tp_bases
  NULL,                                 // tp_mro,
  NULL,                                 // tp_cache,
  NULL,                                 // tp_subclasses,
  NULL,                                 // tp_weaklist,
};


}  // anonymous namespace

//----------------------------------------------------------------------
// member functions
//----------------------------------------------------------------------

PyScatter::PyScatter(Object* x_axis,
		     Object* y_axis)
  : num_points_(0),
    x_axis_(makeAxis(x_axis)),
    y_axis_(makeAxis(y_axis)),
    axes_(Tuple::New(2, x_axis, y_axis)),
    dict_(Dict::New())
{
}


PyScatter::~PyScatter()
{
}


void
PyScatter::accumulate(Object* arg)
{
  // Split the pair into objects for the X and Y coordinates.
  Ref<Object> x;
  Ref<Object> y;
  Sequence* coordinates = cast<Sequence>(arg);
  coordinates->split(x, y);
  // Extract and store the coordinates values.
  x_axis_->append(x);
  y_axis_->append(y);
  ++num_points_;
}


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
  Object* x_axis;
  Object* y_axis;
  args->ParseTuple("OO", &x_axis, &y_axis);

  // Create the object.
  return PyScatter::New(x_axis, y_axis, type);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyScatter* self)
try {
  // Perform C++ deallocation.
  self->~PyScatter();
  // Deallocate memory.
  self->ob_type->tp_free(self);
}
catch (Exception) {
}


PyObject*
tp_str(PyScatter* self)
try {
  Ref<Object> x_axis;
  Ref<Object> y_axis;
  self->axes_->split(x_axis, y_axis);
  Ref<String> x_axis_repr = x_axis->Repr();
  Ref<String> y_axis_repr = y_axis->Repr();
  return String::FromFormat
    ("Scatter(%s, %s)", 
     x_axis_repr->AsString(), y_axis_repr->AsString());
}
catch (Exception) {
  return NULL;
}


PyObject*
nb_lshift(Object* arg1,
		     Object* arg2)
try {
  PyScatter* self = cast<PyScatter>(arg1);
  self->accumulate(arg2);
  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyNumberMethods
tp_as_number = {
  NULL,                                 // nb_add
  NULL,                                 // nb_subtract
  NULL,                                 // nb_multiply
  NULL,                                 // nb_divide
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
  NULL,                                 // nb_true_divide
  NULL,                                 // nb_inplace_floor_divide
  NULL,                                 // nb_inplace_true_divide
};


PyObject*
method_accumulate(PyScatter* self,
		  Object* arg)
try {
  self->accumulate(arg);
  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "accumulate", (PyCFunction) method_accumulate, METH_O, NULL },
  { NULL, NULL, 0, NULL }
};


struct PyMemberDef
tp_members[] = {
  { "axes", T_OBJECT, offsetof(PyScatter, axes_), 0, NULL },
  { NULL, 0, 0, 0, NULL }
};


PyObject*
get___dict__(PyScatter* self)
try {
  RETURN_NEW_REF(Object, self->dict_);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_points(PyScatter* self)
try {
  // Set up the Python extension type for the list of points, if this is
  // the first time we're being called.
  static bool first_time = true;
  if (first_time) {
    int result = PyType_Ready(&type_points);
    assert(result == 0);
    first_time = false;
  }

  // Return an object representing the list of points.
  Ref<PyPoints> result = type_points.tp_alloc(&type_points, 0);
  new(result) PyPoints(self);
  return result.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
get_range(PyScatter* self)
try {
  Ref<Tuple> x_range = self->x_axis_->getRange();
  Ref<Tuple> y_range = self->y_axis_->getRange();
  return Tuple::New(2, (Object*) x_range, (Object*) y_range);
}
catch (Exception) {
  return NULL;
}


PyGetSetDef
tp_getset[] = {
  { "__dict__", (getter) get___dict__, NULL, NULL, NULL },
  { "points", (getter) get_points, NULL, NULL, NULL },
  { "range", (getter) get_range, NULL, NULL, NULL },
  { NULL, NULL, NULL, NULL },
};


}  // anonymous namespace

PyTypeObject
PyScatter::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Scatter",                            // tp_name
  sizeof(PyScatter),                    // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  NULL,                                 // tp_repr
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
  tp_methods,                           // tp_methods
  tp_members,                           // tp_members
  tp_getset,                            // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  offsetof(PyScatter, dict_),           // tp_dictoffset
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

