//----------------------------------------------------------------------
//
// metadata.hh
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

#ifndef __METADATA_HH__
#define __METADATA_HH__

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <string>

#include "TDirectory.h"

//----------------------------------------------------------------------
// functions
//----------------------------------------------------------------------

/* Return true if metadata is disabled.  */
extern bool
isMetadataDisabled();

/* Return metadata for object stored as 'name' in 'directory'.  

   Sets 'data' to the contents of the metadata and returns true on
   success.  Returns false on failure.  */
extern bool
getMetadata(TDirectory* directory, const char* name, std::string& data);

/* Set metadata for object stored as 'name' in 'directory'.

   Returns true on success, false on failure.  */
extern bool
setMetadata(TDirectory* directory, const char* name, 
	    const std::string& data);

//----------------------------------------------------------------------

#endif  // #ifndef __METADATA_HH__
