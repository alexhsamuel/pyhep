//----------------------------------------------------------------------
//
// PyX11Window.cc
//
// Copyright (C) 2004 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <map>
#include <pthread.h>
#include <time.h>
#include <vector>

#include "PyX11Window.hh"

using namespace Py;

//----------------------------------------------------------------------
// global variables
//----------------------------------------------------------------------

namespace {

/* Names of X11 event types, indexed by the X11 event type code.  */
const char* const 
event_names[] = {
  "unknown (0)",
  "unknown (1)",
  "KeyPress",
  "KeyRelease",
  "ButtonPress",
  "ButtonRelease",
  "MotionNotify",
  "EnterNotify",
  "LeaveNotify",
  "FocusIn",
  "FocusOut",
  "KeymapNotify",
  "Expose",
  "GraphicsExpose",
  "NoExpose",
  "VisibilityNotify",
  "CreateNotify",
  "DestroyNotify",
  "UnmapNotify",
  "MapNotify",
  "MapRequest",
  "ReparentNotify",
  "ConfigureNotify",
  "ConfigureRequest",
  "GravityNotify",
  "ResizeRequest",
  "CirculateNotify",
  "CirculateRequest",
  "PropertyNotify",
  "SelectionClear",
  "SelectionRequest",
  "SelectionNotify",
  "ColormapNotify",
  "ClientMessage",
  "MappingNotify",
};


//----------------------------------------------------------------------
// Information about the event thread.

/* The POSIX thread object representing the thread.  */
pthread_t
event_thread;


/* The Python thread state object for the thread.  */
PyThreadState*
thread_state;


/* X event polling interval, in seconds.  */
double
event_polling_interval = 0.10;


//----------------------------------------------------------------------
// Information about our current X11 connection.

struct XInfo
{
  XInfo(Display* display);

  /* The display.  */
  Display* display;

  /* The screen number  */
  int screen_number;
  
  /* Information about the visual.  */
  int depth;
  Visual* visual;
  int bits_per_pixel;
  PixelFormat pixel_format;
  int byte_order;

  /* A map from X11 window handles to Python window objects.  */
  typedef std::map<Window, PyX11Window*> WindowMap_t;
  WindowMap_t window_map;

};


static struct XInfo*
X = NULL;


//----------------------------------------------------------------------
// helper classes
//----------------------------------------------------------------------

/* Global lock on the X display.

   Because of bugs in many Xlib implementations' thread locking, we
   perform our own.  An instance of this class represents a lock on the
   display.  Note that the lock is not recursive.
*/

class DisplayLock
{
public:

  DisplayLock();
  ~DisplayLock();

private:

  static pthread_mutex_t display_mutex_;

};


inline
DisplayLock::DisplayLock()
{
  pthread_mutex_lock(&display_mutex_);
}


inline
DisplayLock::~DisplayLock()
{
  pthread_mutex_unlock(&display_mutex_);
}


pthread_mutex_t
DisplayLock::display_mutex_ = PTHREAD_MUTEX_INITIALIZER;


//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

XInfo::XInfo(Display* disp)
  : display(disp)
{
  // Get the default screen.
  screen_number = XDefaultScreen(display);
  // Get the default depth.
  depth = XDefaultDepth(display, screen_number);
  // Get the default visual.
  visual = XDefaultVisual(display, screen_number);

  // Determine the hardware's byte order.
  int one = 1;
  int hw_byte_order = (*(char*) &one == 0) ? MSBFirst : LSBFirst;

  // Extract the color masks from the visual.
  unsigned long red_mask = visual->red_mask;
  unsigned long green_mask = visual->green_mask;
  unsigned long blue_mask = visual->blue_mask;

  // Determine the AGG pixel format for this visual.
  pixel_format = PIXELFORMAT_undefined;
  byte_order = LSBFirst;
  switch (depth)
  {
  case 15:
    bits_per_pixel = 16;
    if (red_mask == 0x7c00 && green_mask == 0x3e0 && blue_mask == 0x1f) {
      pixel_format = PIXELFORMAT_rgb555;
      byte_order = hw_byte_order;
    }
    break;
                
  case 16:
    bits_per_pixel = 16;
    if (red_mask == 0xf800 && green_mask == 0x7e0 && blue_mask == 0x1f) {
      pixel_format = PIXELFORMAT_rgb565;
      byte_order = hw_byte_order;
    }
    break;
                
  case 24:
  case 32:
    bits_per_pixel = 32;
    if (green_mask == 0xff00) {
      if (red_mask == 0xff && blue_mask == 0xff0000) {
	pixel_format = PIXELFORMAT_abgr32;
	byte_order = LSBFirst;
      }
      else if (red_mask == 0xff0000 && blue_mask == 0xff) {
	pixel_format = PIXELFORMAT_argb32;
	byte_order = MSBFirst;
      }
    }
    break;

  default:
    break;
  }        
    
  // Make sure we found one that works.
  if (pixel_format == PIXELFORMAT_undefined) {
    throw Exception
      (PyExc_RuntimeError,
       "display is incompatible (depth=%d, mask=%lx/%lx/%lx)",
       depth, red_mask, green_mask, blue_mask);
  }
}


/* Make sure we have initialized X11.  

   Raise a 'RuntimeError' if X11 has not been initialized.  
*/

inline void
confirmInitialized()
{
  if (X->display == NULL)
    throw Exception(PyExc_RuntimeError, 
		    "X11 display has not been initialized");
  if (thread_state == NULL)
    throw Exception(PyExc_RuntimeError, 
		    "X11 event thread has not been started");
}


/* Get the current time, as a double.  */

inline double
getCurrentTime()
{
  struct timeval now;
  gettimeofday(&now, NULL);
  return now.tv_sec + now.tv_usec * 1e-6;
}


/* Extract a point from a Python object.  */

inline Point
parsePoint(Object* point_obj)
{
  Sequence* point_seq = cast<Sequence>(point_obj);
  if (point_seq->Size() != 2)
    throw Exception(PyExc_TypeError, "a point must have two elements");
  Ref<Object> x_obj = point_seq->GetItem(0);
  double x = x_obj->FloatAsDouble();
  Ref<Object> y_obj = point_seq->GetItem(1);
  double y = y_obj->FloatAsDouble();
  return Point(x, y);
}


/* Extract points from 'points_arg' and append them to 'points'.  */
void
parsePoints(Object* points_arg,
	    PointList& points)
{
  Sequence* points_seq = cast<Sequence>(points_arg);

  // Loop over all points to construct the boundary path.
  int num_points = points_seq->Size();
  for (int i = 0; i < num_points; ++i) {
    Ref<Object> point_obj = points_seq->GetItem(i);
    points.push_back(parsePoint(point_obj));
  }
}


/* Send a window event into Pythonland.

   Calls the window's event callback function, if any.

   'window' -- The window that received the event.

   'event_name' -- The name of the event.

   'data' -- Additional data to pass to the function.
*/

void
sendEvent(PyX11Window* window,
	  const char* const event_name,
	  PyObject* data)
{
  if (window->event_function_ == None) 
    // Nothing to do.
    return;

  // Swap the current thread into the Python interpreter.
  ThreadStateSwap tss(thread_state);
  try {
    // Call the callback function.
    Callable* fn = cast<Callable>(window->event_function_);
    Ref<Object> result = 
      fn->CallFunction("OsO", window, event_name, data);
  }
  catch (Exception exception) {
    // We must catch all exceptions here, because there isn't a Python
    // interpreter higher on the call stack in this thread.  Just print
    // out the exception and continue.
    std::cerr << "An exception occurred in X11 event handling:\n";
    exception.Print();
    exception.Clear();
  }
}
	  

/* Thread function to handle X11 events.

   Does not return.  
*/

void*
eventThreadFunction(void* /* cookie */)
{
  while (true) {
    // Get the next event from the X11 queue, if there is one.
    bool have_event;
    XEvent event;
    {
      DisplayLock lock;
      if (XPending(X->display) == 0) {
	// No events in the queue.  
	have_event = false;
      }
      else {
	// There is an event in the queue.  Get it.
	XNextEvent(X->display, &event);
	// Don't sleep on the next iteration, so that we quickly drain
	// the queue.
	have_event = true;
      }
    }

    if (! have_event) {
      // No event.  We may now send idle events to windows that have
      // requested them. 
      double now = getCurrentTime();
      for (XInfo::WindowMap_t::iterator iter = X->window_map.begin();
	   iter != X->window_map.end();
	   ++iter) {
	PyX11Window* window = iter->second;
	// Are idle events ineabled for this window?
	if (window->idle_interval_ < 0)
	  // Nope.
	  continue;
	// Has enough time elapsed?
	if (now - window->last_idle_time_ > window->idle_interval_) {
	  // Yes.  Send an idle event.
	  sendEvent(window, "idle", Py_None);
	  // Reset the idle clock.
	  window->last_idle_time_ = now;
	}
      }
      
      // Sleep for a while before we poll again.
      long sleep_time = long(event_polling_interval * 1000000);
      struct timespec sleep_timespec = 
          { sleep_time / 1000000, sleep_time % 1000000 };
      nanosleep(&sleep_timespec, NULL);

      continue;
    }

    // Make sure the event is for our display.
    assert(X->display == event.xany.display);
    // Extract the window it applies to.
    Window window = event.xany.window;

    // Look up the window in our map to Python window objects.
    XInfo::WindowMap_t::iterator window_map_iter = 
      X->window_map.find(window);
    if (window_map_iter == X->window_map.end())
      // Didn't find it; we don't care about this event.
      continue;
    // Extract the Python window object.
    PyX11Window* self = window_map_iter->second;

    switch (event.type) {
    case ClientMessage:
      // Check which client message this is.
      if ((unsigned) event.xclient.data.l[0] == self->wm_delete_window_) {
	DisplayLock lock;
	// The window manager has asked us to close the window.  Do it.
	XDestroyWindow(X->display, self->window_);
      }
      else
	// Ignore other messages.
	;
      break;

    case ConfigureNotify:
      // Check whether the window size has changed.
      if (event.xconfigure.width != self->renderer_.getWidth()
	  || event.xconfigure.height != self->renderer_.getHeight()) {
	// It did.  First, resize the image image to the new window size.
	{
	  DisplayLock lock; 
	  self->resizeImage(event.xconfigure.width, 
			    event.xconfigure.height);
	}
	// Notify the window's callback function.
	Ref<Object> window_size = 
	  Py_BuildValue("(ii)", self->renderer_.getWidth(), 
			self->renderer_.getHeight());
	sendEvent(self, "resize", window_size);
      }
      break;

    case DestroyNotify:
      { 
	DisplayLock lock;
	// Ask the window to clean up its stuff.
	self->onDestroy();
      }
      // Notify the window's callback function.
      sendEvent(self, "destroy", None);
      break;

    case Expose:
      // We are going to repaint the entire window, so remove any
      // additional expose events in the event queue for this window.
      {
	DisplayLock lock;
	XEvent extra_expose_event;
	while (XCheckWindowEvent(X->display, window, 
				 ExposureMask, &extra_expose_event))
	  ;
      }

      // Redraw the window.
      self->update();
      break;

    default:  // Unknown event type: ignore it.
      break;
    }
  }

  // Unreachable.
  abort();
}


/* Start up the X11 event thread.  */

void
initializeEventThread()
{
  // X11 must already be set up.
  if (X == NULL)
    throw Exception(PyExc_RuntimeError, 
		    "X11 display has not been initialized");

  if (thread_state != NULL)
    // Already initialized; nothing to do.
    return;

  DisplayLock lock;

  // Tell Python we will be using threads.
  PyEval_InitThreads();
  PyEval_ReleaseLock();
  // Construct a new thread state object for the event thread.
  thread_state = PyThreadState_New(PyThreadState_Get()->interp);
  // Start the event thread.
  int result = 
    pthread_create(&event_thread, NULL, eventThreadFunction, NULL);
  // Make sure it works!
  if (result != 0) {
    PyThreadState_Delete(thread_state);
    thread_state = NULL;
    throw Exception(PyExc_RuntimeError, 
		    "could not start X11 event thread");
  }
  PyEval_AcquireLock();
}


}  // anonymous namespace

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyX11Window::PyX11Window(int width,
			 int height)
  : is_destroyed_(false),
    idle_interval_(-1),
    event_function_(newRef(None)),
    renderer_(width, height)
{
  // Make sure X11 is initialized.
  confirmInitialized();

  DisplayLock lock;

  // Create the window.
  Window root_window = RootWindow(X->display, X->screen_number);
  unsigned long attributes_mask = 0;
  XSetWindowAttributes attributes;
  window_ = XCreateWindow
    (X->display, root_window, 0, 0, width, height, 0, X->depth,
     InputOutput, X->visual, attributes_mask, &attributes);
  // Map the X11 window handle to this object.
  X->window_map[window_] = this;

  // Ask for structure notify and exposure events.
  XSelectInput(X->display, window_, 
	       ExposureMask
	       | StructureNotifyMask);

  // Ask the window manager to notify us when the user closes the
  // window, rather than unceremoniously dropping the connection.
  wm_delete_window_ = XInternAtom(X->display, "WM_DELETE_WINDOW", False);
  XSetWMProtocols(X->display, window_, &wm_delete_window_, 1);

  // Create a GC for it.
  XGCValues values;
  gc_ = XCreateGC(X->display, window_, 0, &values);
  assert(gc_ >= 0);

  // Initialize the image size.
  resizeImage(width, height);

  // Put up the window.
  XMapWindow(X->display, window_);
  XFlush(X->display);
}


