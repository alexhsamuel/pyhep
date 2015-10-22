#-----------------------------------------------------------------------
#
# module hep.root
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Root program library interface."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

# Before loading the binary module that drags in the ROOT libraries, we
# have to make sure the 'ROOTSYS' environment variable is set.  The ROOT
# shared libraries use this during their initialization.
import hep.config
import os

ROOTSYS = os.path.join(hep.config.base_dir, "hep", "root", "ROOTSYS")
if not os.path.isdir(ROOTSYS):
    raise ImportError, "can't find ROOTSYS at %r" % ROOTSYS
os.environ["ROOTSYS"] = ROOTSYS

# Now it's OK to bring in ROOT.
import root
import ext

import cPickle
from   hep.bool import *
import hep.fs
import hep.hist
import hep.py
import hep.table
import hep.text
import os.path
from   os.path import join, split, realpath
import sys
import weakref

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

root_version = ext.getRootVersion()
"""The version number of the Root libraries used."""

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Directory(hep.fs.Directory):

    def __init__(self, file, tdirectory, purge_cycles=True):
        self.__file = file
        self.__tdirectory = tdirectory
        self.__path = tdirectory.GetPath().split(":", 1)[1][1 :]
        self.purge_cycles = purge_cycles

        self.__info = {}
        tlist = tdirectory.GetListOfKeys()
        for tkey in [ _cast(tlist[i]) for i in range(len(tlist)) ]:
            self.__info[tkey.GetName()] = self.__makeinfo(tkey)

        self.__subdirs = {}
        

    def __del__(self):
        # Purge cycles now, if selected.
        if self.purge_cycles:
            self.__tdirectory.Purge(1)


    def __str__(self):
        return join(self.__file.path, self.__path)


    def __repr__(self):
        return "Directory(%r, %r)" % (self.__file, self.__tdirectory)


    file = property(lambda self: self.__file)


    def join(self, name):
        return join(self.__path, name)


    def list(self, **kw_args):
        """Print keys and types in this directory.

        See 'keys' for a description of optional keyword arguments."""

        # Find the paths to list.
        paths = self.keys(**kw_args)
        paths.sort()
        # Get the types and titles of the paths.
        infos = map(self.getinfo, paths)
        types = [ i.type for i in infos ]
        abbreviate = hep.text.abbreviator(32)
        titles = [ "'%s'" % abbreviate(i.title) for i in infos ]
        # Construct a formatting template wide enough to display the
        # paths. 
        if len(paths) > 0:
            len_paths = max(map(len, paths))
            len_titles = max(map(len, titles))
            template = "%%-%ds  %%-%ds : %%s" % (len_paths, len_titles)
        # List the paths.
        for path, title, type in zip(paths, titles, types):
            print template % (path, title, type)


    name = property(lambda self: self.__tdirectory.GetName())


    def __get_parent(self):
        dir_name, base_name = split(self.__path)
        if dir_name == "":
            # This is the root directory.  The parent directory is the
            # file system directory containing the HBOOK file.
            parent_path = os.path.dirname(self.file.path)
            return hep.fs.getdir(parent_path)
        else:
            return Directory(self.file, dir_name)


    parent = property(__get_parent)


    path = property(lambda self: self.__path)


    root = property(lambda self: self.file.root)


    writable = property(lambda self: self.file.writable)


    with_metadata = property(lambda self: self.file.with_metadata)


    def _del(self, key, **kw_args):
        tkey = self.__getTKey(key)
        if self.__info[key].type == "directory":
            if key in self.__subdirs:
                # The directory no longer exists, so don't try to purge
                # cycles when cleaning it up.
                self.__subdirs[key].purge_cycles = False
                del self.__subdirs[key]
            # Directories need to be handled a litte differently.
            self.__tdirectory.Delete("%s;1" % key)
        else:
            self.__tdirectory.Delete("%s;*" % key)
        del self.__info[key]


    def _get(self, key, **kw_args):
        # Get info about the object.
        info = self.__info[key]
        # Extract the requested object.
        object = self.__tdirectory.Get(key)
        assert object is not None and object.this != "NULL"
        # Cast it to its runtime type.
        object = _cast(object)

        if info.type == "directory":
            if not self.__subdirs.has_key(key):
                self.__subdirs[key] = \
                    Directory(self.file, object, self.purge_cycles)
            return self.__subdirs[key]

        elif object.InheritsFrom("TTree"):
            # Choose the row class.
            row_type = kw_args.get("row_type", hep.table.RowDict)
            # It's a tree.  Open it as a table.
            address = _getSwigPointerAddress(object.this)
            with_metadata = kw_args.get(
                "with_metadata", self.file.with_metadata)
            tree = ext.openTree(address, self.file.writable, row_type,
                                with_metadata)
            # Note the file on the tree, so that the file isn't
            # closed until the tree has gone away.
            tree.file = self.file
            # All done.
            return tree
        # TH2 and TH3 are subclasses of TH1 (?!) so we have to check
        # these first.
        elif object.InheritsFrom("TH2"):
            # A two-dimensional histogram.
            return self.__get2DHistogram(self.__tdirectory, object)
        elif object.InheritsFrom("TH3"):
            # A three-dimensional histogram.
            raise hep.NotSupporedError, \
                  "%s object in ROOT file" % object.ClassName()
        elif object.InheritsFrom("TH1"):
            # A one-dimensional histogram.
            return self.__get1DHistogram(self.__tdirectory, object)
        else:
            # Don't know how to handle anything else.
            raise NotImplementedError, \
                  "%s object in ROOT file" % object.ClassName()


    def _getinfo(self, key, **kw_args):
        return self.__info[key]


    def _isdir(self, key, **kw_args):
        return self.__info[key].type == "directory"


    def _keys(self, **kw_args):
        return self.__info.keys()


    def _set(self, key, value, **kw_args):
        if hep.isMap(value):
            # Make a directory.  Use the key as the title, if none was
            # given. 
            title = kw_args.get("title", key)
            tdirectory = self.__tdirectory.mkdir(key, title)
            # Update the info cache.
            tkey = self.__getTKey(key)
            self.__info[key] = self.__makeinfo(tkey)
            # Fill in the initial entries, if some where specified.
            if len(value) > 0:
                self.get(key, **kw_args).update(value, **kw_args)
            # Invalidate the directory cache.
            if key in self.__subdirs:
                del self.__subdirs[key]

        elif hep.hist.isHistogram(value):
            # Save a histogram.
            if value.dimensions == 1:
                self.__set1DHistogram(self.__tdirectory, key, value)
            elif value.dimensions == 2:
                self.__set2DHistogram(self.__tdirectory, key, value)
            else:
                raise NotImplementedError, \
                      "%d-dimensional histograms" % object.dimensions
        else:
            # FIXME: Support other types.
            raise NotImplementedError, \
                  "%s object in ROOT file" % str(type(value))

        # Update the info cache.
        tkey = self.__getTKey(key)
        self.__info[key] = self.__makeinfo(tkey)


    def __getTKey(self, name):
        """Return the 'TKey' corresponding to 'name' in this directory.

        raise -- 'KeyError' if there is no key named 'name'."""
        
        key = self.__tdirectory.GetKey(name)
        if key is None or key.this == "NULL":
            raise KeyError, name
        return _cast(key)


    def __makeinfo(self, tkey):
        # Look up the specified path.
        class_name = tkey.GetClassName()
        # FIXME: Ugh.  There's GOT to be a better way of doing this.
        if class_name in ("TDirectory", "TFile", ):
            type = "directory"
        elif class_name == "TTree":
            type = "table"
        elif class_name.startswith("TH3"):
            type = "3D histogram"
        elif class_name.startswith("TH2"):
            type = "2D histogram"
        elif class_name.startswith("TH1"):
            type = "1D histogram"
        else:
            type = "unknown"

        # Construct an 'Info' object.
        info = hep.fs.Info(tkey.GetName(), type)
        info.title = tkey.GetTitle()
        info.class_name = class_name
        return info


    def __get1DHistogram(self, directory, histogram):
        # Make sure it's a Root 1D histogram.
        assert histogram.InheritsFrom("TH1")
        histogram = _cast(histogram, root.TH1)
        # Get the axis parameters.
        axis = histogram.GetXaxis()
        range = axis.GetXmin(), axis.GetXmax()
        num_bins = axis.GetNbins()
        # Determine the type of the bin contents from the object's class.
        if histogram.InheritsFrom("TH1F") \
           or histogram.InheritsFrom("TH1D"):
            bin_type = float
        elif histogram.InheritsFrom("TH1C") \
             or histogram.InheritsFrom("TH1S"):
            bin_type = int
        else:
            raise NotImplementedError, \
                  "histogram type %s" % histogram.ClassName()

        # Construct a new Python histogram.
        result = hep.hist.Histogram1D(
            num_bins, range,
            bin_type=bin_type, error_model="symmetric")
        # Fill the underflow bin.
        contents = histogram.GetBinContent(0)
        error = histogram.GetBinError(0)
        result.setBinContent("underflow", contents)
        result.setBinError("underflow", error)
        # Fill the ordinary bins.
        for bin_number in xrange(0, num_bins):
            contents = histogram.GetBinContent(bin_number + 1)
            error = histogram.GetBinError(bin_number + 1)
            result.setBinContent(bin_number, contents)
            result.setBinError(bin_number, error)
        # Fill the overflow bin.
        contents = histogram.GetBinContent(num_bins + 1)
        error = histogram.GetBinError(num_bins + 1)
        result.setBinContent("overflow", contents)
        result.setBinError("overflow", error)
        # Set some other attributes.
        _setAttributesFromTNamed(histogram, result)
        result.number_of_samples = int(histogram.GetEntries())

        return result


    def __get2DHistogram(self, directory, histogram):
        assert histogram.InheritsFrom("TH2")
        histogram = _cast(histogram, root.TH2)
        # Get the axis parameters.
        xaxis = histogram.GetXaxis()
        yaxis = histogram.GetYaxis()
        xbins = xaxis.GetNbins()
        ybins = yaxis.GetNbins()
        # Determine the type of the bin contents from the object's class.
        if histogram.InheritsFrom("TH2F"):
            bin_type = float
            histogram = _cast(histogram, root.TH2F)
        elif histogram.InheritsFrom("TH2D"):
            bin_type = float
            histogram = _cast(histogram, root.TH2D)
        elif histogram.InheritsFrom("TH2C"):
            bin_type = int
            histogram = _cast(histogram, root.TH2C)
        elif histogram.InheritsFrom("TH2S"):
            bin_type = int
            histogram = _cast(histogram, root.TH2S)
        else:
            raise NotImplementedError, \
                  "2D histograms of type '%s'" % histogram.ClassName()

        # Construct a new Python histogram.
        result = hep.hist.Histogram(
            (xbins, (xaxis.GetXmin(), xaxis.GetXmax())),
            (ybins, (yaxis.GetXmin(), yaxis.GetXmax())),
            bin_type=bin_type, error_model="symmetric")
        # Fill the bins, including underflows and overflows.
        for x in xrange(0, xbins + 2):
            for y in xrange(0, ybins + 2):
                if x == 0:
                    x_binno = "underflow"
                elif x == xbins + 1:
                    x_binno = "overflow"
                else:
                    x_binno = x - 1
                if y == 0:
                    y_binno = "underflow"
                elif y == ybins + 1:
                    y_binno = "overflow"
                else:
                    y_binno = y - 1
                result.setBinContent(
                    (x_binno, y_binno), histogram.GetBinContent(x, y))
                result.setBinError(
                    (x_binno, y_binno), histogram.GetBinError(x, y))
        # Set some other attributes.
        _setAttributesFromTNamed(histogram, result)
        result.number_of_samples = int(histogram.GetEntries())

        return result


    def __set1DHistogram(self, directory, name, histogram):
        # FIXME: Support other types.
        # assert histogram.bins.bin_type == float

        # Construct a histogram.
        num_bins = histogram.axes[0].number_of_bins
        range_lo, range_hi = histogram.axes[0].range
        directory.cd()
        result = root.TH1F("", "", num_bins, range_lo, range_hi)

        # Fill the underflow bin.
        result.SetBinContent(0, histogram.getBinContent("underflow"))
        result.SetBinError(0, max(*histogram.getBinError("underflow")))
        # Fill the normal bins.
        for bin_number in xrange(0, num_bins):
            contents = histogram.getBinContent(bin_number)
            result.SetBinContent(bin_number + 1, contents)
            error = max(*histogram.getBinError(bin_number))
            result.SetBinError(bin_number + 1, error)
        # Fill the overflow bin.
        result.SetBinContent(num_bins + 1, histogram.getBinContent("overflow"))
        result.SetBinError(num_bins + 1, max(*histogram.getBinError("overflow")))
        # Set other things, if the corresponding attributes are
        # present. 
        _setAttributesInTNamed(histogram, result)
        result.SetName(name)
        result.SetEntries(histogram.number_of_samples)
        result.Write()


    def __set2DHistogram(self, directory, name, histogram):
        # Get axis information.
        xaxis, yaxis = histogram.axes
        xtype = xaxis.type
        xbins = xaxis.number_of_bins
        xmin, xmax = xaxis.range
        ytype = yaxis.type
        ybins = yaxis.number_of_bins
        ymin, ymax = yaxis.range
        # Choose the appropriate ROOT histogram type.
        if xtype == float and ytype == float:
            root_type = root.TH2D
        elif xtype == int and ytype == int:
            root_type = root.TH2S
        else:
            raise NotImplementedError, \
                  "2D histogram with axis types %s and %s" \
                  % (xtype, ytype)
        # Construct a histogram.
        directory.cd()
        result = root_type("", "", xbins, xmin, xmax, ybins, ymin, ymax)

        # Fill the bins, including underflows and overflows.
        for x in xrange(0, xbins + 2):
            for y in xrange(0, ybins + 2):
                if x == 0:
                    x_binno = "underflow"
                elif x == xbins + 1:
                    x_binno = "overflow"
                else:
                    x_binno = x - 1
                if y == 0:
                    y_binno = "underflow"
                elif y == ybins + 1:
                    y_binno = "overflow"
                else:
                    y_binno = y - 1
                result.SetBinContent(
                    x, y, histogram.getBinContent((x_binno, y_binno)))
                result.SetBinError(
                    x, y, max(*histogram.getBinError((x_binno, y_binno))))
        # Set other things, if the corresponding attributes are
        # present. 
        _setAttributesInTNamed(histogram, result)
        result.SetName(name)
        result.SetEntries(histogram.number_of_samples)

        result.Write()



