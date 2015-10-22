//----------------------------------------------------------------------
//
// tree.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Table implementation based on Root trees.  */

#ifndef __TREE_HH__
#define __TREE_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include "python.hh"

//----------------------------------------------------------------------
// Python function declarations
//----------------------------------------------------------------------

PyObject* function_createTree(PyObject* self, Py::Arg* args);
PyObject* function_openTree(PyObject* self, Py::Arg* args);

//----------------------------------------------------------------------

#endif  // #ifndef __TREE_HH__