PyX11Window::~PyX11Window()
{
  DisplayLock lock;

  if (! is_destroyed_) {
    onDestroy();
    XDestroyWindow(X->display, window_);
    XFlush(X->display);
  }
}


/* Resize the image to 'width' by 'height' pixels.

   The caller must hold the X display lock.

   'first_time' -- This is the first call to this function; no need copy
   the old image's contents, or free the old image.
*/

void
PyX11Window::resizeImage(int width,
			 int height)
{
  // Hold on to the old image.
  XImage* old_image = image_;
  if (old_image != NULL)
    old_image->data = NULL;

  // Create a new image of the appropriate size.  We don't actually need
  // an image buffer here; we'll set one before we paint from this
  // image. 
  image_ = XCreateImage
    (X->display, X->visual, X->depth, ZPixmap, 0, NULL, 
     width, height, X->bits_per_pixel, width * (X->bits_per_pixel / 8));
  image_->byte_order = X->byte_order;

  renderer_.resize(width, height);

  // Clean up the old image.
  if (old_image != NULL) 
    XDestroyImage(old_image);
}


/* Deallocate X resources when the window has been destroyed.

   The caller must hold the X display lock.  
*/

void
PyX11Window::onDestroy()
{
  // Mark the window as destroyed.
  is_destroyed_ = true;

  // Remove the window from the map, since it won't exist any more.
  XInfo::WindowMap_t::iterator window_map_iter = 
    X->window_map.find(window_);
  assert(window_map_iter != X->window_map.end());
  assert(window_map_iter->second == this);
  X->window_map.erase(window_map_iter);

  // Clean up X11 resources.
  XFreeGC(X->display, gc_);

  // Clean up the image buffer and the image.
  image_->data = NULL;
  XDestroyImage(image_);
}


