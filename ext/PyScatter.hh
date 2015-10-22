//----------------------------------------------------------------------
//
// PyScatter.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Extension class for storing scatter-plot data.

   This module provides a Python extension class to store
   two-dimensional scatter plots.
*/

#ifndef __PYSCATTER_HH__
#define __PYSCATTER_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <memory>
#include <vector>

#include "python.hh"
#include "PyHist.hh"

//----------------------------------------------------------------------
// forward declarations
//----------------------------------------------------------------------

class AxisBase;

//----------------------------------------------------------------------
// Python type
//----------------------------------------------------------------------

struct PyScatter
  : public Py::Object
{
  // Python stuff ------------------------------------------------------

  static PyTypeObject type;
  static PyScatter* New(Py::Object*, Py::Object*, PyTypeObject* type=&type);
  static bool Check(PyObject* object);

  // Methods  ----------------------------------------------------------

  PyScatter(Py::Object* x_axis, Py::Object* y_axis);
  ~PyScatter();

  /* Extract x and y from the two-element sequence 'arg' and accumulate.  */
  void accumulate(Py::Object* arg);
  
  // Data  -------------------------------------------------------------

  /* Number of points in the sampling.  */
  int num_points_;

  /* C++ objects for the axes; these also store the coordinate values.  */
  std::auto_ptr<AxisBase> x_axis_;
  std::auto_ptr<AxisBase> y_axis_;

  /* A sequence of the two Python axis objects describing the axes.  */
  Py::Ref<Py::Tuple> axes_;

  /* Dictionary for user-defined attributes.  */
  Py::Ref<Py::Dict> dict_;

};


//----------------------------------------------------------------------
// inline method definitions
//----------------------------------------------------------------------

inline PyScatter*
PyScatter::New(Py::Object* x_axis,
	       Py::Object* y_axis,
	       PyTypeObject* type)
{
  // Construct the Python object.
  Py::Ref<Py::Object> result = type->tp_alloc(type, 0);
  // Perform C++ initialization.
  new(result) PyScatter(x_axis, y_axis);
  // All done.
  return (PyScatter*) result.release();
}


inline bool
PyScatter::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYSCATTER_HH__
