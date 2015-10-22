//----------------------------------------------------------------------
//
// PyImageFile.cc
//
// Copyright 2005 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <Imlib.h>

#include "PyX11Window.hh"
#include "PyImageFile.hh"

using namespace Py;

//----------------------------------------------------------------------
// method definitions
//----------------------------------------------------------------------

PyImageFile::PyImageFile(int width,
			 int height)
  : renderer_(width, height)
{
  renderer_.resize(width, height);
}


PyImageFile::~PyImageFile()
{
}


//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

namespace {

static ImlibData*
getImlib()
{
  // Unfortunately, Imlib needs an X display to initialize itself.
  static ImlibData* imlib_data;

  if (imlib_data == NULL) {
    imlib_data = Imlib_init(initializeX11());
    if (imlib_data == NULL)
      throw Exception(PyExc_RuntimeError, "could not initialize Imlib");
  }

  return imlib_data;
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


//----------------------------------------------------------------------
// function definitions
//----------------------------------------------------------------------

PyObject* 
tp_new(PyTypeObject* type,
       Arg* args,
       Dict* kw_args)
try {
  int width;
  int height;
  args->ParseTuple("ii", &width, &height);
  // Check arguments.
  if (width < 1 || height < 1)
    throw Exception(PyExc_ValueError, "width and height must be postive");

  // Construct the object.
  return PyImageFile::New(width, height);
}
catch (Exception) {
  return NULL;
}


void
tp_dealloc(PyImageFile* self)
try {
  // Perform C++ deallocation.
  self->~PyImageFile();
  // Free memory for the Python object.
  PyMem_DEL(self);
}
catch (Exception) {
}


PyObject*
method_drawCircle(PyImageFile* self, 
		  Arg* args)
try {
  double x, y, r;
  Object* fill_arg;
  args->ParseTuple("dddO", &x, &y, &r, &fill_arg);
  bool fill = fill_arg->IsTrue();

  self->renderer_.drawCircle(Point(x, y), r, fill);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_drawLine(PyImageFile* self, 
		Arg* args)
try {
  Object* points_arg;
  args->ParseTuple("O", &points_arg);
  // Parse the points in the line.
  PointList points;
  parsePoints(points_arg, points);

  self->renderer_.drawLine(points);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_drawPolygon(PyImageFile* self, 
		   Arg* args)
try {
  Object* points_arg;
  args->ParseTuple("O", &points_arg);
  // Parse the points in the polygon.
  PointList points;
  parsePoints(points_arg, points);

  self->renderer_.drawPolygon(points);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
method_drawText(PyImageFile* self,
		Arg* args)
try {
  Point point;
  PyUnicodeObject* text_arg;
  args->ParseTuple("ddU", &point.x, &point.y, &text_arg);
  wchar_t text[text_arg->length];
  int len_text = PyUnicode_AsWideChar(text_arg, text, text_arg->length);
  assert(len_text == text_arg->length);

  try {
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
method_save(PyImageFile* self,
	    Arg* args)
{
  char* path;
  args->ParseTuple("s", &path);
  
  ImlibData* imlib_data = getImlib();
  char* image_buffer = self->renderer_.getImageBuffer(PIXELFORMAT_rgb24);
  try {
    ImlibImage* image = Imlib_create_image_from_data
      (imlib_data, (unsigned char*) image_buffer, NULL, 
       self->renderer_.getWidth(), self->renderer_.getHeight());
    if (image == NULL)
      throw Exception(PyExc_RuntimeError, 
		      "could not create image (Imlib_create_image_from_data)");
    if (! Imlib_save_image(imlib_data, image, path, NULL)) 
      throw Exception(PyExc_RuntimeError, 
		      "could not save image (Imlib_save_image)");
    Imlib_destroy_image(imlib_data, image);
  }
  catch (...) {
    delete[] image_buffer;
    throw;
  }

  delete[] image_buffer;

  RETURN_NONE;
}


PyMethodDef
tp_methods[] = {
  { "drawCircle", (PyCFunction) method_drawCircle, METH_VARARGS, NULL },
  { "drawLine", (PyCFunction) method_drawLine, METH_VARARGS, NULL },
  { "drawPolygon", (PyCFunction) method_drawPolygon, METH_VARARGS, NULL },
  { "drawText", (PyCFunction) method_drawText, METH_VARARGS, NULL },
  { "save", (PyCFunction) method_save, METH_VARARGS, NULL },
  { NULL, NULL, 0, NULL }
};


int
set_color(PyImageFile* self,
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

  self->renderer_.setColor(Color(r, g, b));

  return 0;
}
catch (Exception) {
  return -1;
}


int
set_dash(PyImageFile* self,
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


int
set_font(PyImageFile* self,
	 Object* value,
	 void* /* cookie */)
try {
  const char* font_path;
  double size;
  Tuple* args = cast<Tuple>(value);
  double oblique_shear;
  args->ParseTuple("sdd", &font_path, &size, &oblique_shear);

  try {
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


int
set_thickness(PyImageFile* self,
	      Object* value,
	      void* /* cookie */)
try {
  self->renderer_.setThickness(value->FloatAsDouble());
  return 0;
}
catch (Exception) {
  return -1;
}


struct PyGetSetDef
tp_getset[] = {
  { "color", NULL, (setter) set_color, NULL, NULL },
  { "dash", NULL, (setter) set_dash, NULL, NULL },
  { "font", NULL, (setter) set_font, NULL, NULL },
  { "thickness", NULL, (setter) set_thickness, NULL, NULL },
  { NULL, NULL, NULL, NULL, NULL },
};


}  // anonymous namespace


PyTypeObject
PyImageFile::type = {
  PyObject_HEAD_INIT(&PyType_Type)
  0,                                    // ob_size
  "ImageFile",                          // tp_name
  sizeof(PyImageFile),                  // tp_size
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


