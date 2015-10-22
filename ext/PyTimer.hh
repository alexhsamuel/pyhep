//----------------------------------------------------------------------
//
// PyTimer.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Execution timer extension class.  

   Uses times() to obtain the current time.  On Linux, this limits the
   resolution to one clock tick = 10 msec.  */

#ifndef __PYTIMER_HH__
#define __PYTIMER_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>

#include "python.hh"

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

struct PyTimer
  : public Py::Object
{
  static PyTypeObject type;
  static PyTimer* New();
  static bool Check(PyObject* object);

  PyTimer();
  ~PyTimer();

  /* Start the timer.

     The timer must not be running.  */
  void start();

  /* Stop the timer.

     The timer must be running.  The timer must be the active timer,
     i.e. since this timer was started, no other timer was started and
     not subsequently stopped.  */
  void stop();

  /* True if this timer is running.  */
  bool running_;

  /* Total time this timer has been running, in clock ticks.  */
  long inclusive_time_;

  /* Exclusive time this timer has been running, in clock tick.

     This is equal to the total time minus the time that other timers
     have been running "on top of" this one.  */
  long exclusive_time_;

  clock_t inclusive_start_;
  clock_t exclusive_start_;

  static const double ticks_to_sec_;

};


inline PyTimer*
PyTimer::New()
{
  // Construct the Python object.
  PyTimer* result = Py::allocate<PyTimer>();
  // Perform C++ construction.
  try {
    new(result) PyTimer();
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }

  return result;
}


inline bool
PyTimer::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


//----------------------------------------------------------------------

class TimerRun
{
public:
  
  TimerRun(PyTimer* timer) : timer_(timer) { timer->start(); }
  ~TimerRun() { timer_->stop(); }

private:

  PyTimer* const timer_;

};


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern PyTimer* getTimer(const char* name);

extern PyObject* function_timer_get(PyObject*, Py::Arg* args);
extern PyObject* function_timer_start(PyObject*, Py::Arg* args);
extern PyObject* function_timer_stop(PyObject*, Py::Arg* args);
extern PyObject* function_timer_stopAll(PyObject*);
extern PyObject* function_timer_printAll(PyObject*);

//----------------------------------------------------------------------

#endif  // #ifndef __PYTIMER_HH__
