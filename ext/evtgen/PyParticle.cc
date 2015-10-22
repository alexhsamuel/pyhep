//----------------------------------------------------------------------
//
// PyParticle.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <iostream>

#include "EvtGenBase/EvtParticle.hh"
#include "EvtGenBase/EvtParticleFactory.hh"
#include "EvtGenBase/EvtPDL.hh"
#include "EvtGenBase/EvtVector4R.hh"
#include "PyParticle.hh"

using namespace Py;

//----------------------------------------------------------------------
// methods
//----------------------------------------------------------------------

PyParticle::PyParticle(EvtParticle* particle,
		       bool owns_particle)
  : particle_(particle),
    owns_particle_(owns_particle)
{
}


PyParticle::~PyParticle()
{
  assert(particle_ != NULL);
  if (owns_particle_)
    delete particle_;

}


//----------------------------------------------------------------------
// Python support
//----------------------------------------------------------------------

namespace {

PyParticle*
tp_new(PyTypeObject* self,
       Tuple* args,
       Dict* kw_args)
try {
  char* name;
  double p0, p1, p2, p3;
  bool choose_momentum = false;
  if (args->Size() == 1) {
    args->ParseTuple("s", &name);
    choose_momentum = true;
  }
  else
    args->ParseTuple("sdddd", &name, &p0, &p1, &p2, &p3);

  EvtId id = EvtPDL::getId(name);
  if (id.getId() == -1)
    throw Exception(PyExc_ValueError, "unknown name '%s'", name);
  // If no momemtum was specified, construct it for the particle at rest.
  if (choose_momentum) {
    p0 = EvtPDL::getMeanMass(id);
    p1 = 0.0;
    p2 = 0.0;
    p3 = 0.0;
  }
  EvtVector4R momentum(p0, p1, p2, p3);

  // Construct the EvtGen particle.
  EvtParticle* particle = 
    EvtParticleFactory::particleFactory(id, momentum);
  assert(particle != NULL);

  // Wrap it.
  return PyParticle::New(particle, true);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyParticle* self)
try {
  // Perform C++ deallocation.
  self->~PyParticle();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
  return;
}


PyObject*
tp_str(PyParticle* self)
try {
  EvtId id = self->particle_->getId();
  std::string name = EvtPDL::name(id);
  
  return String::FromFormat("<%s>", name.c_str());
}
catch (Exception) {
  return NULL;
}


PyObject*
get_decay_products(PyParticle* self,
		   void* /* closure */)
try {
  int length = self->particle_->getNDaug();
  Ref<Tuple> result = Tuple::New(length);
  for (int i = 0; i < length; ++i) {
    EvtParticle* daughter = self->particle_->getDaug(i);
    result->InitializeItem(i, PyParticle::New(daughter, false));
  }

  return result.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
get_momentum(PyParticle* self,
	     void* /* closure */)
try {
  Ref<Object> lab_obj = import("hep.lorentz", "lab");
  EvtVector4R p4 = self->particle_->getP4Lab();
  return lab_obj->CallMethod
    ("Momentum", "dddd", p4.get(0), p4.get(1), p4.get(2), p4.get(3));
}
catch (Exception) {
  return NULL;
}


PyObject*
get_position(PyParticle* self,
	     void* /* closure */)
try {
  Ref<Object> lab_obj = import("hep.lorentz", "lab");
  EvtVector4R x4 = self->particle_->get4Pos();
  return lab_obj->CallMethod
    ("Vector", "dddd", x4.get(0), x4.get(1), x4.get(2), x4.get(3)); 
}
catch (Exception) {
  return NULL;
}


PyObject*
get_species(PyParticle* self,
	    void* /* closure */)
try {
  EvtId id = self->particle_->getId();
  std::string name = EvtPDL::name(id);
  return String::FromString(name);
}  
catch (Exception) {
  return NULL;
}


struct PyGetSetDef
tp_getset[] = {
  { "decay_products", (getter) get_decay_products, NULL, NULL, NULL },
  { "momentum", (getter) get_momentum, NULL, NULL, NULL },
  { "position", (getter) get_position, NULL, NULL, NULL },
  { "species", (getter) get_species, NULL, NULL, NULL },
  { NULL, NULL, NULL, NULL, NULL },
};


}  // anonymous namespace

//----------------------------------------------------------------------

PyTypeObject
PyParticle::type = 
{
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Particle",                           // tp_name
  sizeof(PyParticle),                   // tp_size
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
  (reprfunc) &tp_str,                   // tp_str
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
  NULL,                                 // tp_methods
  NULL,                                 // tp_members
  tp_getset,                            // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) &tp_new,                    // tp_new
};
