//----------------------------------------------------------------------
//
// evtgen/ext.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python extension module for access to EvtGen libraries.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <iostream>
#include <Python.h>

#include "PyParticle.hh"
#include "PyGenerator.hh"
#include "python.hh"

using namespace Py;

//----------------------------------------------------------------------
// Python module definition
//----------------------------------------------------------------------

namespace {

PyMethodDef
functions[] = 
{
  { NULL, NULL, 0, NULL }
};

PyTypeObject*
types[] = {
  &PyGenerator::type,
  &PyParticle::type,
  NULL
};


}  // anonymous namespace


extern "C" {

void 
initext()
try {
  Module::Initialize("ext", functions, types, "");
}
catch (Exception) {
  std::cerr << "could not initialize module 'ext'" << std::endl;
}


}  // extern "C"
