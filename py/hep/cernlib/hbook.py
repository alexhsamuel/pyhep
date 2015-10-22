#-----------------------------------------------------------------------
#
# module hep.cernlib.hbook
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""HBOOK library interface."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

import array
import ext
from   hep.bool import *
import hep.fs
import hep.hist
import hep.table
import os
import os.path
from   os.path import join, split

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Directory(hep.fs.Directory):
    """A directory in an RZ file."""

    def __init__(self, file, path, purge_cycles=True):
        """Create a 'Directory' object for 'path' in 'file'."""

        self.__file = file
        self.__path = path
        self.__rz_path = file.makepath(path)
        self.purge_cycles = purge_cycles

        # Read the directory and build info.
        self.__info = dict(
            [ (n, self.__makeinfo(n, i, t))
              for (n, i, t) in _hlnext(self.__rz_path) ])
        # Initialize the subdirectory cache.
        self.__subdirs = {}


    def __del__(self):
        # Purge cycles now, if selected.
        if self.purge_cycles:
            ext.hcdir(self.__rz_path, " ")
            ext.rzpurg(1)


    def __repr__(self):
        return "Directory(%r, %r)" % (self.__file, self.__path)


    def __str__(self):
        return join(self.__file.path, self.__path)


    file = property(lambda self: self.__file)


    def join(self, *names):
        return join(self.__path, *names)


    name = property(lambda self: os.path.basename(self.__path))


    def __get_parent(self):
        dir_name, base_name = split(self.__path)
        if dir_name == "":
            # This is the root directory.  The parent directory is the
            # file system directory containing the HBOOK file.
            parent_path = os.path.dirname(self.__file.path)
            return hep.fs.getdir(parent_path)
        else:
            return Directory(self.__file, dir_name)


    parent = property(__get_parent)


    path = property(lambda self: self.__path)


    root = property(lambda self: self.__file.root)


    rz_path = property(lambda self: self.__rz_path)


    writable = property(lambda self: self.__file.writable)


    def _del(self, key, **kw_args):
        ext.hcdir(self.__rz_path, " ")
        # Kill the sucka.
        if self.isdir(key):
            ext.hddir(key)
            # Update the subdirectory cache.
            if key in self.__subdirs:
                # The directory no longer exists, so don't try to purge
                # cycles when cleaning it up.
                self.__subdirs[key].purge_cycles = False
                # Uncahce it.
                del self.__subdirs[key]
        else:
            # We need its RZ ID to delete it.
            rz_id = self.__info[key].rz_id
            ext.hscr(rz_id, 0, " ")
        # Update the info cache.
        del self.__info[key]

        
    def _get(self, key, **kw_args):
        # Look up the specified path.
        info = self.__info[key]

        if info.type == "directory":
            # It's a directory.  Return a 'Directory' object, checking
            # the cache first.
            if not self.__subdirs.has_key(key):
                self.__subdirs[key] = Directory(
                    self.__file, join(self.__path, key), self.purge_cycles)
            return self.__subdirs[key]

        # Otherwise, load it into memory.
        ext.hcdir(self.__rz_path, " ")
        ext.hrin(info.rz_id, 999999, 0)

        # Construct a Python object for it.
        if info.type == "table":
            # Build a table handle.
            table =  ext.openTuple(
                info.rz_id, self.__rz_path, self.writable)
            # Associate this file with this table, so that the file
            # isn't closed while the table handle still exists.
            table.file = self
            return table

        elif info.type == "1D histogram":
            histogram = self._read1DHistogram(info.rz_id)
            # Remove the HBOOK object from memory.
            ext.hcdir("//PAWC", " ")
            ext.hdelet(info.rz_id)
            # Return the histogram.
            return histogram

        elif info.type == "2D histogram":
            histogram = self._read2DHistogram(info.rz_id)
            # Remove the HBOOK object from memory.
            ext.hcdir("//PAWC", " ")
            ext.hdelet(info.rz_id)
            # Return the histogram.
            return histogram

        else:
            raise NotImplementedError, "type '%s'" % info.type


    def _getinfo(self, key, **kw_args):
        return self.__info[key]


    def _isdir(self, key, **kw_args):
        return self.__info[key].type == "directory"


    def _keys(self, **kw_args):
        return self.__info.keys()


    def _set(self, key, value, **kw_args):
        # Was the RZ ID specified as a keyword argument?
        rz_id = kw_args.get("rz_id", None)
        if rz_id is None:
            if hasattr(object, "rz_id"):
                # The object has an 'rz_id' attribute, so use its value.
                rz_id = int(object.rz_id)
            else:
                # No RZ ID specified; choose an ID.
                rz_id = self._make_rz_id()

        if hep.isMap(value):
            type = "directory"
            # Make a directory.
            ext.hcdir(self.__rz_path, " ")
            ext.hmdir(key, " ")
            # Fill in the initial entries, if some where specified.
            if len(value) > 0:
                self.get(key, **kw_args).update(value, **kw_args)
            # Invalidate the directory cache.
            if key in self.__subdirs:
                del self.__subdirs[key]

        elif hep.hist.isHistogram(value):
            # Make the histogram object in PAWC memory.
            if value.dimensions == 1:
                type = "1D histogram"
                self._make1DHistogram(value, key, rz_id)
            elif value.dimensions == 2:
                type = "2D histogram"
                self._make2DHistogram(value, key, rz_id)
            else:
                raise NotImplementedError, \
                      "cannot save an %d-D histogram in an HBOOK file" \
                      % dimensions
            # Save the histogram to the HBOOK file.
            ext.hcdir(self.__rz_path, " ")
            ext.hrout(rz_id, " ")
            # Clean up the in-memory PAW histogram.
            ext.hcdir("//PAWC", " ")
            ext.hdelet(rz_id)

        else:
            raise NotImplementedError, \
                  "cannot save a %s in an HBOOK file" \
                  % type(value).__name__

        # Update the info cache.
        self.__info[key] = self.__makeinfo(key, rz_id, type)

        
    def _make_rz_id(self):
        """Return an RZ ID unused in this directory."""

        # Collect IDs used in the directory.
        rz_ids = [ info.rz_id for info in self.__info.values() ]
        # If no IDS, return 1.
        if rz_ids == []:
            return 1
        # Return the first unused ID.
        rz_ids.sort()
        for i in range(1, len(rz_ids) + 1):
            if rz_ids[i - 1] != i:
                return i
        return rz_ids[-1] + 1


    def __makeinfo(self, name, rz_id, type):
        """Construct an info object for an RZ directory entry."""

        info = hep.fs.Info(name, type)
        info.rz_id = rz_id
        return info


    def _make1DHistogram(self, hist, title, rz_id):
        assert hist.dimensions == 1
        axis = hist.axis
        num_bins = axis.number_of_bins
        range_lo, range_hi = map(float, axis.range)

        # Create the HBOOK histogram.
        ext.hbook1(rz_id, title, num_bins, range_lo, range_hi, 0)
        # Activate storage of per-bin errors for this histogam.
        ext.hbarx(rz_id)
        # Construct a C array containing the bin contents as floats.
        bin_contents = [ hist.getBinContent(n)
                         for n in xrange(0, num_bins) ]
        pack_array = array.array("f", bin_contents)
        # Stuff the bin contents into the HBOOK histogram.
        ext.hpak(rz_id, pack_array.buffer_info()[0])
        # Construct a C array containing the bin errors as floats.
        bin_errors = \
            [ max(*hist.getBinError(bin)) for bin in xrange(num_bins) ]
        pack_array = array.array("f", bin_errors)
        # Stuff the bin errors into the HBOOK histogram.
        ext.hpake(rz_id, pack_array.buffer_info()[0])
        # Set the underflow and overflow contents.
        # FIXME: This is hackish, but I can't find any other way in the API
        # to do this.
        ext.hf1(rz_id, range_lo - 1, hist.getBinContent("underflow"))
        ext.hf1(rz_id, range_hi + 1, hist.getBinContent("overflow"))
        # Set the number of entries.
        ext.hfnoent(rz_id, hist.number_of_samples)


    def _read1DHistogram(self, rz_id):
        # Make sure this ID corresponds to a 1D histogram.
        kind = ext.hkind(rz_id)
        if kind != 1:
            raise TypeError, "ID %d is not a 1D histogram" % rz_id

        # Obtain histogram parameters.
        title, num_bins, min, max = ext.hgive(rz_id)[:4]
        # Construct the histogram.
        result = hep.hist.Histogram1D(
            num_bins, (min, max),
            bin_type=float, error_model="symmetric",
            title=title, rz_id=rz_id)

        # Get the bin contents.
        bin_contents = ext.hunpak(rz_id, " ", 0, num_bins)
        assert len(bin_contents) == num_bins
        # Get the bin errors.
        bin_errors = ext.hunpke(rz_id, " ", 0, num_bins)
        assert len(bin_errors) == num_bins
        # Store them in the histogram.
        for bin in xrange(0, num_bins):
            result.setBinContent(bin, bin_contents[bin])
            result.setBinError(bin, bin_errors[bin])
        # Store underflow and overflow too.
        result.setBinContent("underflow", ext.hi(rz_id, 0))
        result.setBinContent("overflow", ext.hi(rz_id, num_bins + 1))
        # Store the number of entries.
        result.number_of_samples = ext.hnoent(rz_id)

        return result


    def _make2DHistogram(self, hist, title, rz_id):
        assert hist.dimensions == 2

        x_axis, y_axis = hist.axes
        num_x_bins = x_axis.number_of_bins
        num_y_bins = y_axis.number_of_bins
        x_min, x_max = map(float, x_axis.range)
        y_min, y_max = map(float, y_axis.range)

        # Create the HBOOK histogram.
        ext.hbook2(rz_id, title, num_x_bins, x_min, x_max,
                   num_y_bins, y_min, y_max, 0)
        # Activate storage of per-bin errors for this histogam.
        ext.hbarx(rz_id)

        # Construct a C array containing the bin contents as floats.
        pack_array = array.array("f")
        for y in xrange(0, num_y_bins):
            for x in xrange(0, num_x_bins):
                pack_array.append(hist.getBinContent((x, y)))
        # Fill the bin contents.
        ext.hpak(rz_id, pack_array.buffer_info()[0])
        # Now fill the C array with bin errors.
        for y in xrange(0, num_y_bins):
            for x in xrange(0, num_x_bins):
                pack_array[y * num_x_bins + x] = max(*hist.getBinError((x, y)))
        # Fill the bin errors.
        ext.hpake(rz_id, pack_array.buffer_info()[0])

        # Set the underflow and overflow bins.  This is kind of hackish;
        # using 'hfcxy' here depends on our having called 'hpak' or 'hpake'
        # directly before.
        for x in xrange(0, num_x_bins):
            ext.hfcxy(x + 1, 0, hist.getBinContent((x, "underflow")))
            ext.hfcxy(x + 1, num_y_bins + 1, hist.getBinContent((x, "overflow")))
        for y in xrange(0, num_y_bins):
            ext.hfcxy(0, y + 1, hist.getBinContent(("underflow", y)))
            ext.hfcxy(num_x_bins + 1, y + 1, hist.getBinContent(("overflow", y)))
        ext.hfcxy(0, 0,
                  hist.getBinContent(("underflow", "underflow")))
        ext.hfcxy(num_x_bins + 1, 0,
                  hist.getBinContent(("overflow", "underflow")))
        ext.hfcxy(0, num_y_bins + 1,
                  hist.getBinContent(("underflow", "overflow")))
        ext.hfcxy(num_x_bins + 1, num_y_bins + 1,
                  hist.getBinContent(("overflow", "overflow")))
        # FIXME: Set underflow and overflow errors.  (Is this supported?)
        # Set the number of entries.
        ext.hfnoent(rz_id, hist.number_of_samples)


    def _read2DHistogram(self, rz_id):
        # Make sure this ID corresponds to a 2D histogram.
        kind = ext.hkind(rz_id)
        if kind != 2:
            raise TypeError, "ID %d is not a 2D histogram" % rz_id

        # Obtain histogram parameters.
        title, num_x_bins, x_min, x_max, num_y_bins, y_min, y_max, loc = \
            ext.hgive(rz_id)
        # Construct the histogram.
        result = hep.hist.Histogram(
            (num_x_bins, (x_min, x_max)),
            (num_y_bins, (y_min, y_max)),
            bin_type=float, error_model="symmetric",
            title=title, rz_id=rz_id)

        # Fill the bin contents and errors.
        for x in xrange(0, num_x_bins + 2):
            # Compute our bin number from the HBOOK bin number.
            if x == 0:
                x_bin_number = "underflow"
            elif x == num_x_bins + 1:
                x_bin_number = "overflow"
            else:
                x_bin_number = x - 1

            for y in xrange(0, num_y_bins + 2):
                # Compute our bin number from the HBOOK bin number.
                if y == 0:
                    y_bin_number = "underflow"
                elif y == num_y_bins + 1:
                    y_bin_number = "overflow"
                else:
                    y_bin_number = y - 1

                content = ext.hij(rz_id, x, y)
                error = ext.hije(rz_id, x, y)
                result.setBinContent((x_bin_number, y_bin_number), content)
                result.setBinError((x_bin_number, y_bin_number), error)

        # Load the number of entries.
        result.number_of_samples = ext.hnoent(rz_id)

        return result