#-----------------------------------------------------------------------

class TFile(root.TFile):
    """Subclass of 'TFile' wrapper with close-on-delete."""

    def __del__(self):
        self.Close()



#-----------------------------------------------------------------------

class File(object):
    """An open Root file."""

    def __init__(self, path, mode, purge_cycles=True, with_metadata=True):
        """Do not instantiate this class directly.  Use 'open'."""
        
        # Parse 'mode'.
        if mode == "r":
            writable = False
            if not os.path.isfile(path):
                raise IOError, "'%s' does not exist" % path
            options = "READ"
        elif mode == "r+":
            writable = True
            if not os.path.isfile(path):
                raise IOError, "'%s' does not exist" % path
            options = "UPDATE"
        elif mode in ("w", "a", "a+"):
            writable = True
            options = "UPDATE"
        elif mode == "w+":
            writable = True
            options = "RECREATE"
        else:
            raise ValueError, "unknown mode %s" % mode
        # Purge cycles only when the file is writable.
        if not writable:
            purge_cycles = False

        self.__writable = writable
        self.__mode = mode
        self.__purge_cycles = purge_cycles
        self.__with_metadata = with_metadata

        # Open the file.
        self.__tfile = TFile(path, options)
        # Make sure that worked.
        if self.__tfile.IsZombie():
            raise IOError, "could not open %s" % path
        self.__path = realpath(path)


    def __str__(self):
        return self.__path


    def __repr__(self):
        return "File(%r, %r)" % (self.__path, self.__mode)


    path = property(lambda self: self.__path)


    writable = property(lambda self: self.__writable)
    """True if the file may be written to or modified."""


    root = property(lambda self:
                    Directory(self, self.__tfile, self.__purge_cycles))


    with_metadata = property(lambda s: s.__with_metadata)
            


