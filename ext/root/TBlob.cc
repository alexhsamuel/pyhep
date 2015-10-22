//----------------------------------------------------------------------
//
// TBlob.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

/* Root object to store arbitrary binary data.  */

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>

#include "TBlob.hh"

//----------------------------------------------------------------------
// class members
//----------------------------------------------------------------------

// Root magic macro to generate class implementation crud.
ClassImp(TBlob);


TBlob::TBlob()
  : TNamed(),
    data_(NULL),
    length_(0)
{
}


TBlob::TBlob(const char* name, 
	     const char* title)
  : TNamed(name, title),
    data_(NULL),
    length_(0)
{
}


TBlob::~TBlob()
{
  ClearData();
  assert(data_ == NULL);
}


void
TBlob::ClearData()
{
  if (data_ != NULL) {
    assert(length_ != 0);
    delete [] data_;
    data_ = NULL;
    length_ = 0;
  }
}


void
TBlob::SetData(const char* data,
	       size_t length)
{
  ClearData();
  assert(data_ == NULL);
  if (length > 0) {
    data_ = new char[length];
    memcpy(data_, data, length);
    length_ = length;
  }
}


const char*
TBlob::GetData()
  const
{
  return data_;
}


size_t
TBlob::GetLength()
  const
{
  return length_;
}


void
TBlob::Streamer(TBuffer& buffer)
{
  if (buffer.IsReading()) {
    // Clear out anything that might be there already.
    ClearData();
    assert(data_ == NULL);

    // Read the number of bytes.
    buffer >> length_;
    // Allocate space for them.
    data_ = new char[length_];
    // Read them in.
    int read = buffer.ReadBuf(data_, length_);
    assert(read == (int) length_);
  }

  else {
    // Write the number of bytes.
    buffer << length_;
    // Write them out.
    buffer.WriteBuf(data_, length_);
  }
}
