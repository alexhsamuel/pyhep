/****************************************************************
* X11/Xlib.h
*****************************************************************/
#ifndef G__XLIB_H
#define G__XLIB_H

/* NOTE: xlib.dll is not generated by default. 
 * Goto $CINTSYSDIR/lib/xlib directory and do 'sh setup' if you use UNIX. */
#ifndef G__XLIBDLL_H
#pragma include_noerr "X11/xlib.dll"
#endif

#ifndef __MAKECINT__
#pragma ifndef G__XLIBDLL_H /* G__XLIBDLL_H is defined in pthread.dll */
#pragma message Note: X11/xlib.dll is not found. Do 'sh setup' in $CINTSYSDIR/lib/xlib directory if you use UNIX.
#pragma endif
#endif

#endif
