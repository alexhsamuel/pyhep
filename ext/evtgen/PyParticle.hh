//----------------------------------------------------------------------
//
// PyParticle.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Wrapper class for EvtGen particle.  */

#ifndef __PYPARTICLE_HH__
#define __PYPARTICLE_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <Python.h>

#include "python.hh"

//----------------------------------------------------------------------
// forward declrations
//----------------------------------------------------------------------

class EvtParticle;

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

struct PyParticle
  : public Py::Object
{
  static PyTypeObject type;
  static PyParticle* New(EvtParticle* particle, bool owns_particle);

  PyParticle(EvtParticle* particle, bool owns_particle);
  ~PyParticle();

  EvtParticle* particle_;
  bool owns_particle_;
};


inline PyParticle*
PyParticle::New(EvtParticle* particle,
		bool owns_particle)
{
  // Construct the Python object.
  PyParticle* result = Py::allocate<PyParticle>();
  // Perform C++ construction.
  try {
    new(result) PyParticle(particle, owns_particle);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }

  return result;
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYPARTICLE_HH__