/* Paint the contents of the image into the window.

   The caller must hold the X display lock.
*/

void
PyX11Window::update()
{
  // Convert the image to the pixel format used by the display.
  char* image_buffer = renderer_.getImageBuffer(X->pixel_format);

  // Save the old image buffer.
  char* old_image_data = image_->data;
  // Set the converted image buffer into our X image object.
  image_->data = image_buffer;
  // Draw the image.
  XPutImage(X->display, window_, gc_, image_, 0, 0, 0, 0, 
	    renderer_.getWidth(), renderer_.getHeight());
  // Restore the old image buffer.
  image_->data = old_image_data;
  // Clean up.
  delete[] image_buffer;
}


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

namespace {

PyObject*
tp_new(PyTypeObject* type,
       Arg* args,
       Dict* kw_args)
try {
  // Parse arguments.
  int width;
  int height;
  args->ParseTuple("ii", &width, &height);
  // Check arguments.
  if (width < 1 || height < 1)
    throw Exception(PyExc_ValueError, "width and height must be positive");

  // Construct the object.
  return PyX11Window::New(width, height);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyX11Window* self)
try {
  // Perform C++ deallocation.
  self->~PyX11Window();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
}


PyObject*
method_destroy(PyX11Window* self,
	       Arg* args)
try {
  DisplayLock lock;

  if (! self->is_destroyed_) {
    self->is_destroyed_ = true;
    XDestroyWindow(X->display, self->window_);
    XFlush(X->display);
  }
  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_drawCircle(PyX11Window* self, 
		  Arg* args)
try {
  double x, y, r;
  Object* fill_arg;
  args->ParseTuple("dddO", &x, &y, &r, &fill_arg);
  bool fill = fill_arg->IsTrue();

  if (self->is_destroyed_)
    RETURN_NONE;

  DisplayLock lock;
  self->renderer_.drawCircle(Point(x, y), r, fill);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_drawLine(PyX11Window* self, 
		Arg* args)
try {
  Object* points_arg;
  args->ParseTuple("O", &points_arg);

  // Parse the points in the line.
  PointList points;
  parsePoints(points_arg, points);

  if (self->is_destroyed_)
    RETURN_NONE;

  DisplayLock lock;
  self->renderer_.drawLine(points);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_drawPolygon(PyX11Window* self, 
		   Arg* args)
try {
  Object* points_arg;
  args->ParseTuple("O", &points_arg);

  PointList points;
  parsePoints(points_arg, points);

  if (self->is_destroyed_)
    RETURN_NONE;

  DisplayLock lock;
  self->renderer_.drawPolygon(points);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_drawText(PyX11Window* self,
		Arg* args)
try {
  Point point;
  PyUnicodeObject* text_arg;
  args->ParseTuple("ddU", &point.x, &point.y, &text_arg);
  
  wchar_t text[text_arg->length];
  int len_text = PyUnicode_AsWideChar(text_arg, text, text_arg->length);
  assert(len_text == text_arg->length);

  if (self->is_destroyed_)
    RETURN_NONE;

  try {
    DisplayLock lock;
    self->renderer_.drawText(point, text, len_text);
  }
  catch (NoFontError) {
    throw Exception(PyExc_RuntimeError, "no font set");
  }

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_resize(PyX11Window* self,
	      Arg* args)
try {
  // Parse arguments.
  int width;
  int height;
  Object* fix_aspect_arg = NULL;
  args->ParseTuple("ii|O", &width, &height, &fix_aspect_arg);
  bool fix_aspect = 
    (fix_aspect_arg == NULL) ? false : fix_aspect_arg->IsTrue();

  // Don't let the sizes exceed the screen size.
  int screen_width = DisplayWidth(X->display, X->screen_number);
  int screen_height = DisplayHeight(X->display, X->screen_number);
  if (width > 2 * screen_width || height > 2 * screen_height)
    throw Exception(PyExc_ValueError, "window size is too large");

  DisplayLock lock;

  XSizeHints* size_hints = XAllocSizeHints();
  // Tell the window manager about the window size.  Otherwise it may
  // not allow the window to be resized.  Also set the minimum window
  // size.
  size_hints->flags = PBaseSize | PMinSize;
  size_hints->base_width = width;
  size_hints->base_height = height;
  size_hints->min_width = 0;
  size_hints->min_height = 0;
  // Tell the window manager to fix the aspect ratio, if requested.
  if (fix_aspect) {
    size_hints->flags |= PAspect;
    size_hints->min_aspect.x = width;
    size_hints->min_aspect.y = height;
    size_hints->max_aspect.x = width;
    size_hints->max_aspect.y = height;
  }
  XSetWMNormalHints(X->display, self->window_, size_hints);
  XFree(size_hints);
  // Resize the window.
  XResizeWindow(X->display, self->window_, width, height);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_update(PyX11Window* self, 
	      Arg* args)
try {
  args->ParseTuple("");

  if (self->is_destroyed_)
    RETURN_NONE;

  DisplayLock lock;
  self->update();

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyMethodDef
tp_methods[] = {
  { "destroy", (PyCFunction) method_destroy, METH_VARARGS, NULL },
  { "drawCircle", (PyCFunction) method_drawCircle, METH_VARARGS, NULL },
  { "drawLine", (PyCFunction) method_drawLine, METH_VARARGS, NULL },
  { "drawPolygon", (PyCFunction) method_drawPolygon, METH_VARARGS, NULL },
  { "drawText", (PyCFunction) method_drawText, METH_VARARGS, NULL },
  { "resize", (PyCFunction) method_resize, METH_VARARGS, NULL },
  { "update", (PyCFunction) method_update, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


int
set_color(PyX11Window* self,
	  Object* value,
	  void* /* cookie */)
try {
  // Make sure the value is an three-element sequence.
  if (! Sequence::Check(value))
    throw Exception(PyExc_ValueError, 
		    "color must be an '(r,g,b)' sequence");
  Sequence* rgb_tuple = cast<Sequence>(value);
  if (rgb_tuple->Size() != 3)
    throw Exception(PyExc_ValueError, 
		    "color must be an '(r,g,b)' sequence");

  // Decode red, green, and blue values.  Make sure each is between zero
  // and one. 
  Ref<Object> r_obj = rgb_tuple->GetItem(0);
  double r = r_obj->FloatAsDouble();
  r = (r < 0) ? 0 : (r > 1) ? 1 : r;
  Ref<Object> g_obj = rgb_tuple->GetItem(1);
  double g = g_obj->FloatAsDouble();
  g = (g < 0) ? 0 : (g > 1) ? 1 : g;
  Ref<Object> b_obj = rgb_tuple->GetItem(2);
  double b = b_obj->FloatAsDouble();
  b = (b < 0) ? 0 : (b > 1) ? 1 : b;

  DisplayLock lock;
  self->renderer_.setColor(Color(r, g, b));

  return 0;
}
catch (Exception) {
  return -1;
}


int
set_dash(PyX11Window* self,
	 Object* value,
	 void* /* cookie */)
try {
  // Start with an empty list.
  Dash dash;

  if (value != Py_None) {
    // A sequece of dash/gap lengths is provided.  Parse it.
    Sequence* dash_seq = cast<Sequence>(value);
    int num_dash = dash_seq->Size();
    // Make sure there are an even number of elements.
    if ((num_dash % 2) != 0)
      throw Exception(PyExc_ValueError, 
		      "dash must have an even number of elements");
    // Loop over them.
    for (int i = 0; i < num_dash / 2; ++i) {
      Ref<Object> dash_length = dash_seq->GetItem(i * 2);
      Ref<Object> gap_length = dash_seq->GetItem(i * 2 + 1);
      dash.push_back
	(std::pair<double, double>
	 (dash_length->FloatAsDouble(), gap_length->FloatAsDouble()));
    }
  }
  self->renderer_.setDash(dash);

  return 0;
}
catch (Exception) {
  return -1;
}


PyObject*
get_event_function(PyX11Window* self,
		   void* /* cookie */)
try {
  RETURN_OBJ_REF(self->event_function_);
}
catch (Exception) {
  return NULL;
}


int
set_event_function(PyX11Window* self,
		   Object* value,
		   void* /* cookie */)
try {
  // Make sure it's callable.
  if (! Callable::Check(value))
    throw Exception(PyExc_ValueError, "event function must be callable");
  self->event_function_ = newRef(value);
  return 0;
}
catch (Exception) {
  return -1;
}


int
set_font(PyX11Window* self,
	 Object* value,
	 void* /* cookie */)
try {
  const char* font_path;
  double size;
  Tuple* args = cast<Tuple>(value);
  double oblique_shear;
  args->ParseTuple("sdd", &font_path, &size, &oblique_shear);

  try {
    DisplayLock lock;
    self->renderer_.setFont(font_path, size, oblique_shear);
  }
  catch (FontLoadError) {
    throw Exception
      (PyExc_RuntimeError, "could not load font '%s'", font_path);
  }
  catch (FontEncodingError) {
    throw Exception(PyExc_RuntimeError, 
		    "could not set Unicode encoding for font '%s'", 
		    font_path);
  }

  return 0;
}
catch (Exception) {
  return -1;
}


PyObject*
get_height(PyX11Window* self,
	   void* /* cookie */)
try {
  return Int::FromLong(self->renderer_.getHeight());
}
catch (Exception) {
  return NULL;
}


PyObject*
get_idle_interval(PyX11Window* self,
		  void* /* cookie */)
try {
  if (self->idle_interval_ < 0)
    RETURN_NONE;
  else
    return Float::FromDouble(self->idle_interval_);
}
catch (Exception) {
  return NULL;
}


int
set_idle_interval(PyX11Window* self,
		  Object* value,
		  void* /* cookie */)
try {
  if (value == Py_None)
    self->idle_interval_ = -1;
  else {
    self->idle_interval_ = value->FloatAsDouble();
    self->last_idle_time_ = getCurrentTime();
  }

  return 0;
}
catch (Exception) {
  return -1;
}


PyObject*
get_is_destroyed(PyX11Window* self,
		 void* /* cookie */)
try {
  return newBool(self->is_destroyed_);
}
catch (Exception) {
  return NULL;
}


int
set_thickness(PyX11Window* self,
	      Object* value,
	      void* /* cookie */)
try {
  self->renderer_.setThickness(value->FloatAsDouble());
  return 0;
}
catch (Exception) {
  return -1;
}


int
set_title(PyX11Window* self,
	  Object* value,
	  void* /* cookie */)
try {
  Ref<String> title = value->Str();
  XStoreName(X->display, self->window_, title->AsString());
  XSetIconName(X->display, self->window_, title->AsString());
  return 0;
}
catch (Exception) {
  return -1;
}


PyObject*
get_width(PyX11Window* self,
	  void* /* cookie */)
try {
  return Int::FromLong(self->renderer_.getWidth());
}
catch (Exception) {
  return NULL;
}


struct PyGetSetDef
tp_getset[] = {
  { "color", NULL, (setter) set_color, NULL, NULL },
  { "dash", NULL, (setter) set_dash, NULL, NULL },
  { "event_function", (getter) get_event_function, 
    (setter) set_event_function, NULL, NULL },
  { "font", NULL, (setter) set_font, NULL, NULL },
  { "height", (getter) get_height, NULL, NULL, NULL },
  { "idle_interval", (getter) get_idle_interval, 
    (setter) set_idle_interval, NULL, NULL },
  { "is_destroyed", (getter) get_is_destroyed, NULL, NULL, NULL },
  { "thickness", NULL, (setter) set_thickness, NULL, NULL },
  { "title", NULL, (setter) set_title, NULL, NULL },
  { "width", (getter) get_width, NULL, NULL, NULL },
  { NULL, NULL, NULL, NULL, NULL },
};


}  // anonymous namespace


PyTypeObject
PyX11Window::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "X11Window",                          // tp_name
  sizeof(PyX11Window),                  // tp_size
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
function_X11_initialize(PyObject* /* cookie */,
			Arg* args)
try {
  // Parse arguments.
  Object* display_arg = None;
  args->ParseTuple("|O", &display_arg);
  // Check arguments.
  Ref<String> display_str;
  const char* display_name;
  if (display_arg == None)
    // If the display argument is omitted or 'None', use NULL, to obtain
    // the default X11 display.
    display_name = NULL;
  else {
    // Use the specified display string.
    display_str = display_arg->Str();
    display_name = display_str->AsString();
  }

  initializeX11(display_name);
  initializeEventThread();

  // All done.
  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
function_X11_getScreenSize(PyObject* /* cookie */,
			   Arg* args)
try {
  args->ParseTuple("");

  if (X == NULL) 
    throw Exception(PyExc_RuntimeError, 
		    "X11 display has not been initialized");

  DisplayLock lock;

  return buildValue
    ("(ii)(ff)", 
     DisplayWidth(X->display, X->screen_number),
     DisplayHeight(X->display, X->screen_number),
     0.001 * DisplayWidthMM(X->display, X->screen_number),
     0.001 * DisplayHeightMM(X->display, X->screen_number));     
}
catch (Exception) {
  return NULL;
}


//----------------------------------------------------------------------
// functions
//----------------------------------------------------------------------

Display*
initializeX11(const char* display_name)
{
  // Are we already initialized?
  if (X != NULL) 
    // Looks like we are.  Nothing to do.
    return X->display;

  DisplayLock lock;

  // Open the display.
  Display* display = XOpenDisplay(display_name);
  if (display == NULL)
    throw Exception(PyExc_RuntimeError, "could open X display '%s'", 
		    XDisplayName(display_name));
  // Construct information about this display.
  try {
    X = new XInfo(display);
  }
  catch (...) {
    // It failed.  Clean up.
    XCloseDisplay(display);
    throw;
  }

  return display;
}


