//----------------------------------------------------------------------
//
// ext.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Python interface to CERN Program Library (CERNLIB) functions.

   This module provides a straightforward Python interface to many of
   the functions in the CERNLIB library.  So far, no effort has been
   made to convert all entry points in the library wholesale; instead,
   calls are added on an as-needed basis.

   Data structures and calling conventions are adjusted only as
   necessary to make these Fortran calls accessible from Python.  In
   general, we follow these rules when writing a wrapper for a CERNLIB
   call.  Since the conversion is generally mechanical, documentation
   for the calls is generally not included here.  See the CERNLIB manual
   for instructions on using the calls.  (A few functions deviate from
   these rules; these are noted individually.)

     - The Python function name in this module is the same as the
       CERNLIB function name (in lower-case).

     - The arguments to the Python function are the same as those of the
       CERNLIB function, excluding output-only arguments.  (In the
       CERNLIB manual, an output-only argument is indicated with a
       trailing asterisk.)  They have the same names (in lower-case) and
       appear in the same order. 

     - Python ints, floats, and strings are used for Fortran integers,
       reals, and character arrays, respectively.

     - If a CERNLIB procedure has no output or input-output arguments,
       the corresponding Python function returns 'None'.  (In the
       CERNLIB manual, an input-output argument is indicated with a
       leading and a trailing asterisk.)

     - If a CERNLIB procedure has a single output or input-output
       argument, the corresponding Python function returns the value of
       this argument after the call.

     - If a CERNLIB procedure has more than one output and input-output
       arguments, the corresponding Python function returns a tuple
       containing the values of these arguments.

     - Whitespace is trimmed from the right side of output strings
       (because Fortran character arrays are fixed-length and padded on
       the right with spaces).

     - The value of an output or input-output array argument is
       converted to a Python list when returned.

     - Where memory addresses appear as arguments or return values, they
       are represented as Python integers.

   In addition to CERNLIB calls, this module includes the following:

     - The 'close' function wraps the Fortran built-in 'close'
       function.  Its argument is the logical unit number to close.
*/

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <algorithm>
#include <iostream>
#include <pthread.h>

#include "cernlib.hh"
#include "hbook.hh"
#include "minuit.hh"
#include "python.hh"
#include "util.hh"

using namespace Py;

//----------------------------------------------------------------------
// configuration
//----------------------------------------------------------------------

