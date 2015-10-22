//----------------------------------------------------------------------
//
// PyContour.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python extension function for computing contour plots.  */

#ifndef __PYCONTOUR_HH__
#define __PYCONTOUR_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Python.h>

#include "python.hh"

//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern PyObject* function_contours(Py::Object*, Py::Arg* args);

//----------------------------------------------------------------------

#endif  // #ifndef __PYCONTOUR_HH__
