//----------------------------------------------------------------------
//
// metadata.cc
//
// Copyright 2003 by Alex Samuel.  All rights reserved.
//
//----------------------------------------------------------------------

//----------------------------------------------------------------------
// includes
//----------------------------------------------------------------------

#include <cassert>
#include <string>

#include "metadata.hh"
#include "TBlob.hh"

//----------------------------------------------------------------------
// constants
//----------------------------------------------------------------------

namespace {

const char* const 
metadata_dir_name = "_pyhep_metadata";

const char* const 
metadata_dir_title = "PyHEP metadata";

//----------------------------------------------------------------------
// helper functions
//----------------------------------------------------------------------

TDirectory*
getMetadataDirectory(TDirectory* directory,
		     bool create)
{
  assert(directory != NULL);

  TDirectory* mdir = (TDirectory*) directory->Get(metadata_dir_name);
  if (mdir == NULL && create) {
    mdir = directory->mkdir(metadata_dir_name, metadata_dir_title);
    return mdir;
  }
  else
    return mdir;
}


}  // anonymous namespace

//----------------------------------------------------------------------
// functions
//----------------------------------------------------------------------

bool
getMetadata(TDirectory* directory, 
	    const char* name,
	    std::string& data)
{
  if (isMetadataDisabled())
    return false;

  TDirectory* metadata_dir = getMetadataDirectory(directory, false);
  if (metadata_dir == NULL)
    return "";

  TObject* metadata_obj = metadata_dir->Get(name);
  metadata_dir->Print();
  if (metadata_obj == NULL)
    return false;
  if (! metadata_obj->InheritsFrom("TBlob"))
    return false;

  TBlob* blob = (TBlob*) metadata_obj;
  data = std::string(blob->GetData(), blob->GetLength());
  return true;
}


bool
setMetadata(TDirectory* directory,
	    const char* name,
	    const std::string& data)
{
  if (isMetadataDisabled())
    return false;

  TDirectory* metadata_dir = getMetadataDirectory(directory, true);
  if (metadata_dir == NULL)
    return false;

  metadata_dir->cd();
  std::string title = std::string("PyHEP metadata for ") + name;
  TBlob blob(name, title.c_str());
  blob.SetData(data.data(), data.size());
  return blob.Write() > 0;
}