#-----------------------------------------------------------------------

class File(object):
    """An open HBOOK file."""

    __next_lun = 20
    # The next available Fortran LUN.


    def __init__(self, path, mode, record_length, purge_cycles):
        """Create or open an HBOOK file.

        'path' -- The path to the HBOOK file.

        'mode' -- The access mode, ala 'os.open':

          * 'r' -- Open an existing file for reading.

          * 'r+' -- Open an existing file for reading and writing.

          * 'w', 'a', 'a+' -- Open a file for reading and writing,
            creating it if necessary.

          * 'w+' -- Open a file for reading and writing, replacing an
            existing file if necessary.

        'record_length' -- The RZ record length to use.

        'purge_cycles' -- If true, all cycles in this file will be
        purged when the file is closed."""

        # Initialize this attribute so __del__ does not bomb out if the
        # object is not completely initialized.
        self.__lun = None
        self.__path = path

        # Parse 'mode'.
        if mode == "r":
            # Open an existing file read-only.
            if not os.path.isfile(path):
                raise IOError, "%s does not exist" % path
            options = "P"
            writable = False
        elif mode == "r+":
            if not os.path.isfile(path):
                raise IOError, "%s does not exist" % path
            options = "UP"
            writable = True
        elif mode in ("w", "a", "a+"):
            if os.path.exists(path):
                # The file alread exists; open it for modification.
                options = "UP"
            else:
                # The file does not exist; create it.
                options = "NP"
            writable = True
        elif mode == "w+":
            # This mode indicates open for writing with truncation, so
            # remove the file if it already exists, and (re)create it.
            if os.path.exists(path):
                os.unlink(path)
            options = "NP"
            writable = True
        else:
            raise ValueError, "unknown mode %s" % mode

        lun = File.__next_lun
        top_directory_title = "LUN%d" % lun
        status, record_length = ext.hropen(
            lun, top_directory_title, path, options, record_length)
        if status != 0:
            raise IOError, "could not open %s" % path
        
        File.__next_lun = lun + 1

        self.__mode = mode
        self.__writable = writable
        self.__lun = lun
        self.__purge_cycles = purge_cycles


    def __del__(self):
        if self.__lun is not None:
            # Close the file.
            ext.hrend("LUN%d" % self.__lun)
            ext.close(self.__lun)
        else:
            # If __lun is None, the file was probably not initialized
            # fully, so do nothing.
            pass
                                                                                

    path = property(lambda self: self.__path)
    """The path to the HBOOK file."""


    lun = property(lambda self: self.__lun)
    """The Fortran LUN used for the open file."""


    writable = property(lambda self: self.__writable)
    """True if the file may be written to or modified."""


    def __repr__(self):
        return "File(%r, %r)" % (self.__path, self.__mode)


    def __str__(self):
        return self.__path


    def makepath(self, *components):
        """Return the RZ path for path 'components' in this file."""

        components = filter(None, components)
        return "//" + join("LUN%d" % self.__lun, *components)
        

    path = property(lambda self: self.__path)


    writable = property(lambda self: self.__writable)


    root = property(lambda self: Directory(self, "", self.__purge_cycles))