#-----------------------------------------------------------------------
# helper functions
#-----------------------------------------------------------------------

def _getSwigPointerAddress(pointer_string):
    """Return the numerical address pointed to by a SWIG pointer."""

    return root.rootc.getPointerValue(pointer_string)


def _cast(object, new_class=None):
    """Cast an instnace of a 'TObject' subclass to another subclass.

    'object' -- An instance of a subclass of 'TObject'.

    'new_class' -- A subclass of 'TObject', to which to cast 'object'.
    If 'None', 'object' is cast to its actual most-derived class type,
    as determined by its 'ClassName' method.

    returns -- 'object', cast to 'new_class'.

    raises -- 'TypeError' if the dynamic type of 'object' is not a
    subclass of 'new_class'."""

    if object.this == "NULL":
        raise RuntimeError, "cast of NULL TObject"

    if new_class is None:
        # Get the object's actual class name.
        class_name = object.ClassName()
        try:
            # Look up the pointer class in the ROOT SWIG module.
            getattr(root, class_name)
        except AttributeError:
            raise NotImplementedError, \
                  "ROOT class %s not available" % class_name
    else:
        class_name = new_class.__name__
        if not object.InheritsFrom(class_name):
            raise TypeError, \
                  "%s is not a %s" % (repr(object), class_name)

    # Get the pointer class corresponding to the object class.
    ptr_class_name = class_name + "Ptr"
    ptr_class = getattr(root, ptr_class_name)
    # Convert the 'this' pointer.
    # WARNING: Since this is equivalent to a C++ 'reinterpret_cast', it
    # works only if both classes have the same offset.  In particular,
    # a downcast from a secondary base class will produce an invalid
    # object. 
    # this = root.ptrcast(object.this, class_name + "_p")
    parts = object.this.split("_")
    # FIXME: Oh gawd.  This hack is necessary because the format of SWIG
    # pointers changed between versions 1.1 and 1.3.  This whole
    # function is a horrible thing.
    if parts[2] == "p":
        this = "_%s_p_%s" % (parts[1], class_name)
    elif parts[3] == "p":
        this = "_%s_%s_p" % (parts[1], class_name)
    else:
        assert False
    # Construct the result.
    return ptr_class(this)


