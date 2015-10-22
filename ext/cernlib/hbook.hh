//----------------------------------------------------------------------
// 
// hbook.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Implementation of Python HEP classes on top of the HBOOK library.  */

#ifndef __HBOOK_HH__
#define __HBOOK_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include "python.hh"

//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern PyObject* function_createColumnWiseNtuple(PyObject* self, 
						 Py::Arg* args);
extern PyObject* function_createRowWiseNtuple(PyObject* self, 
					      Py::Arg* args);
extern PyObject* function_openTuple(PyObject* self, Py::Arg* args);
extern PyObject* function_writeMetadata(PyObject* self, Py::Arg* args);

//----------------------------------------------------------------------

#endif  // #ifndef __HBOOK_HH__
