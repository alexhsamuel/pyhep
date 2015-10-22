//----------------------------------------------------------------------
//
// PyFourVector.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

#ifndef __PYFOURVECTOR_HH__
#define __PYFOURVECTOR_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>

#include "python.hh"

//----------------------------------------------------------------------
// Python type
//----------------------------------------------------------------------

struct PyFourVector
  : public Py::Object
{
  // The type used to store component values.
  typedef double component_t;

  static PyTypeObject type;
  static PyFourVector* New(component_t t, component_t x, 
			   component_t y, component_t z, 
			   PyTypeObject* type=&type);
  static bool Check(PyObject* object);

  PyFourVector(component_t t, component_t x, 
	       component_t y, component_t z);
  ~PyFourVector();

  component_t getNormSquared() const;

  const component_t t_;
  const component_t x_;
  const component_t y_;
  const component_t z_;

};


inline PyFourVector*
PyFourVector::New(component_t t,
		  component_t x,
		  component_t y,
		  component_t z,
		  PyTypeObject* type)
{
  // Construct the Python object.
  Py::Ref<Py::Object> result = type->tp_alloc(type, 0);
  // Perform C++ initialization.
  new(result) PyFourVector(t, x, y, z);
  // All done.
  return (PyFourVector*) result.release();
}


inline bool
PyFourVector::Check(PyObject* object)
{
  return ((Object*) object)->IsInstance(&type);
}


inline
PyFourVector::PyFourVector(component_t t,
			   component_t x,
			   component_t y,
			   component_t z)
  : t_(t),
    x_(x),
    y_(y),
    z_(z)
{
}


inline
PyFourVector::~PyFourVector()
{
}


inline PyFourVector::component_t
PyFourVector::getNormSquared()
  const
{
  return t_ * t_ - x_ * x_ - y_ * y_ - z_ * z_;
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYFOURVECTOR_HH__
