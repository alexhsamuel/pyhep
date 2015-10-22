//----------------------------------------------------------------------
//
// cernlib.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* C++ Declarations of CERNLIB functions, and related utilities.  */

#ifndef __CERNLIB_HH__
#define __CERNLIB_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <string>

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

#define PAWC_SIZE 4000000

//----------------------------------------------------------------------
// types
//----------------------------------------------------------------------

// Minuit callback function FCN(NPAR,GRAD,FVAL,XVAL,IFLAG,FUTIL).
typedef void 
(*mnfcn_t)(const int*, double*, double*, const double*, const int*, void*);


//----------------------------------------------------------------------
// function declarations
//----------------------------------------------------------------------

extern "C" {

// This is the common block which HBOOK uses as working space.
extern int pawc_[PAWC_SIZE];

// Function defined in cernlib.F.
extern void close_lun__(int* lun);
extern void hbook_init__();
extern void hfnoent_(int* idd, int* numb);
extern void open_lun__(const int* lun, const char* path, int* status, 
		       int len_path);

}  // extern "C"

//----------------------------------------------------------------------
// inline function definitions
//----------------------------------------------------------------------

/* Extract a string from a Fortran character buffer.

   'str' -- A whitespace-padded Fortran character buffer.

   'str_len' -- The length of the buffer.

   returns -- The string contents of the buffer, without any trailing
   whitespace. 
*/
inline std::string
stringFromFortran(const char* str,
		  size_t str_len)
{
  // Scan backwards, looking for non-spaces.
  for (const char* p = str + str_len - 1; p >= str; --p)
    // Found a non-space character.  The string extends up to here.
    if (*p != ' ')
      return std::string(str, p - str + 1);

  // The buffer is filled with spaces.  It's an empty string.
  return std::string("");
}


/* Fill a Fortran character buffer from a string.

   'source' -- The string with which to fill the buffer.

   'str' -- The character buffer.

   'str_length' -- The size of 'str'.

   If the length of 'source' exceeds 'str_length', it is truncated.
*/
inline void
makeFortranString(const std::string& source,
		  char* str,
		  size_t str_length)
{
  // Copy from the source into the buffer, truncating if necessary.
  size_t source_length = source.length();
  strncpy(str, source.c_str(), 
	  (source_length < str_length) ? source_length : str_length);
  // Right-pad the string with spaces, if it does not fill the buffer.
  if (source_length < str_length) 
    memset(str + source_length, ' ', str_length - source_length);
}


//----------------------------------------------------------------------
// cernlib Fortran functions
//----------------------------------------------------------------------

