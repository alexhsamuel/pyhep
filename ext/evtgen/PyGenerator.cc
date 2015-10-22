//----------------------------------------------------------------------
//
// PyGenerator.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <string>
#include <unistd.h>

#include "EvtGen/EvtGen.hh"
#include "EvtGenBase/EvtRandom.hh"
#include "EvtGenBase/EvtRandomEngine.hh"
#include "PyGenerator.hh"
#include "PyParticle.hh"
#include "python.hh"
#include "random.hh"

using namespace Py;

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

class EvtShuffledLEcuyerRandomEngine
  : public EvtRandomEngine
{
public:

  virtual ~EvtShuffledLEcuyerRandomEngine();
  virtual double random();

private:

  ShuffledLEcuyerRandom engine_;

};


//----------------------------------------------------------------------
// class members
//----------------------------------------------------------------------

EvtShuffledLEcuyerRandomEngine::~EvtShuffledLEcuyerRandomEngine()
{
}


double 
EvtShuffledLEcuyerRandomEngine::random()
{
  return engine_.random();
}


//----------------------------------------------------------------------

PyGenerator::PyGenerator(const char* decay_file_path,
			 const char* pdt_path)
  : random_engine_(new EvtShuffledLEcuyerRandomEngine)
{
  generator_.reset
    (new EvtGen(decay_file_path, pdt_path, random_engine_.get()));
}


PyGenerator::~PyGenerator()
{
}


//----------------------------------------------------------------------
// Python support
//----------------------------------------------------------------------

namespace {

/* Extract a path from an argument tuple.

   Extracts the specified argument, converts it to a path string, and
   checks that the path is an accessible (for reading) file.

   'args' -- An argument tuple.

   'index' -- The index of the argument to get.

   returns -- The path string.
*/
inline std::string
getArgPath(Tuple* args,
	   int index)
{
  // Extract the path from the argument tuple.
  Ref<Object> arg_obj = args->GetItem(index);
  std::string path = arg_obj->StrAsString();
  // Make sure the file exists and is readable.
  if (access(path.c_str(), R_OK) != 0)
    throw Exception(PyExc_IOError, "cannot open '%s': %s", 
		    path.c_str(), strerror(errno));
  // All good.
  return path;
}


PyObject*
tp_new(PyTypeObject* type,
       Tuple* args,
       Dict* kw_args)
try {
  std::string pdt_path;
  std::string decay_file_path;

  // Determine the path to the particle data file.
  if (args->Size() < 1) {
    // Use the default particle data file.
    Ref<Object> default_pdt_path = 
      import("hep.evtgen", "default_pdt_path");
    pdt_path = default_pdt_path->StrAsString();
  }
  else 
    // The first argument is the path to the particle data file.
    pdt_path = getArgPath(args, 0);

  // Determine the path to the decay file.
  if (args->Size() < 2) {
    // Use the default decay file.
    Ref<Object> default_decay_file_path =
      import("hep.evtgen", "default_decay_file_path");
    decay_file_path = default_decay_file_path->StrAsString();
  }
  else 
    // The second argument is the path to the main decay file.
    decay_file_path = getArgPath(args, 1);

  // Construct the generator.
  Ref<PyGenerator> result = 
    PyGenerator::New(decay_file_path.c_str(), pdt_path.c_str());

  // Interpret any additional arguments as paths to user decay files,
  // and load these.
  for (int a = 2; a < args->Size(); ++a) {
    std::string path = getArgPath(args, a);
    result->generator_->readUDecay(path.c_str());
  }

  // All done.
  return result.release();
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyGenerator* self)
try {
  // Perform C++ deallocation.
  self->~PyGenerator();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
  return;
}


PyObject*
method_decay(PyGenerator* self,
	     Tuple* args)
try {
  PyParticle* particle;
  args->ParseTuple("O!", &PyParticle::type, &particle);

  self->generator_->generateDecay
    (const_cast<EvtParticle*> (particle->particle_));

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_readDecayFile(PyGenerator* self,
		     Tuple* args)
try {
  const char* decay_file_path;
  args->ParseTuple("s", &decay_file_path);
  // Make sure the file exists and is readable.
  if (access(decay_file_path, R_OK) != 0)
    throw ExceptionFromErrno();
    
  self->generator_->readUDecay(decay_file_path);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "decay", (PyCFunction) method_decay, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


}  // anonymous namespace


PyTypeObject
PyGenerator::type = 
{
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Generator",                          // tp_name
  sizeof(PyGenerator),                  // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  NULL,                                 // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  NULL,                                 // tp_as_mapping
  NULL,                                 // tp_hash
  NULL,                                 // tp_call
  NULL,                                 // tp_str
  NULL,                                 // tp_getattro
  NULL,                                 // tp_setattro
  NULL,                                 // tp_as_buffer
  Py_TPFLAGS_DEFAULT
  | Py_TPFLAGS_BASETYPE,                // tp_flags
  NULL,                                 // tp_doc
  NULL,                                 // tp_traverse
  NULL,                                 // tp_clear
  NULL,                                 // tp_richcompare
  0,                                    // tp_weaklistoffset
  NULL,                                 // tp_iter
  NULL,                                 // tp_iternext
  tp_methods,                           // tp_methods
  NULL,                                 // tp_members
  NULL,                                 // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) &tp_new,                    // tp_new
};


//----------------------------------------------------------------------
// global functions
//----------------------------------------------------------------------

extern "C"
{


// These two functions are called by JetSet.

float 
begran_(int*)
{
  return EvtRandom::Flat();
}


float 
rlu_()
{
  return EvtRandom::Flat();
}


}  // extern "C"
