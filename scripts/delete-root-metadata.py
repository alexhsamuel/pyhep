#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.root import _cast

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def removeMetadata(tdir):
    """Remove PyHEP metadata from 'tdir' and its subdirectories.

    'tdir' -- A 'TDirectory' object, open for writing."""

    keys = [ _cast(k) for k in tdir.GetListOfKeys() ]
    for key in keys:
        name = key.GetName()
        # Is it the metadata directory?
        if name == hep.root.metadata_key_name:
            # Yes.  Kill it.
            print "deleting metadata in %s" % tdir.GetPath()
            _cast(tdir.Get(name)).Delete("*;*")
            tdir.Delete("%s;*" % name)
        # Is it a subdirectory?
        elif key.GetClassName() == "TDirectory":
            # Remove recursively.
            removeMetadata(_cast(tdir.Get(name)))


#-----------------------------------------------------------------------
# script
#-----------------------------------------------------------------------

if __name__ == "__main__":
    import hep.root.root 
    import sys
    removeMetadata(hep.root.root.TFile(sys.argv[1], "update"))