#-----------------------------------------------------------------------
# helper functions
#-----------------------------------------------------------------------

def _cmp_columns(c1, c2):
    # Order by decreasing size of column type.
    size1 = hep.table._type_info[c1.type][1]
    size2 = hep.table._type_info[c2.type][1]
    return -cmp(size1, size2)


def _getColumnsInOrder(schema):
    """Return the columns in 'schema', ordered for data alignment.

    returns -- A list of the columns in 'schema', which has been ordered
    to provide the correct alignment of variables.  Columns with wider
    types precede columns with narrower types."""

    columns = list(schema.columns)
    columns.sort(_cmp_columns)
    return columns


def _hlnext(rz_path):
    """An iterator over entries in a directory.

    'path' -- The RZ path to the directory.

    yields -- '(key, rz_id, type)' for each element in the directory."""

    ext.hcdir(rz_path, " ")
    rz_id = 0
    while True:
        rz_id, rz_type, key = ext.hlnext(rz_id, "12ND")
        if rz_id == 0:
            raise StopIteration
        # Always use lower-case names.
        key = key.lower()
        yield key, rz_id, {
            "1": "1D histogram",
            "2": "2D histogram",
            "N": "table",
            "D": "directory",
        }[rz_type]


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def create(path, record_length=1024, purge_cycles=True):
    """Create a new HBOOK file.

    'path' -- The path to the HBOOK file.

    'record_length' -- The RZ record length to use.

    'purge_cycles' -- If true, all cycles are purged when the file is
    closed.

    returns -- A 'Directory' object to the root of the new file."""

    file = File(path, "w+", record_length, purge_cycles)
    return Directory(file, "")


