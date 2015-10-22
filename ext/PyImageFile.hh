//----------------------------------------------------------------------
//
// PyImageFile.hh
//
// Copyright 2005 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Rendering to memory bitmap for writing to an image file.  */

#ifndef __PYIMAGEFILE_HH__
#define __PYIMAGEFILE_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>

#include "aggrender.hh"
#include "python.hh"

//----------------------------------------------------------------------
// class definitions
//----------------------------------------------------------------------

struct PyImageFile
  : public Py::Object
{
  static PyTypeObject type;
  static PyImageFile* New(int width, int height);
  static bool Check(PyObject* object);

  PyImageFile(int width, int height);
  ~PyImageFile();

  // The image renderer.
  AggImage renderer_;

};


//----------------------------------------------------------------------
// inline function definitions
//----------------------------------------------------------------------

inline PyImageFile*
PyImageFile::New(int width,
		 int height)
{
  // Construct the Python object.
  PyImageFile* result = Py::allocate<PyImageFile>();
  // Perform C++ construction.
  try {
    new(result) PyImageFile(width, height);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }
  
  return result;
}


inline bool
PyImageFile::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYIMAGEFILE_HH__
