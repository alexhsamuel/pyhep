//----------------------------------------------------------------------
//
// PyTimer.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <stack>
#include <sys/times.h>
#include <unistd.h>

#include "PyTimer.hh"
#include "python.hh"

using namespace Py;

//----------------------------------------------------------------------
// variables
//----------------------------------------------------------------------

namespace {

/* Stack of runnign timers.  The most-recently-started is at the top.  */

std::stack<PyTimer*> 
timer_stack;


/* Push 'timer' onto the timer stack.

   Takes a new reference to 'timer'.  */

inline void
timer_stack_push(PyTimer* timer)
{
  // Hold a reference to timers on the stack.
  timer->IncRef();
  timer_stack.push(timer);
}


/* Return a borrowed reference to the timer at the top of the stack.  */

inline PyTimer*
timer_stack_top()
{
  return timer_stack.top();
}


/* Pop the timer at the top of the timer stack.

   Returns a new reference to the popped timer.  */

inline PyTimer*
timer_stack_pop()
{
  // We're holding a reference to the timer on the stack.  Return this
  // reference to the caller.
  PyTimer* top_timer = timer_stack.top();
  timer_stack.pop();
  return top_timer;
}


/* Return true if the timer stack is empty.  */

inline bool
timer_stack_is_empty()
{
  return timer_stack.empty();
}


/* Map from timer names to timer objects.  */

Dict* const
timer_dict = Dict::New();

//----------------------------------------------------------------------
// functions
//----------------------------------------------------------------------

/* Return the current system time, in clock ticks.  */

inline clock_t
getTime()
{
  struct tms process_times;
  clock_t wall_time = times(&process_times);
  return wall_time;
}
  

/* Return a new reference to the timer named 'name'.

   If there is no timer named 'name', create a new one.  */

inline PyTimer*
get(String* name)
{
  if (timer_dict->HasKey(name)) {
    Ref<Object> timer = timer_dict->GetItem(name);
    return newRef(cast<PyTimer>(timer));
  }
  else {
    Ref<PyTimer> new_timer = PyTimer::New();
    timer_dict->SetItem(name, new_timer);
    return new_timer.release();
  }
}


}  // anonymous namespace


PyTimer*
getTimer(const char* name)
{
  Ref<String> name_str = String::FromString(name);
  return get(name_str);
}


//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyTimer::PyTimer()
  : running_(false),
    inclusive_time_(0),
    exclusive_time_(0)
{
}


PyTimer::~PyTimer()
{
}


inline void
PyTimer::start()
{
  assert(! running_);

  clock_t now = getTime();
  // If there is a timer on top of the stack, update its exclusive time,
  // since it won't be active any more.
  if (! timer_stack_is_empty()) {
    PyTimer* top_timer = timer_stack_top();
    top_timer->exclusive_time_ += now - top_timer->exclusive_start_;
  }

  // Put this timer on top of the stack.
  timer_stack_push(this);
  running_ = true;
  // Store start times.
  inclusive_start_ = now;
  exclusive_start_ = now;
}


inline void
PyTimer::stop()
{
  // Make sure the timer is running and active, and pop it from the
  // stack. 
  Ref<PyTimer> top_timer = timer_stack_pop();
  assert(running_);
  assert((PyTimer*) top_timer == this);

  // Update accumulated times.
  clock_t now = getTime();
  exclusive_time_ += now - exclusive_start_;
  inclusive_time_ += now - inclusive_start_;
  running_ = false;

  // If we revealed another timer at the top of the stack, store its
  // start time since it is now active.
  if (! timer_stack_is_empty())
    timer_stack_top()->exclusive_start_ = now;
}


// Conversion factor from clock ticks to seconds.
const double
PyTimer::ticks_to_sec_ = 1.0 / sysconf(_SC_CLK_TCK);


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