def _setAttributesInTNamed(python_obj, root_obj):
    # Set the name from the 'name' attribute, if present.
    if hasattr(python_obj, "name"):
        root_obj.SetName(str(python_obj.name))
    # Set the title from the 'title' attribute, if present.
    if hasattr(python_obj, "title"):
        root_obj.SetTitle(str(python_obj.title))


def _setAttributesFromTNamed(root_obj, python_obj):
    # Set the name and title.
    python_obj.name = root_obj.GetName()
    python_obj.title = root_obj.GetTitle()


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def create(path, purge_cycles=True):
    """Create a new Root file.

    'path' -- The path to the file.

    'purge_cycles' -- If true, all cycles are purged when the file is
    closed.

    returns -- A 'Directory' object for the root directory of the
    file.""" 

    file = File(path, "w+", purge_cycles)
    return file.root


def open(path, writable=False, purge_cycles=True, with_metadata=True):
    """Open an existing Root file.

    'path' -- The path to the file.

    'writable' -- If true, open for writing as well as reading; otherwise,
    open for reading only.

    'purge_cycles' -- If true, all cycles are purged when the file is
    closed.

    returns -- A 'Directory' object for the root directory of the
    file.""" 

    if writable:
        mode = "r+"
    else:
        mode = "r"
    file = File(path, mode, purge_cycles, with_metadata)
    return file.root