namespace {

// Set 'trace' to 'true' to enable call tracing.
const bool trace = false;
// Trace messages are written to the 'traceout' stream.
std::ostream& traceout = std::cout;

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

/* Trim trailing spaces and NUL-terminate in place a character array.  

   If the last character is non-blank, it is replaced by NUL.  */

void
terminateCharArray(char* str,
		   int length)
{
  // Start one back from the end.
  --length;
  // Scan back from the end of the string, looking for the first
  // non-blank character.
  while (length > 0 && str[length - 1] == ' ')
    --length;
  // NUL-terminate the string.
  str[length] = '\0';
}
  

/* Construct a Python string from a Fortran character array.

   Blank spaces at the end are stripped from the string.  The string is
   not NUL-terminated.
 
   'str' -- The character array.

   'len' -- The length of the character array.

   returns -- A Python string object, or 'NULL' if allocation fails.
*/
   
String*
pyStringFromFortran(const char* str,
		    int len)
{
  // Scan back from the end of the string, looking for the first
  // non-space character.
  while (len > 0 && str[len - 1] == ' ')
    --len;
  // Construct the string.
  return String::FromStringAndSize(str, len);
}


//----------------------------------------------------------------------
// wrappers for CERLIB entries
//----------------------------------------------------------------------

PyObject*
py_close(PyObject* /* self */,
	 Arg* args)
try {
  int lun;
  args->ParseTuple("i", &lun);

  if (trace)
    traceout << "CLOSE(" << lun << ")" << std::endl;

  close_lun__(&lun);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_dgauss(PyObject* /* self */,
	  Arg* args)
try {
  Object* function_arg;
  String* var_name;
  double lo;
  double hi;
  double accuracy = 1e-8;
  args->ParseTuple("OSdd|d", &function_arg, &var_name, &lo, &hi, 
		   &accuracy);

  double result = 
    dgauss(cast<Callable>(function_arg), var_name, lo, hi, accuracy);
  return Float::FromDouble(result);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hbarx(PyObject* /* self */,
	 Arg* args)
try {
  int id;
  args->ParseTuple("i", &id);
  
  hbarx_(&id);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


/* The 'variable' argument to 'hbname' is the pointer to the first
   element in the array of variables to and from which ntuple values are
   written and read.  */

PyObject*
py_hbname(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  char* chblok;
  int len_chblok;
  int variable;
  char* chform;
  int len_chform;
  args->ParseTuple("is#is#", &id, &chblok, &len_chblok, &variable, 
		   &chform, &len_chform);

  if (trace)
    traceout << "HBNAME(" << id << ", '" << chblok << "', " 
	     << (void*) variable << ", '" << chform << "')" << std::endl;

  hbname_(&id, chblok, (void*) variable, chform, len_chblok, len_chform);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hbook1(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  const char* chtitl;
  int len_chtitl;
  int nx;
  float xmi;
  float xma;
  float vmx;
  args->ParseTuple("is#ifff", &id, &chtitl, &len_chtitl, &nx, &xmi, 
		   &xma, &vmx);

  if (trace)
    traceout << "HBOOK1(" << id << ",' " << chtitl << "', "
	     << nx << ", " << xmi << ", " << xma << ", " 
	     << vmx << ")" << std::endl;

  hbook1_(&id, chtitl, &nx, &xmi, &xma, &vmx, len_chtitl);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hbook2(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  const char* chtitl;
  int len_chtitl;
  int nx;
  float xmi;
  float xma;
  int ny;
  float ymi;
  float yma;
  float vmx;
  args->ParseTuple("is#iffifff", &id, &chtitl, &len_chtitl, &nx, &xmi, 
		   &xma, &ny, &ymi, &yma, &vmx);

  if (trace)
    traceout << "HBOOK2(" << id << ",' " << chtitl << "', "
	     << nx << ", " << xmi << ", " << xma << ", " 
	     << ny << ", " << ymi << ", " << yma << ", " 
	     << vmx << ")" << std::endl;

  hbook2_(&id, chtitl, &nx, &xmi, &xma, &ny, &ymi, &yma, &vmx, len_chtitl);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hcdir(PyObject* /* self */,
	 Arg* args)
try {
  const char* chpath;
  int len_chpath;
  const char* chopt;
  int len_chopt;
  args->ParseTuple("s#s#", &chpath, &len_chpath, &chopt, &len_chopt);

  if (chopt[0] == 'R') {
    // With this option, 'chpath' is an output argument.  Use a large
    // temporary buffer to receive the output string.
    char path_buffer[1024];
    hcdir_(path_buffer, chopt, sizeof(path_buffer), len_chopt);

    return pyStringFromFortran(path_buffer, sizeof(path_buffer));
  }
  else {
    hcdir_(chpath, chopt, len_chpath, len_chopt);
    if (quest_[0] != 0)
      throw Exception(PyExc_IOError, "could not change to directory '%s'", 
		      chpath);

    return String::FromStringAndSize(chpath, len_chpath);
  }
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hdelet(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  args->ParseTuple("i", &id);

  hdelet_(&id);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hddir(PyObject* /* self */,
	 Arg* args)
try {
  char* chpath;
  args->ParseTuple("s", &chpath);

  hddir_(chpath, strlen(chpath));

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hf1(PyObject* /* self */,
       Arg* args)
try {
  int id;
  float x;
  float weight;
  args->ParseTuple("iff", &id, &x, &weight);

  hf1_(&id, &x, &weight);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hfcxy(PyObject* /* self */,
	 Arg* args)
try {
  int icx;
  int icy;
  float x;
  args->ParseTuple("iif", &icx, &icy, &x);

  hfcxy_(&icx, &icy, &x);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hfnoent(PyObject* /* self */,
	   Arg* args)
try {
  int idd;
  int numb;
  args->ParseTuple("ii", &idd, &numb);

  hfnoent_(&idd, &numb);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hgive(PyObject* /* self */,
	 Arg* args)
{
  int id;
  args->ParseTuple("i", &id);
  
  char chtitl[81];
  int nx, ny, nwt;
  float xmi, xma, ymi, yma;
  void* loc;
  hgive_(&id, chtitl, &nx, &xmi, &xma, &ny, &ymi, &yma, &nwt, &loc, 
	 sizeof(chtitl) - 1);
  terminateCharArray(chtitl, sizeof(chtitl));
  return buildValue("siffiffi", chtitl, nx, xmi, xma, ny, ymi, yma, loc);
} 


PyObject*
py_hgiven(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  int nvar;
  args->ParseTuple("ii", &id, &nvar);
  int nvar_alloc = nvar;

  char chtitl[129];
  const int len_tag = 80;
  char chtag[len_tag * nvar_alloc];
  float rlow[nvar_alloc];
  float rhigh[nvar_alloc];
  hgiven_(&id, chtitl, &nvar, chtag, rlow, rhigh, sizeof(chtitl) - 1, len_tag);
  int num_results = std::min(nvar, nvar_alloc);
  terminateCharArray(chtitl, sizeof(chtitl));

  Ref<Tuple> names = Tuple::New(num_results);
  Ref<Tuple> mins = Tuple::New(num_results);
  Ref<Tuple> maxs = Tuple::New(num_results);
  for (int i = 0; i < num_results; ++i) {
    names->InitializeItem
      (i, pyStringFromFortran(&chtag[i * len_tag], len_tag));
    Ref<Float> lo = Float::FromDouble(rlow[i]);
    mins->InitializeItem(i, lo);
    Ref<Float> hi = Float::FromDouble(rhigh[i]);
    maxs->InitializeItem(i, hi);
  }
  return buildValue("siOOO", chtitl, nvar, 
		    (Object*) names, (Object*) mins, (Object*) maxs);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hgntf(PyObject* /* self */,
	 Arg* args)
try {
  int id;
  int irow;
  args->ParseTuple("ii", &id, &irow);

  if (trace)
    traceout << "HGNTF(" << id << ", " << irow << ")";

  int ierr;
  hgntf_(&id, &irow, &ierr);
  
  if (trace)
    traceout << " = " << ierr << std::endl;

  return Int::FromLong(ierr);
}
catch (Exception) {
  return NULL;
}


/* The 'chvar' and 'nvar' arguments to the CERNLIB 'hgntv' function are
   represented by a single Python list, whose elements must all be
   strings (the names of the variables whose values are to be
   retrieved).  The 'chvar' array is constructed automatically.  */

PyObject*
py_hgntv(PyObject* /* self */,
	 Arg* args)
try {
  int id;
  PyObject* chvar_arg;
  int irow;
  args->ParseTuple("iOi", &id, &chvar_arg, &irow);
  Sequence* chvar_seq = cast<Sequence>(chvar_arg);

  int nvar = chvar_seq->Size();
  int len_chvar = 0;
  // Find the length of the longest string in the list.  Each character
  // array in the Fortran array 'chvar' must be the same length.
  for (int i = 0; i < nvar; ++i) {
    Ref<Object> item = chvar_seq->GetItem(i);
    Ref<String> item_str = item->Str();
    int len = item_str->Size();
    if (len > len_chvar)
      len_chvar = len;
  }
  // Construct the Fortran array.
  char chvar[nvar * len_chvar + 1];
  // Clean it out with blanks.
  memset(chvar, ' ', nvar * len_chvar);
  // NUL-terminate it, so we can print it out as a C string if
  // necessary. 
  chvar[nvar * len_chvar] = '\0';
  // Copy the input strings into the array.
  for (int i = 0; i < nvar; ++i) {
    Ref<Object> item = chvar_seq->GetItem(i);
    Ref<String> item_str = item->Str();
    memcpy(chvar + i * len_chvar, 
	   item_str->AsString(), item_str->Size());
  }

  if (trace)
    traceout << "HGNTV(" << id << ", '" << chvar << "', " << nvar 
	     << ", " << irow << ")";

  int ierr;
  hgntv_(&id, chvar, &nvar, &irow, &ierr, len_chvar);

  if (trace)
    traceout << " = " << ierr << std::endl;
  
  return Int::FromLong(ierr);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hi(PyObject* /* self */,
      Arg* args)
try {
  int id;
  int i;
  args->ParseTuple("ii", &id, &i);
  
  float value = hi_(&id, &i);
  
  return Float::FromDouble(value);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hij(PyObject* /* self */,
       Arg* args)
try {
  int id;
  int i;
  int j;
  args->ParseTuple("iii", &id, &i, &j);
  
  float value = hij_(&id, &i, &j);

  return Float::FromDouble(value);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hije(PyObject* /* self */,
	Arg* args)
try {
  int id;
  int i;
  int j;
  args->ParseTuple("iii", &id, &i, &j);
  
  float value = hije_(&id, &i, &j);

  return Float::FromDouble(value);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hkind(PyObject* /* self */,
	 Arg* args)
try {
  int id;
  const char* chopt = " ";
  args->ParseTuple("i|s", &id, &chopt);
  
  int kind;
  hkind_(&id, &kind, chopt, strlen(chopt));

  return Int::FromLong(kind);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hlnext(PyObject* /* self */,
	  Arg* args)
try {
  int idh;
  char* chopt;
  int len_chopt;
  args->ParseTuple("is#", &idh, &chopt, &len_chopt);

  char chtype[1] = "";
  char chtitl[129] = "";
  hlnext_(&idh, chtype, chtitl, chopt, sizeof(chtype), 
	  sizeof(chtitl) - 1, len_chopt);
  
  if (idh == 0) 
    // HBOOK does not fill in chtype and chtitl if idh is zero.
    return buildValue("iOO", idh, None, None);
  else {
    terminateCharArray(chtitl, sizeof(chtitl));
    return buildValue("ics", idh, chtype[0], chtitl);
  }
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hmdir(PyObject* /* self */,
	 Arg* args)
try {
  const char* chpath;
  int len_chpath;
  const char* chopt;
  int len_chopt;
  args->ParseTuple("s#s#", &chpath, &len_chpath, &chopt, &len_chopt);

  hmdir_(chpath, chopt, len_chpath, len_chopt);
  if (quest_[0] != 0)
    throw Exception(PyExc_IOError, 
		    "could not create directory '%s'", chpath);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hnoent(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  args->ParseTuple("i", &id);

  int noent;
  hnoent_(&id, &noent);

  return Int::FromLong(noent);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hntvdef(PyObject* /* self */,
	   Arg* args)
try {
  int id;
  int ivar;
  args->ParseTuple("ii", &id, &ivar);

  char chtag[129];
  char block[129];
  int itype;
  hntvdef_(&id, &ivar, chtag, block, &itype, 
	   sizeof(chtag) - 1, sizeof(block) - 1);
  terminateCharArray(chtag, sizeof(chtag));
  terminateCharArray(block, sizeof(block));

  return buildValue("ssi", chtag, block, itype);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hpak(PyObject* /* self */,
	Arg* args)
try {
  int id;
  int conten;
  args->ParseTuple("ii", &id, &conten);

  if (trace)
    traceout << "HPAK(" << id << ", " << (void*) conten << ")" << std::endl;

  hpak_(&id, (float*) conten);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hpake(PyObject* /* self */,
	 Arg* args)
try {
  int id;
  int conten;
  args->ParseTuple("ii", &id, &conten);

  if (trace)
    traceout << "HPAK(" << id << ", " << (void*) conten << ")" << std::endl;

  hpake_(&id, (float*) conten);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hrend(PyObject* /* self */,
	 Arg* args)
try {
  const char* chtop;
  int len_chtop;
  args->ParseTuple("s#", &chtop, &len_chtop);

  hrend_(chtop, len_chtop);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hrin(PyObject* /* self */,
	Arg* args)
try {
  int id;
  int icycle;
  int iofset;
  args->ParseTuple("iii", &id, &icycle, &iofset);

  hrin_(&id, &icycle, &iofset);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hropen(PyObject* /* self */,
	  Arg* args)
try {
  int lun;
  const char* chtop;
  int len_chtop;
  const char* chfile;
  int len_chfile;
  const char* chopt;
  int len_chopt;
  int lrec;
  args->ParseTuple("is#s#s#i", &lun, &chtop, &len_chtop, &chfile, 
		   &len_chfile, &chopt, &len_chopt, &lrec);

  int istat;
  hropen_(&lun, chtop, chfile, chopt, &lrec, &istat, len_chtop,
	  len_chfile, len_chopt); 
  
  return buildValue("ii", istat, lrec);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hrout(PyObject* /* self */,
	 Arg* args)
try {
  int id;
  const char* chopt;
  int len_chopt;
  args->ParseTuple("is#", &id, &chopt, &len_chopt);

  int icycle;
  hrout_(&id, &icycle, chopt, len_chopt);
  
  return Int::FromLong(icycle);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hscr(PyObject* /* self */,
	Arg* args)
try {
  int id;
  int icycle;
  const char* chopt;
  args->ParseTuple("iis", &id, &icycle, &chopt);
  
  hscr_(&id, &icycle, chopt, strlen(chopt));

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}  


PyObject*
py_hunpak(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  const char* choice = " ";
  int num;
  int len_conten;
  args->ParseTuple("isii", &id, &choice, &num, &len_conten);
  if (len_conten <= 0)
    throw Exception(PyExc_ValueError, "invalid CONTEN length %d", 
		    len_conten);

  float conten[len_conten];
  hunpak_(&id, conten, choice, &num, strlen(choice));

  Ref<List> result = List::New(len_conten);
  for (int i = 0; i < len_conten; ++i) {
    Ref<Float> c = Float::FromDouble(conten[i]);
    result->InitializeItem(i, c);
  }
  return result.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
py_hunpke(PyObject* /* self */,
	  Arg* args)
try {
  int id;
  const char* choice = " ";
  int num;
  int len_conten;
  args->ParseTuple("isii", &id, &choice, &num, &len_conten);
  if (len_conten <= 0)
    throw Exception(PyExc_ValueError, "invalid CONTEN length %d", 
		    len_conten);

  float conten[len_conten];
  hunpke_(&id, conten, choice, &num, strlen(choice));

  Ref<List> result = List::New(len_conten);
  for (int i = 0; i < len_conten; ++i) {
    Ref<Float> c = Float::FromDouble(conten[i]);
    result->InitializeItem(i, c);
  }
  return result.release();
}
catch (Exception) {
  return NULL;
}


PyObject*
py_prob(PyObject* /* self */,
	Arg* args)
try {
  float x;
  int n;
  args->ParseTuple("fi", &x, &n);
  if (x < 0)
    throw Exception(PyExc_ValueError, "'x' may not be negative");
  if (n < 1)
    throw Exception(PyExc_ValueError, "'n' must be at least one");

  double p = prob_(&x, &n);
  
  return Float::FromDouble(p);
}
catch (Exception) {
  return NULL;
}


PyObject*
py_rzlogl(PyObject* /* self */,
	  Arg* args)
try {
  int lun;
  int loglev;
  args->ParseTuple("ii", &lun, &loglev);

  rzlogl_(&lun, &loglev);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


PyObject*
py_rzpurg(PyObject* /* self */,
	  Arg* args)
try {
  int nkeep;
  args->ParseTuple("i", &nkeep);
  
  rzpurg_(&nkeep);

  RETURN_NONE;
}
catch (Exception) {
  return NULL;
}


//----------------------------------------------------------------------

PyObject*
function_integrate(PyObject* /* self */,
		   Arg* args)
try {
  Object* function;
  Object* region_arg;
  double accuracy = 1e-8;
  args->ParseTuple("OO|d", &function, &region_arg, &accuracy);
  Sequence* region_seq = cast<Sequence>(region_arg);

  std::vector<IntegrationRange> region;
  for (int i = 0; i < region_seq->Size(); ++i) {
    Ref<Object> range_obj = region_seq->GetItem(i);
    Tuple* range = cast<Tuple>(range_obj);
    String* var_name;
    double lo;
    double hi;
    range->ParseTuple("Sdd", &var_name, &lo, &hi);
    region.push_back(IntegrationRange(var_name, lo, hi));
  }

  double result = integrate(cast<Callable>(function), region, accuracy);
  return Float::FromDouble(result);
}
catch (Exception) {
  return NULL;
}


//----------------------------------------------------------------------

PyMethodDef
functions[] = {
  { "close",    (PyCFunction) py_close,   METH_VARARGS, NULL },
  { "dgauss",   (PyCFunction) py_dgauss,  METH_VARARGS, NULL },
  { "hbarx",    (PyCFunction) py_hbarx,   METH_VARARGS, NULL },
  { "hbname",   (PyCFunction) py_hbname,  METH_VARARGS, NULL },
  { "hbook1",   (PyCFunction) py_hbook1,  METH_VARARGS, NULL },
  { "hbook2",   (PyCFunction) py_hbook2,  METH_VARARGS, NULL },
  { "hcdir",    (PyCFunction) py_hcdir,   METH_VARARGS, NULL },
  { "hddir",    (PyCFunction) py_hddir,   METH_VARARGS, NULL },
  { "hdelet",   (PyCFunction) py_hdelet,  METH_VARARGS, NULL },
  { "hf1",      (PyCFunction) py_hf1,     METH_VARARGS, NULL },
  { "hfcxy",    (PyCFunction) py_hfcxy,   METH_VARARGS, NULL },
  { "hfnoent",  (PyCFunction) py_hfnoent, METH_VARARGS, NULL },
  { "hgive",    (PyCFunction) py_hgive,   METH_VARARGS, NULL },
  { "hgiven",   (PyCFunction) py_hgiven,  METH_VARARGS, NULL },
  { "hgntf",    (PyCFunction) py_hgntf,   METH_VARARGS, NULL },
  { "hgntv",    (PyCFunction) py_hgntv,   METH_VARARGS, NULL },
  { "hi",       (PyCFunction) py_hi,      METH_VARARGS, NULL },
  { "hij",      (PyCFunction) py_hij,     METH_VARARGS, NULL },
  { "hije",     (PyCFunction) py_hije,    METH_VARARGS, NULL },
  { "hkind",    (PyCFunction) py_hkind,   METH_VARARGS, NULL },
  { "hlnext",   (PyCFunction) py_hlnext,  METH_VARARGS, NULL },
  { "hmdir",    (PyCFunction) py_hmdir,   METH_VARARGS, NULL },
  { "hnoent",   (PyCFunction) py_hnoent,  METH_VARARGS, NULL },
  { "hntvdef",  (PyCFunction) py_hntvdef, METH_VARARGS, NULL },
  { "hpak",     (PyCFunction) py_hpak,    METH_VARARGS, NULL },
  { "hpake",    (PyCFunction) py_hpake,   METH_VARARGS, NULL },
  { "hrend",    (PyCFunction) py_hrend,   METH_VARARGS, NULL },
  { "hrin",     (PyCFunction) py_hrin,    METH_VARARGS, NULL },
  { "hropen",   (PyCFunction) py_hropen,  METH_VARARGS, NULL },
  { "hrout",    (PyCFunction) py_hrout,   METH_VARARGS, NULL },
  { "hscr",     (PyCFunction) py_hscr,    METH_VARARGS, NULL },
  { "hunpak",   (PyCFunction) py_hunpak,  METH_VARARGS, NULL },
  { "hunpke",   (PyCFunction) py_hunpke,  METH_VARARGS, NULL },
  { "prob",     (PyCFunction) py_prob,    METH_VARARGS, NULL },
  { "rzpurg",   (PyCFunction) py_rzpurg,  METH_VARARGS, NULL },
  { "rzlogl",   (PyCFunction) py_rzlogl,  METH_VARARGS, NULL },

  { "createColumnWiseNtuple", 
    (PyCFunction) function_createColumnWiseNtuple, METH_VARARGS, NULL },
  { "createRowWiseNtuple", 
    (PyCFunction) function_createRowWiseNtuple, METH_VARARGS, NULL },
  { "integrate",
    (PyCFunction) function_integrate, METH_VARARGS, NULL },
  { "minuit_maximumLikelihoodFit",
    (PyCFunction) function_minuit_maximumLikelihoodFit, METH_VARARGS, NULL },
  { "minuit_minimize", 
    (PyCFunction) function_minuit_minimize, METH_VARARGS, NULL },
  { "openTuple", (PyCFunction) function_openTuple, METH_VARARGS, NULL },
  
  { NULL, NULL, 0, NULL }
};


PyTypeObject*
types[] = {
  NULL
};


}  // anonymous namespace


extern "C" {

void
initext()
try {
  Module::Initialize("ext", functions, types, "");
  hbook_init__();
}
catch (Exception) {
  std::cerr << "could not initialize module 'ext'" << std::endl;
}


}  // extern "C"