def open(path, writable=False, record_length=1024, purge_cycles=True):
    """Open an existing HBOOK file.

    'path' -- The path to the HBOOK file.

    'record_length' -- The RZ record length to use.

    'purge_cycles' -- If true, all cycles are purged when the file is
    closed.

    returns -- A 'Directory' object to the root of the file."""

    if writable:
        mode = "r+"
    else:
        mode = "r"
        purge_cycles = False
    file = File(path, mode, record_length, purge_cycles)
    return file.root


def createTable(name, directory, schema, rz_id=None, column_wise=True):
    """Create an ntuple in an HBOOK file.

    Note that the restrictions on allowed schemas are different for
    column- and row-wise ntuples.

    'name' -- The title of the ntuple.

    'directory' -- A 'Directory' object of an HBOOK file.

    'schema' -- The schema to use for the table.

    'rz_id' -- The ntuple's RZ ID.  If 'None', one is chosen
    automatically.

    'column_wise' -- If true, creates a column-wise ntuple.  Otherwise,
    creates a row-wise ntuple.

    returns -- A table object."""

    # Make sure the table is being put in an HBOOK file.
    if not isinstance(directory, Directory):
        raise TypeError, "directory is not in an HBOOK file"
    # Make sure the file is writable.
    if not directory.writable:
        raise hep.fs.AccessError, "%s is not writable" % directory

    if rz_id is None:
        rz_id = directory._make_rz_id()

    # Check that the names and types of columns are consistent with
    # the ntuple type.
    for column in schema.columns:
        if column_wise:
            if len(column.name) > 32:
                raise ValueError, "column names in a column-wise " \
                      "ntuple may not be longer than 32 characters"
            if column.type \
                   not in ("int32", "int64", "float32", "float64"):
                raise ValueError, "unsupported type '%s' " \
                      "for column-wise ntuple" % column.type
        else:
            if len(column.name) > 8:
                raise ValueError, "column names in a row-wise " \
                      "ntuple may not be longer than 8 characters"
            if column.type != "float32":
                raise ValueError, "columns in a row-wise ntuple " \
                      "must be \"float32\" type"

    rz_path = directory.rz_path
    if column_wise:
        table = ext.createColumnWiseNtuple(rz_id, name, rz_path, schema)
        if len(schema) != len(table.schema):
            # A problem occured with one or more columns.
            raise RuntimeError, "error creating columns of %s" % path
    else:
        table = ext.createRowWiseNtuple(rz_id, name, rz_path, schema)
    table.file = directory.file
    return table