def createTable(name, directory, schema, title=None,
                separate_branches=False, branch_name="default"):
    """Create a new table.

    A new table is implemented in a Root file by a Root tree (a
    'TTree' instance).  

    'name' -- The name under which to store the tree.

    'directory' -- The Root 'Directory' in which to store the tree. 

    'schema' -- The table schema.

    'title' -- The tree's title.  If 'None', the name is used.

    'separate_branches' -- If true, the leaf corresponding to each
    column is places on a separate branch with the same name as the
    column.  Otherwise, all leaves are combined into a single
    branch, named by 'branch_name'.

    'branch_name' -- If 'separate_branches' is false, this is the
    name of the branch containing all the leaves.

    'with_metdata' -- Load and store metadata.
    """

    # Make sure the table is being put in a Root directory.
    if not isinstance(directory, Directory):
        raise TypeError, "directory is not in a Root file"
    # Make sure the directory is writable.
    if not directory.writable:
        raise hep.fs.AccessError, "%s is not writable" % directory

    # Clean up arguments.
    if title is None:
        # No title specified; use the tree name.
        title = name
    # Make sure 'separate_branches' is boolean.
    separate_branches = bool(separate_branches)

    # Build the tree.
    address = _getSwigPointerAddress(
        directory._Directory__tdirectory.this)
    tree = ext.createTree(
        address, name, title, schema, separate_branches, branch_name,
        8192, directory.file.with_metadata)
    # Note the file on the tree, so that the file isn't closed until
    # the tree has gone away.
    tree.file = directory.file
    return tree

