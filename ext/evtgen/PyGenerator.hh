//----------------------------------------------------------------------
//
// PyGenerator.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Wrapper class for EvtGen generator.  */

#ifndef __PYGENERATOR_HH__
#define __PYGENERATOR_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <memory>
#include <Python.h>

#include "python.hh"

//----------------------------------------------------------------------
// forward declarations
//----------------------------------------------------------------------

class EvtGen;
class EvtRandomEngine;

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

struct PyGenerator
  : public Py::Object
{
  static PyTypeObject type;
  static PyGenerator* New(const char* decay_file_path, const char* pdt_path);

  PyGenerator(const char* decay_file_path, const char* pdt_path);
  ~PyGenerator();

  std::auto_ptr<EvtRandomEngine> random_engine_;
  std::auto_ptr<EvtGen> generator_;
};


inline PyGenerator*
PyGenerator::New(const char* decay_file_path,
		 const char* pdt_path)
{
  // Construct the Python object.
  PyGenerator* result = Py::allocate<PyGenerator>();
  // Perform C++ construction.
  try {
    new(result) PyGenerator(decay_file_path, pdt_path);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }
  
  return result;
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYGENERATOR_HH__
