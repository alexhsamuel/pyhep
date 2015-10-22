//----------------------------------------------------------------------
//
// PyRandom.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python extension class for flat data tables.  */

#ifndef __PYRANDOM_HH__
#define __PYRANDOM_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>

#include "python.hh"
#include "random.hh"

//----------------------------------------------------------------------
// class definitions
//----------------------------------------------------------------------

struct PyShuffledLEcuyerRandom
  : public Py::Object
{
  static PyTypeObject type;
  static PyShuffledLEcuyerRandom* New(long seed=0, PyTypeObject* type=&type);
  static bool Check(PyObject* object);

  PyShuffledLEcuyerRandom(long seed=0);
  ~PyShuffledLEcuyerRandom();

  // The underlying random number generator.
  ShuffledLEcuyerRandom random_;

};


//----------------------------------------------------------------------
// inline methods
//----------------------------------------------------------------------

inline 
PyShuffledLEcuyerRandom*
PyShuffledLEcuyerRandom::New(long seed,
			     PyTypeObject* type)
{
  // Construct the Python object.
  Py::Ref<Py::Object> result = type->tp_alloc(type, 0);
  // Preform C++ initialization.
  new(result) PyShuffledLEcuyerRandom(seed);
  // All done.
  return (PyShuffledLEcuyerRandom*) result.release();
}


inline bool
PyShuffledLEcuyerRandom::Check(PyObject* object)
{
  return ((Object*) object)->IsInstance(&type);
}


inline
PyShuffledLEcuyerRandom::PyShuffledLEcuyerRandom(long seed)
  : random_(seed)
{
}


inline
PyShuffledLEcuyerRandom::~PyShuffledLEcuyerRandom()
{
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYRANDOM_HH__
