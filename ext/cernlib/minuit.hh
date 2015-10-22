//----------------------------------------------------------------------
// 
// minuit.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python interface to the MINUIT library.  */

#ifndef __MINUIT_HH__
#define __MINUIT_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include "python.hh"

//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern PyObject* function_minuit_minimize(PyObject* self, Py::Arg* args);
extern PyObject* function_minuit_maximumLikelihoodFit(PyObject* self, 
						      Py::Arg* args);

//----------------------------------------------------------------------

#endif  // #ifndef __MINUIT_HH__