extern "C" {

extern void     dadmul_        (double (*f)(const int*, const double*),
				const int* n,
				const double* a,
				const double* b,
				const int* minpts,
				const int* maxptx,
				const double* eps,
				double* wk,
				const int* iwk,
				double* result,
				double* relerr,
				int* nfnevl,
				int* ifail);
extern double   dgauss_        (double (*f)(const double*), 
				const double* a, 
				const double* b, 
				const double* eps);
extern void     dinv_          (const int* n,
				double* a,
				const int* idim,
				int* ir,
				int* ifail);
extern void     hbarx_         (const int* id);
extern void     hbnamc_        (const int* id,
				const char* chblok,
				void* variable,
				const char* chform,
				int len_chblok,
				int len_chform);
extern void     hbname_        (const int* id,
				const char* chblok,
				void* variable,
				const char* chform,
				int len_chblok,
				int len_chform);
extern void     hbnt_          (const int* id,
				const char* chtitl,
				const char* chopt,
				int len_chtitl,
				int len_chopt);
extern void     hbook1_        (const int* id,
				const char* chtitl,
				const int* nx,
				const float* xmi,
				const float* xma,
				const float* vmx,
				int len_chtitl);
extern void     hbook2_        (const int* id,
				const char* chtitl,
				const int* nx,
				const float* xmi,
				const float* xma,
				const int* ny,
				const float* ymi,
				const float* yma,
				const float* vmx,
				int len_chtitl);
extern void     hbookn_        (const int* id,
				const char* chtitl,
				const int* nvar,
				const char* chrzpa,
				const int* nwbuff,
				const char* chtags,
				int len_chtitl,
				int len_chrzpa,
				int len_chtags);
extern int      hcbits_[37];
extern int      hcbook_[51];
extern void     hcdir_         (const char* chpath,
				const char* chopt, 
				int len_chpath,
				int len_chopt); 
extern void     hdcofl_        ();
extern void     hddir_         (const char* chpath,
				int len_chpath);
extern void     hdelet_        (const int* id);
extern void     hf1_           (const int* id,
				const float* x,
				const float* weight);
extern void     hfcxy_         (const int* icx,
				const int* icy,
				const float* x);
extern void     hfn_           (const int* id, 
				const char* x);
extern void     hfnt_          (const int* id);
extern void     hgive_         (const int* id,
				char* chtitl,
				int* nx,
				float* xmi,
				float* xma,
				int* ny,
				float* ymi,
				float* yma,
				int* nwt,
				void** loc,
				int len_chtitl);
extern void     hgiven_        (const int* id,
				char* chtitl,
				int* nvar,
				char* chtag,
				float* rlow,
				float* rhigh,
				int len_chtitl,
				int len_chtag);
extern void     hgnf_          (const int* id,
				const int* idnevt,
				char* x,
				int* ierror);
extern void     hgnpar_        (const int* id,
				const char* chrout,
				int len_chrout);
extern void     hgnt_          (const int* id,
				const int* idnevt,
				int* ierr);
extern void     hgntf_         (const int* id,
				const int* irow,
				int* ierr);
extern void     hgntv_         (const int* id,
				const char* chvar,
				const int* nvar,
				const int* irow,
				int* ierr,
				int len_chvar);
extern float    hi_            (const int* id,
				const int* i);
extern float    hij_           (const int* id,
				const int* i,
				const int* j);
extern float    hije_          (const int* id,
				const int* i,
				const int* j);
extern void     hkind_         (const int* id,
				int* kind,
				const char* chopt,
				int len_chopt);
extern void     hlnext_        (int* idh,
				char* chtype,
				char* chtitl,
				const char* chopt,
				int len_chtype,
				int len_chtitl,
				int len_chopt);
extern void     hmdir_         (const char* chpath,
				const char* chopt,
				int len_chpath,
				int len_chopt);
extern void     hnoent_        (const int* id,
				int* noent);
extern bool     hntnew_        (const int* id);
extern void     hntvdef_       (const int* id1,
				const int* ivar,
				char* chtag,
				char* block,
				int* itype,
				int len_chtag,
				int len_block);
extern void     hpak_          (const int* id,
				float* conten);
extern void     hpake_         (const int* id,
				float* conten);
extern void     hrdir_         (const int* maxdir,
				char** chdir,
				int* ndir,
				int len_chdir);
extern void     hrend_         (const char* chopt,
				int len_chopt);
extern void     hrin_          (int* id,
				int* icycle,
				int* iofset);
extern void     hropen_        (const int* lun, 
				const char* chtop,
				const char* chfile, 
				const char* chopt, 
				int* lrec, 
				int* istat, 
				int len_chtop, 
				int len_chfile,
				int len_chopt);
extern void     hrout_         (const int* id, 
				int* icycle,
				const char* chopt,
				int len_chopt);
extern void     hscr_          (const int* id,
				const int* icycle,
				const char* chopt,
				int len_chopt);
extern void     hunpak_        (const int* id,
				float* conten,
				const char* choice,
				int* num,
				int len_choice);
extern void     hunpke_        (const int* id,
				float* conten,
				const char* choice,
				int* num,
				int len_choice);
extern void     mncomd_        (mnfcn_t fcn, 
				const char* chstr, 
				int* icondn,
				void* futil, 
				int len_chstr);
extern void     mnemat_        (double* emat,
				const int* ndim);
extern void     mnerrs_        (const int* num,
				double* eplus,
				double* eminus,
				double* eparab,
				double* globcc);
extern void     mninit_        (const int* ird, 
				const int* iwr, 
				const int* isav);
extern void     mnparm_        (const int* num, 
				const char* chnam, 
				const double* stval, 
				const double* step, 
				const double* bnd1, 
				const double* bnd2, 
				int* ierflg, 
				int len_chnam);
extern void     mnpout_        (const int* num,
				char* chnam,
				double* val,
				double* error,
				double* bnd1,
				double* bnd2,
				int* ivarbl,
				int len_chnam);
extern void     mnstat_        (double* fmin,
				double* fedm,
				double* errdef,
				int* npari,
				int* nparx,
				int* istat);
extern float    prob_          (float* x,
				int* n);
extern int      quest_[100];
extern int      rzcl_[11];
extern void     rzlogl_        (const int* lun,
				const int* loglev);
extern void     rzpurg_        (const int* nkeep);
extern void     rzvout_        (const int* vect, 
				const int* nout, 
				const int* key,
				int* icycle, 
				const char* chopt, 
				int len_chopt);

}  // extern "C"

//----------------------------------------------------------------------

#endif  // #ifndef __CERNLIB_HH__