namespace {

PyObject*
tp_new(PyTypeObject* type,
       Tuple* args,
       Dict* kw_args)
try {
  // Parse arguments.
  args->ParseTuple("");
  // Construct the object.
  return PyTimer::New();
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyTimer* self)
try {
  // Perform C++ deallocation.
  self->~PyTimer();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
}


PyObject*
tp_str(PyTimer* self)
try {
  // 'String::FromFormat' has trouble with this; not sure why.  Use
  // 'snprintf' instead.
  char str[64];
  snprintf(str, sizeof(str), "incl %8.3f s, excl %8.3f s", 
	   PyTimer::ticks_to_sec_ * self->inclusive_time_,
	   PyTimer::ticks_to_sec_ * self->exclusive_time_);
  return String::FromString(str);
}
catch (Exception) {
  return NULL;
}


PyObject*
tp_repr(PyTimer* self)
try {
  return String::FromFormat("<Timer at %p>", (void*) self);
}
catch (Exception) {
  return NULL;
}


PyObject*
method_start(PyTimer* self)
try {
  // Make sure the timer isn't running.
  if (self->running_)
    throw Exception(PyExc_RuntimeError, "timer is already running");

  self->start();
  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_stop(PyTimer* self)
try {
  // Make sure the timer is runnign and active.
  if (timer_stack_is_empty() || timer_stack_top() != self)
    throw Exception(PyExc_RuntimeError, "timer is not active");

  self->stop();
  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "start", (PyCFunction) method_start, METH_NOARGS, NULL },
  { "stop", (PyCFunction) method_stop, METH_NOARGS, NULL },
  { NULL, NULL, 0, NULL }
};


PyObject*
get_exclusive_time(PyTimer* self)
try {
  return 
    Float::FromDouble(PyTimer::ticks_to_sec_ * self->exclusive_time_);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_inclusive_time(PyTimer* self)
try {
  return 
    Float::FromDouble(PyTimer::ticks_to_sec_ * self->inclusive_time_);
}
catch (Exception) {
  return NULL;
}


PyObject*
get_running(PyTimer* self)
try {
  return newBool(self->running_);
}
catch (Exception) {
  return NULL;
}


struct PyGetSetDef
tp_getset[] = {
  { "exclusive_time", (getter) get_exclusive_time, NULL, NULL, NULL },
  { "inclusive_time", (getter) get_inclusive_time, NULL, NULL, NULL },
  { "running", (getter) get_running, NULL, NULL, NULL },
  { NULL, NULL, NULL, NULL, NULL },
};


}  // anonymous namespace


PyTypeObject
PyTimer::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "Timer",                              // tp_name
  sizeof(PyTimer),                      // tp_size
  0,                                    // tp_itemsize
  (destructor) tp_dealloc,              // tp_dealloc
  NULL,                                 // tp_print
  NULL,                                 // tp_getattr
  NULL,                                 // tp_setattr
  NULL,                                 // tp_compare
  (reprfunc) tp_repr,                   // tp_repr
  NULL,                                 // tp_as_number
  NULL,                                 // tp_as_sequence
  NULL,                                 // tp_as_mapping
  NULL,                                 // tp_hash
  NULL,                                 // tp_call
  (reprfunc) tp_str,                    // tp_str
  NULL,                                 // tp_getattro
  NULL,                                 // tp_setattro
  NULL,                                 // tp_as_buffer
  Py_TPFLAGS_DEFAULT 
  | Py_TPFLAGS_BASETYPE,                // tp_flags
  NULL,                                 // tp_doc
  NULL,                                 // tp_traverse
  NULL,                                 // tp_clearurn
  NULL,                                 // tp_richcompare
  0,                                    // tp_weaklistoffset
  NULL,                                 // tp_iter
  NULL,                                 // tp_iternext
  tp_methods,                           // tp_methods
  NULL,                                 // tp_members
  tp_getset,                            // tp_getset
  NULL,                                 // tp_base
  NULL,                                 // tp_dict
  NULL,                                 // tp_descr_get
  NULL,                                 // tp_descr_set
  0,                                    // tp_dictoffset
  NULL,                                 // tp_init
  NULL,                                 // tp_alloc
  (newfunc) tp_new,                     // tp_new
};


PyObject*
function_timer_get(PyObject*,
		   Arg* args)
try {
  // Parse arguments.
  Object* name_arg;
  args->ParseTuple("O", &name_arg);
  Ref<String> name = name_arg->Str();
  // Get the named timer.
  return get(name);
}
catch (Exception) {
  return NULL;
}


PyObject*
function_timer_start(PyObject*,
		     Arg* args)
try {
  // Parse arguments.
  Object* name_arg;
  args->ParseTuple("O", &name_arg);
  Ref<String> name = name_arg->Str();
  // Get the named timer.
  Ref<PyTimer> timer = get(name);
  // Make sure it's not running.
  if (timer->running_)
    throw Exception(PyExc_RuntimeError, "timer is already running");
  // Start it.
  timer->start();

  return timer.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
function_timer_stop(PyObject*,
		    Arg* args)
try {
  // Parse arguments.
  Object* name_arg = NULL;
  args->ParseTuple("|O", &name_arg);
  // Was a timer name specified?
  Ref<PyTimer> timer;
  if (name_arg == NULL)
    // No.  Use the timer at the top of the stack.
    timer = Ref<PyTimer>::create(timer_stack_top());
  else {
    // Yes. Look up the timer by name.
    Ref<String> name = name_arg->Str();
    timer.set(get(name));
    // Make sure it's the active timer.
    if (timer_stack_is_empty() || timer_stack_top() != timer)
      throw Exception(PyExc_RuntimeError, "timer is not active");
  }

  // Stop it.
  timer->stop();
  // Return it.
  return timer.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
function_timer_stopAll(PyObject*)
try {
  while (! timer_stack_is_empty()) 
    timer_stack_top()->stop();

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
function_timer_printAll(PyObject*)
try {
  // Get a list of names of timers in the dictionary, and sort them.
  Ref<Sequence> timer_names = timer_dict->Keys();
  Ref<Object> ignored = timer_names->CallMethod("sort", "");

  // Print a line for each timer.
  for (int i = 0; i < timer_names->Size(); ++i) {
    Ref<Object> item = timer_names->GetItem(i);
    String* name = cast<String>(item);
    Ref<PyTimer> timer = timer_dict->GetItem(name);
    Ref<String> timer_str = timer->Str();
    printf("timer '%s'%*s: %s\n", name->AsString(), 
	   24 - name->Size(), "", timer_str->AsString());
  }

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}

