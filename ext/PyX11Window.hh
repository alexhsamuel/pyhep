//----------------------------------------------------------------------
//
// PyX11Window.hh
//
// Copyright 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Xlib-based rendering window.  */

#ifndef __PYX11WINDOW_HH__
#define __PYX11WINDOW_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xft/Xft.h>
#include <map>

// The 'Complex' and 'None' X11 macros interfere with types in python.hh.
#undef Complex
#undef None
#include "python.hh"

#include "aggrender.hh"

//----------------------------------------------------------------------
// class definitions
//----------------------------------------------------------------------

struct PyX11Window
  : public Py::Object
{
  static PyTypeObject type;
  static PyX11Window* New(int width, int height);
  static bool Check(PyObject* object);
  static void Delete(PyX11Window* draw);

  PyX11Window(int width, int height);
  ~PyX11Window();

  void resizeImage(int width, int height);
  void confirmNotDestroyed() const;
  void onDestroy();
  void update();

  // True if the window has been destroyed.
  bool is_destroyed_;

  // Image object and GC used for drawing the image.
  XImage* image_;
  GC gc_;

  // The X window.
  Window window_;

  // Used for handling window manager messages.
  Atom wm_delete_window_;

  // State for idle processing.
  double last_idle_time_;
  double idle_interval_;

  // The event callback function.
  Py::Ref<Py::Object> event_function_;

  // The window image renderer.
  AggImage renderer_;

};


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

PyObject* function_X11_initialize(PyObject*, Py::Arg* args);
PyObject* function_X11_getScreenSize(PyObject*, Py::Arg* args);
extern Display* initializeX11(const char* display_name=NULL);

//----------------------------------------------------------------------
// inline function definitions
//----------------------------------------------------------------------

inline PyX11Window* 
PyX11Window::New(int width,
		 int height)
{
  // Construct the Python object.
  PyX11Window* result = Py::allocate<PyX11Window>();
  // Perform C++ construction.
  try {
    new(result) PyX11Window(width, height);
  }
  catch (Py::Exception) {
    Py::deallocate(result);
    throw;
  }

  return result;
}


inline bool
PyX11Window::Check(PyObject* object)
{
  return ((Py::Object*) object)->IsInstance(&type);
}


inline void
PyX11Window::Delete(PyX11Window* window)
{
  // Perform C++ deallocation.
  window->~PyX11Window();
  // Deallocate memory.
  PyMem_DEL(window);
}


inline void
PyX11Window::confirmNotDestroyed()
  const
{
  if (is_destroyed_)
    throw Py::Exception(PyExc_RuntimeError, 
			"window has already destroyed");
}


//----------------------------------------------------------------------

#endif  // #ifndef __PYX11WINDOW_HH__
