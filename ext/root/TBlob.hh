//----------------------------------------------------------------------
//
// TBlob.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Root object to store arbitrary binary data.  */

#ifndef __TBLOB_HH__
#define __TBLOB_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include "TNamed.h"

//----------------------------------------------------------------------
// classes
//----------------------------------------------------------------------

class TBlob
  : public TNamed
{
public:

  TBlob();
  TBlob(const char* name, const char* title);
  virtual ~TBlob();

  /* Clear the data in the blob.  */
  void ClearData();

  /* Set the blob's data to 'length' bytes from 'data'.  */
  void SetData(const char* data, size_t length);

  /* Return the pointer to the buffer containing the blob's data.  

     Returns NULL if the length is zero.  */
  const char* GetData() const;

  /* Return the number of bytes of data.  */
  size_t GetLength() const;

private:

  // Guess what this stuff is.
  char* data_;
  size_t length_;

  // Root magic macro.
  ClassDef(TBlob, 1)

};


//----------------------------------------------------------------------

#endif  // #ifndef __TBLOB_HH__
