#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

import cPickle
import fnmatch
import os.path
import re
import stat

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class AccessError(RuntimeError):

    pass


#-----------------------------------------------------------------------

class Info(object):

    def __init__(self, name, type):
        self.name = name
        self.type = type
        

    def __repr__(self):
        return "Info(name=%r, type=%r)" % (self.name, self.type)


    def __str__(self):
        attributes = self.__dict__.keys()
        attributes.sort()
        return "Info(" \
               + ", ".join([ "%s=%r" % (a, getattr(self, a))
                             for a in attributes ]) \
               + ")"



#-----------------------------------------------------------------------

class Directory(object):
    """A generalized directory.

    A directory object provides access to (file system and other)
    directory contents through a standard mapping protocol (except that
    the 'copy' method is not available).

    The following attributes specify default options.  They may be
    overridden in method calls by keyword arguments.

    'deldirs' -- If true, allow recursively delete directories by
    deleting their contents.  Otherwise, a directory may be deleted only
    when it is empty.

    'makedirs' -- If true, create missing intervening directories when
    setting a key.  For example, if subdirectory 'a' is empty and the
    key 'a/b/c' is set, the subdirectory 'a/b' is automatically
    created.

    'replace' -- If true, when setting a key that already exists,
    replace the previous value.  Otherwise, a key's value may not be
    overwritten.

    'replacedirs' -- Like 'replace' but if true, also allows replacement
    of entire directories."""

    # A subclass must provide these attributes:
    #
    #   'writable' -- True if the directory is writable.
    #
    # and these methods:
    #
    #   '_keys(**kw_args)' -- Return a sequence of keys.
    # 
    #   '_isdir(key, **kw_args)' -- Return true if 'key' corresponds to
    #   a subdirectory; false if not or if it doesn't exist.
    #
    #   '_get(key, **kw_args)' -- Return the value for 'key'.
    # 
    #   '_set(key, value, **kw_args)' -- Set the value for 'key' to
    #   'value'.
    #
    #   '_delete(key, **kw_args)' -- Remove 'key' and its value.
    #
    #   '_getinfo(key, **kw_args)' -- Return an 'Info' object describing
    #   the value of 'key'.
    #

    deldirs = True
    
    makedirs = True

    replace = True

    replacedirs = False


    def __contains__(self, path):
        subdir, key = self._splitdir(path, makedirs=False)
        return key in subdir._keys()
    

    def __delitem__(self, path):
        subdir, key = self._splitdir(path, makedirs=False)
        subdir.__del(key)


    def __getitem__(self, path):
        if path == "":
            return self
        subdir, key = self._splitdir(path, makedirs=False)
        if key in subdir._keys():
            return subdir._get(key)
        else:
            raise KeyError, "%r in %s" % (key, subdir)


    def __len__(self):
        return len(self._keys())


    def __iter__(self):
        return iter(self._keys())


    def __setitem__(self, path, value):
        subdir, key = self._splitdir(path)
        subdir.__set(key, value)


    def clear(self, **kw_args):
        """Delete keys in this directory.

        See 'keys' for a description of optional keyword attributes."""

        for key in self._keys(**kw_args):
            self.__del(key, **kw_args)


    def delete(self, path, **kw_args):
        """Delete 'path'."""

        subdir, key = self._splitdir(path, makedirs=False)
        subdir.__del(key, **kw_args)
        

    def get(self, path, default=None, **kw_args):
        """Return the contents of 'path'."""

        if path == "":
            return self
        # Disable the 'makedirs' option for 'get' operations.
        kw_args["makedirs"] = False
        subdir, key = self._splitdir(path, **kw_args)
        if key in subdir._keys(**kw_args):
            return subdir._get(key, **kw_args)
        else:
            return default


    def getinfo(self, path, **kw_args):
        # Disable the 'makedirs' option for 'getinfo' operations.
        kw_args["makedirs"] = False
        subdir, key = self._splitdir(path, **kw_args)
        if key in subdir._keys(**kw_args):
            return subdir._getinfo(key, **kw_args)
        else:
            raise KeyError, key


    def has_key(self, path, **kw_args):
        subdir, key = self._splitdir(path, **kw_args)
        return key in subdir._keys(**kw_args)
    

    is_empty = property(lambda self: len(self._keys()) == 0)


    def isdir(self, path, **kw_args):
        # Disable the 'makedirs' option for 'isdir' operations.
        kw_args["makedirs"] = False
        subdir, key = self._splitdir(path, **kw_args)
        return subdir._isdir(key, **kw_args)


    def items(self, **kw_args):
        """Return '(key, value)' pairs in this directory.

        See 'keys' for description of optional keyword arguments."""

        return [ (n, self.get(n, **kw_args))
                 for n in self.keys(**kw_args) ]


    def iteritems(self, **kw_args):
        """Return an iterator of '(key, value)' pairs in this directory.

        See 'keys' for description of optional keyword arguments."""

        for key in self.iterkeys(**kw_args):
            yield key, self.get(key, **kw_args)


    def iterkeys(self, **kw_args):
        """Return an iterator of keys in this directory.

        See 'keys' for description of optional keyword arguments."""

        for key in self.keys(**kw_args):
            yield key


    def itervalues(self, **kw_args):
        """Return an iterator of values in this directory.

        See 'keys' for description of optional keyword arguments."""

        for key in self.iterkeys(**kw_args):
            yield self.get(key, **kw_args)


    def keys(self, **kw_args):
        """Returns the keys in this directory.

        If 'recursive' is true, return paths in this directory and its
        subdirectories.

        Optional keyword arguments:

        'recursive' -- If true, return keys in this directory and its
        subdirectories.  Keys in a subdirectory precedes the
        subdirectory key itself.  Default is false.

        'glob' -- Return only keys matching the specified glob pattern.

        'not_dir' -- If true, don't include subdirectory keys.

        'pattern' -- Return only keys matching the specified regular
        expression.

        'known_types' -- Don't return keys whose types are "unknown".

        'only_type' -- Return only keys whose values' types are as
        specified. 

        returns -- A sequence of keys or paths."""

        paths = self._keys(**kw_args)

        if kw_args.get("recursive", False):
            # Construct a list of all keys in this directory and its
            # subdirectories. 
            all_paths = []
            # Loop over keys.
            for key in self._keys():
                # Is it a subdirectory?
                if self.isdir(key):
                    # Yes.  Get the keys it contains.
                    subdir = self._get(key, **kw_args)
                    # Add them, with a path prefix.
                    all_paths.extend([ os.path.join(key, k)
                                       for k in subdir.keys(**kw_args) ])
                # Add this key itself.
                all_paths.append(key)
            # Use the expanded list.
            paths = all_paths

        if "glob" in kw_args:
            # Apply a glob-style filter.
            glob = kw_args["glob"]
            paths = [ p for p in paths
                      if fnmatch.fnmatchcase(os.path.basename(p), glob) ]

        if kw_args.get("not_dir", False):
            # Remove keys of directories.
            paths = [ p for p in paths if not self.isdir(p) ]

        if "pattern" in kw_args:
            # Apply a regex filter.
            regex = re.compile(kw_args["pattern"])
            paths = [ p for p in paths
                      if regex.match(os.path.basename(p)) is not None ]

        if "only_type" in kw_args:
            # Apply a type filter.
            type_key = kw_args["only_type"]
            paths = [ p for p in paths
                      if self.getinfo(p, **kw_args).type == type_key ]
            
        if kw_args.get("known_types", True):
            # Select only types that are not "unknown".
            paths = [ p for p in paths
                      if self.getinfo(p, **kw_args).type != "unknown" ]

        return paths


    def list(self, **kw_args):
        """Print keys and types in this directory.

        See 'keys' for a description of optional keyword arguments."""

        # Find the paths to list.
        paths = self.keys(**kw_args)
        paths.sort()
        # Construct a formatting template wide enough to display the
        # paths. 
        if len(paths) > 0:
            template = "%%-%ds: %%s" % (max(map(len, paths)) + 4)
        # List the paths.
        for path in paths:
            print template % (path, self.getinfo(path).type)


    def popitem(self, **kw_args):
        """Return and remove a single arbitrary element.

        See 'keys' for a description of optional keyword arguments.
        The 'not_dir' option is implied.

        returns -- A '(path, value)' pair from the directory, which is
        also removed."""

        # Make sure we don't return directories that have just been
        # deleted. 
        kw_args["not_dir"] = True
        # Find the keys that are available.
        paths = self.keys(**kw_args)
        # Are there any?
        if len(paths) == 0:
            # Nope.  Complain.
            raise KeyError, "'%s' is empty" % self
        else:
            # Yes.  Remove and return the first.
            path = paths[0]
            value = self._get(path, **kw_args)
            self.__del(path, **kw_args)
            return path, value


    def mkdir(self, path, **kw_args):
        """Create an empty directory at 'path'.

        'path' -- The path at which to create a directory.  It must not
        already exist.

        returns -- The new directory."""

        subdir, key = self._splitdir(path, **kw_args)
        # Check that the key doesn't always exist.
        if key in subdir._keys(**kw_args):
            raise RuntimeError, "'%s' already exists" % key
        # Make the directory.
        subdir.set(key, {}, type="directory")
        # Return it
        return subdir.get(key, **kw_args)


    def set(self, path, value, **kw_args):
        """Set 'path' to 'value'."""

        subdir, key = self._splitdir(path, **kw_args)
        subdir.__set(key, value, **kw_args)


    def setdefault(self, path, default, **kw_args):
        """Return 'path', setting it to 'default' if it doesn't exist."""

        subdir, key = self._splitdir(path, **kw_args)
        # Is it there?
        if key not in subdir._keys(**kw_args):
            # No.  Set the default value.
            subdir.__set(key, default, **kw_args)
        # Return the value.  Get it by key even if we just set the
        # default, in case the value's type changed.
        return subdir._get(key, **kw_args)


    def update(self, values, **kw_args):
        """Add items from 'values' to the directory.

        'values' -- A map."""

        for key in values.keys():
            self.set(key, values[key], **kw_args)


    def values(self, **kw_args):
        """Return the values in this directory.

        See 'keys' for description of optional keyword arguments."""

        return [ self.get(n, **kw_args) for n in self.keys(**kw_args) ]


    def __del(self, key, **kw_args):
        # Check that the directory is writable.
        if not self.writable:
            raise AccessError, "%s is not writable" % self
        # Is it a directory?
        if self._isdir(key, **kw_args):
            args = dict(kw_args)
            args["writable"] = True
            directory = self.get(key, **args)
            # If the recursive directory removal is enabled, do it.
            deldirs = kw_args.get("deldirs", self.deldirs)
            if deldirs:
                for subkey in directory._keys(**kw_args):
                    directory.__del(subkey, **kw_args)
            # Otherwise, the directory better be empty.
            elif not directory.is_empty:
                raise RuntimeError, "%s is not empty" % self
            del directory
        self._del(key, **kw_args)

        
    def __set(self, key, value, **kw_args):
        # Check that the directory is writable.
        if not self.writable:
            raise AccessError, "%s is not writable" % self
        # Does the key already exist?
        if key in self._keys(**kw_args):
            # Yes.  We should replace it if the 'replace' option is
            # true. 
            replace = kw_args.get("replace", self.replace)
            # For directories, we also requre that the 'replacedirs'
            # option is true.
            if self._isdir(key):
                replace = replace and kw_args.get(
                    "replacedirs", self.replacedirs)
            if replace:
                self.__del(key, **kw_args)
            else:
                raise RuntimeError, "'%s' already exists" % key
        self._set(key, value, **kw_args)


    def _splitdir(self, path, **kw_args):
        """For a path, return the base key and the containing subdirectory.

        'path' -- A path name.

        returns -- '(subdir, key)' where 'subdir' is a directory object
        and 'key' is a key in that subdirectory corresponding to
        'path'. """

        dir_name, key = os.path.split(path)
        # Does it start with a path separator?  Then it's an absolute path.
        if dir_name == os.sep:
            raise KeyError, "absolute paths may not be used"
        # Is it in this directory?
        elif dir_name == "":
            # Yes. Just return the name.
            return self, key
        else:
            # It's in a subdirectory.  Recursively split the
            # subdirectory name.
            subdir, dir_key = self._splitdir(dir_name, **kw_args)
            # Does the subdirectory exist as a directory?
            if subdir.has_key(dir_key):
                if subdir._isdir(dir_key, **kw_args):
                    # Yes.  Go with that.
                    subdir = subdir._get(dir_key, **kw_args)
                else:
                    # There is a non-directory under the subdirectory's
                    # name.  That's a problem.
                    raise KeyError, "'%s' is not a directory" % dir_name
            # The subdirectory doesn't exist.  Should we make it?
            elif kw_args.get("makedirs", self.makedirs):
                # Yup.  Do that.
                 subdir = subdir.setdefault(dir_key, {}, **kw_args)
            else:
                # A missing subdirectory.
                raise KeyError, "no key %r in %s" % (dir_name, self)
            return subdir, key

                

#-----------------------------------------------------------------------

class FileSystemDirectory(Directory):
    """A directory object for a directory in the file system.

    Keys in the directory correspond to names of files in the directory.
    The corresponding values are file contents or file handles,
    depending on the file type.

    Instances supply the following additional attributes:

      'parent' -- The parent directory, or 'None' if this is the root
      directory.

      'root' -- The file system's root directory.

    The file type is determined from the file extension (unless
    overridden by the 'type' keyword argument):

      no extension ("directory") -- A subdirectory.

      '.pickle' ("pickle") -- A file contianing a pickled Python object.

      n/a ("symlink") -- A symbolic link.

      '.text' ("text") -- A text file.

    See 'Directory' for a description of generic directory object
    methods, attributes, and options.

    The following options may be set as class attributes or specified as
    keyword arguments:

      'by_line' -- If true, when reading text files return an iterator
      over lines in the file.  Otherwise, return the entire file
      contents as a string.

      'pickle_binary' -- If true, use the binary format when storing
      Python pickles.

    Note that this class contains problematic race conditions when the
    contents of the directory (or its subdirectories) are modified
    simultaneously by another thread or process."""
      

    by_line = False

    pickle_binary = True


    def __init__(self, path, writable=True):
        # Always us the canonicalized path.
        path = os.path.realpath(path)

        # Check that the directory is accessible.
        if not os.access(path, os.R_OK | os.X_OK):
            raise IOError, "'%s' is not accessible" % path
        if writable:
            # Check that the directory is writable.
            if not os.access(path, os.W_OK):
                raise IOError, "'%s' is not writable" % path

        self.__path = path
        self.__writable = writable


    def __str__(self):
        return self.__path


    def __repr__(self):
        return "FileSystemDirectory(%r, writable=%r)" \
               % (self.__path, self.writable)


    def join(self, path, **kw_args):
        """Return the absolute file system path for 'path'."""

        kw_args["makedirs"] = False
        subdir, key = self._splitdir(path, **kw_args)
        if isinstance(subdir, FileSystemDirectory):
            return os.path.join(subdir.__path, key)
        else:
            raise KeyError, \
                  "'%s' is not a file system directory" % subdir


    def __div__(self, path):
        """A synonym for 'join'."""

        return self.join(path)


    def __truediv__(self, path):
        """A synonym for 'join'."""

        return self.join(path)


    name = property(lambda self: os.path.basename(self.__path))


    def __get_parent(self):
        if self.__path == os.sep:
            return None
        else:
            parent_path = os.path.dirname(self.__path)
            # If this directory is writable, we'll return a writable
            # directory object, unless the parent directory itself is
            # not writable.
            writable = self.writable and os.access(parent_path, os.W_OK)
            # Return the parent directory.
            return FileSystemDirectory(parent_path, writable)


    parent = property(__get_parent)


    path = property(lambda self: self.__path)


    def __get_root(self):
        return root


    root = property(__get_root)


    writable = property(lambda self: self.__writable)
    

    def _del(self, key, **kw_args):
        # print "_del(%r, **%r)" % (key, kw_args)
        path = os.path.join(self.__path, key)
        if os.path.isdir(path):
            # FIXME: Sometimes NFS leaves '.nfs*' transient files around
            # for a moment, which causes the 'rmdir' to fail.  Uncomment
            # the following line to see them.
            # print os.listdir(path)
            os.rmdir(path)
        else:
            os.unlink(path)


    def _get(self, key, **kw_args):
        # print "_get(%r, **%r)" % (key, kw_args)
        type = self.__gettype(key, **kw_args)
        return type[3](self, key, **kw_args)


    def _getinfo(self, key, **kw_args):
        # print "_getinfo(%r, **%r)" % (key, kw_args)
        type = self.__gettype(key, **kw_args)
        path = os.path.join(self.__path, key)
        stat_info = os.stat(path)
        # Create the info object.
        info = Info(key, type[0])
        info.path = path
        info.file_size = stat_info.st_size
        info.user_id = stat_info.st_uid
        info.group_id = stat_info.st_gid
        info.access_mode = stat.S_IMODE(stat_info.st_mode)
        info.modification_time = stat_info.st_mtime
        return info


    def _isdir(self, key, **kw_args):
        # print "_isdir(%r, **%r)" % (key, kw_args)
        path = os.path.join(self.__path, key)
        if os.path.isdir(path):
            return True
        else:
            base, extension = os.path.splitext(key)
            type = self.__extension_map[extension]
            return type[2]


    def _keys(self, **kw_args):
        # print "_keys(**%r)" % kw_args
        return os.listdir(self.__path)


    def _set(self, key, value, **kw_args):
        # print "_set(%r, %r, **%r)" % (key, value, kw_args)
        type = self.__gettype(key, **kw_args)
        type[4](self, key, value, **kw_args)


    def __gettype(self, key, **kw_args):
        path = os.path.join(self.__path, key)

        # If it actually is a directory on disk, the type is always
        # "directory". 
        if os.path.isdir(path):
            return self.__type_map["directory"]
        
        # Get the type specified by keyword argument, if any.
        if "type" in kw_args:
            type_name = kw_args.get("type", None)
            try:
                type = self.__type_map[type_name]
            except KeyError:
                raise TypeError, \
                      "can't handle files of type '%s'" % type_name
        else:
            base, extension = os.path.splitext(key)
            try:
                type = self.__extension_map[extension]
            except KeyError:
                return self.__type_map["unknown"]

        # If we identified it as a directory and it exists, it better be
        # a directory.
        if type[0] == "directory" \
           and os.path.exists(path) \
           and not os.path.isdir(path):
            return self.__type_map["unknown"]

        return type
                

    def __get_directory(self, key, **kw_args):
        path = os.path.join(self.__path, key)
        if not os.path.isdir(path):
            raise TypeError, "'%s' is not a directory" % key
        writable = kw_args.get("writable", self.writable)
        return FileSystemDirectory(path, writable)


    def __set_directory(self, key, value, **kw_args):
        # Make sure 'value' looks like a map.
        if not (hasattr(value, "keys") and hasattr(value, "get")):
            raise TypeError, "value is not a map"
        # Make the directory.
        path = os.path.join(self.__path, key)
        os.mkdir(path)
        # Fill in the initial entries, if some where specified.
        if len(value) > 0:
            self.get(key, **kw_args).update(value, **kw_args)


    def __get_hbook_file(self, key, **kw_args):
        path = self.join(key)
        if not os.path.isfile(path):
            raise TypeError, "'%s' is not a file" % key
        writable = kw_args.get("writable", False)
        record_length = kw_args.get("record_length", 1024)
        purge_cycles = kw_args.get("purge_cycles", True)

        from hep.cernlib import hbook
        return hbook.open(path, writable, record_length, purge_cycles)


    def __set_hbook_file(self, key, value, **kw_args):
        path = self.join(key)
        if os.path.isfile(path):
            raise ValueError, "'%s' already exists" % key
        record_length = kw_args.get("record_length", 1024)
        purge_cycles = kw_args.get("purge_cycles")

        from hep.cernlib import hbook
        hbook_file = hbook.create(path, record_length, purge_cycles)
        hbook_file.update(value)


    def __get_pickle(self, key, **kw_args):
        path = os.path.join(self.__path, key)
        if not os.path.isfile(path):
            raise TypeError, "'%s' is not a file" % key
        return cPickle.load(file(path))


    def __set_pickle(self, key, value, **kw_args):
        path = os.path.join(self.__path, key)
        binary = kw_args.get("pickle_binary", self.pickle_binary)
        cPickle.dump(value, file(path, "w"), binary)


    def __get_root_file(self, key, **kw_args):
        path = self.join(key)
        if not os.path.isfile(path):
            raise TypeError, "'%s' is not a file" % key
        writable = kw_args.get("writable", False)
        purge_cycles = kw_args.get("purge_cycles", True)
        with_metadata = kw_args.get("with_metadata", True)

        import hep.root
        return hep.root.open(path, writable, purge_cycles, with_metadata)


    def __set_root_file(self, key, value, **kw_args):
        path = self.join(key)
        if os.path.isfile(path):
            raise ValueError, "'%s' already exists" % key
        purge_cycles = kw_args.get("purge_cycles")

        import hep.root
        root_file = hep.root.create(path, purge_cycles)
        root_file.update(value)


    def __get_symlink(self, key, **kw_args):
        path = os.path.join(self.__path, key)
        if os.path.islink(path):
            return os.readlink(path)
        else:
            raise TypeError, "'%s' is not a symlink" % key


    def __set_symlink(self, key, value, **kw_args):
        path = os.path.join(self.__path, key)
        os.symlink(value, path)


    def __get_table(self, key, **kw_args):
        import hep.table
        path = self.join(key, **kw_args)
        update = kw_args.get("writable", False)
        row_type = kw_args.get("row_type", hep.table.RowDict)
        with_metadata = kw_args.get("with_metadata", True)
        return hep.table.open(path, update, row_type, with_metadata)


    def __set_table(self, key, value, **kw_args):
        raise NotImplementedError, "cannot assign table obejects"


    def __get_text(self, key, **kw_args):
        path = os.path.join(self.__path, key)
        if os.path.isfile(path):
            text_file = file(path)
            by_line = kw_args.get("by_line", self.by_line)
            if by_line:
                return text_file.xreadlines()
            else:
                return text_file.read()
        else:
            raise TypeError, "'%s' is not an ordinary file" % key


    def __set_text(self, key, value, **kw_args):
        path = os.path.join(self.__path, key)
        file(path, "w").write(value)


    def __get_unknown(self, key, **kw_args):
        raise NotImplementedError, "cannot get files of unknown type"


    def __set_unknown(self, key, value, **kw_args):
        raise NotImplementedError, "cannot set files of unknown type"


    __types = [
        ("directory", "", True, __get_directory, __set_directory),
        ("HBOOK file", ".hbook", True, __get_hbook_file, __set_hbook_file),
        ("pickle", ".pickle", False, __get_pickle, __set_pickle),
        ("Root file", ".root", True, __get_root_file, __set_root_file),
        ("symlink", None, False, __get_symlink, __set_symlink),
        ("table", ".table", False, __get_table, __set_table),
        ("text", ".txt", False, __get_text, __set_text),
        ("unknown", None, False, __get_unknown, __set_unknown),
        ]


    # The items in '__types' mapped to their type names.
    __type_map = dict([ (t[0], t) for t in __types ])

    # The items in '__types' mapped to their file extensions.
    __extension_map = dict([ (t[1], t) for t in __types ])

        

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def get(path, **kw_args):
    if "default" in kw_args:
        have_default = True
        default_vaule = hep.popitem(kw_args, "default")
    else:
        have_default = False
        
    path = os.path.realpath(path)
    dir_name, base_name = os.path.split(path)
    parent_dir = getdir(dir_name, **kw_args)
    if base_name in parent_dir:
        return parent_dir.get(base_name, **kw_args)
    elif have_default:
        return default_value
    else:
        raise KeyError, base_name


def set(path, value, **kw_args):
    path = os.path.realpath(path)
    dir_name, base_name = os.path.split(path)
    parent_dir = getdir(dir_name, **kw_args)
    parent_dir.set(base_name, value, **kw_args)


def getdir(path, **kw_args):
    """Return a directory object for the file system directory 'path'.

    'path' -- The path to a directory.

    returns -- A 'FileSystemDirectory' object."""

    # Canonicalize the path.
    path = os.path.realpath(path)

    # Does it exist as a file system directory?
    if os.path.isdir(path):
        # Yes.  Stop right here and return it.  Should we return it
        # writable? 
        writable = kw_args.get("writable")
        if writable == None:
            # Determine writable status from the directory's write
            # permissions. 
            writable = os.access(path, os.W_OK)
        return FileSystemDirectory(path, writable)

    # Does not exist as a directory.  Split its parent path.
    dir_name, base_name = os.path.split(path)
    # Get its parent directory.
    parent_dir = getdir(dir_name, **kw_args)
    # Create it in its parent directory.
    makedirs = kw_args.get("makedirs", False)
    if makedirs:
        return parent_dir.setdefault(base_name, {}, **kw_args)
    else:
        return parent_dir.get(base_name, **kw_args)


def getcwd(writable="auto"):
    """Return a directory object for the current working directory."""

    return getdir(os.getcwd(), writable=writable)


def tardir(directory, output_dir=None, compression="bz2", options="",
           replace=True):
    """Build a tar archive from a directory tree.

    The archive file is named as 'directory' with the extension '.tar',
    plus an additional extension indicating the compression method.  The
    archive file contains 'directory' and its contents as the only
    top-level directory item.

    'directory' -- The directory to archive.

    'output_dir' -- The directory in which to write the tar archive.  By
    default, the archive is written in the parent of 'directory'.

    'compression' -- Compression mechanism to use: '"bz2"' (bzip2
    compression, the default), '"gz"' (gzip compression), or 'None'.

    'options' -- Additional command-line options to pass to the 'tar'
    command.

    'replace' -- If true, allow an existing tar archive to be replaced.

    returns -- The full path to the generated tar archive."""

    # Construct a path for the tar file.  If an output directory is not
    # specified, put the tar file next to the directory being
    # processed. 
    if output_dir is None:
        output_dir = directory.parent
    tar_file_path = output_dir.join(directory.name + ".tar")
    if compression is not None:
        tar_file_path += "." + compression
    # Check if it exists.
    if os.path.exists(tar_file_path):
        if not replace:
            raise ValueError, "'%s' already exists" % tar_file_path
        # Otherwise, happily overwrite it.

    dir_name, base_name = os.path.split(directory.path)
    # Construct the base command line.
    command_line = [
        "/bin/tar",
        "--create",
        "--file",
        tar_file_path,
        "--directory",
        dir_name,
        ] 
    # Add compression options.
    if compression == "bz2":
        command_line.append("--bzip")
    elif compression == "gz":
        command_line.append("--gzip")
    elif compression is None:
        pass
    else:
        raise ValueError, "unknown compression %r" % compression
    # Add additional caller-specified options.
    command_line += [ o for o in options.split(" ") if o.strip() != "" ]
    # Add the names of the files to include.
    command_line += [
        os.path.join(base_name, k)
        for k in directory.keys(recursive=True, not_dir=True) ]

    # Run the command.
    exit_code = os.spawnve(os.P_WAIT, command_line[0], command_line, {})
    # Check the exit code.
    if exit_code != 0:
        raise RuntimeError, \
              "%s failed (exit code %d)" % (command_line[0], exit_code)
    # Return the name of the tar file.
    return tar_file_path
    

def untardir(tar_file_path, directory=None, options="",
             replacedirs=False):
    """Extract a directory from a tar archive.

    See the 'tardir' command.  The tar archive must contain a directory
    in its root whose name is the same as the base name of the tar
    archive file itself; it is this directory that is extracted from the
    archive.  For instance, the tar archive 'foo.tar' should contain the
    top-level directory 'foo'.

    'tar_file_path' -- The path to the tar file.

    'directory' -- The directory in which to expand the tar archive.  If
    omitted, the directory containing the tar file is used.

    'options' -- Additional command-line options to pass to the 'tar'
    command.

    'replacedirs' -- If true, allow deletion of an existing directory to
    make room for the contents of the tar archive.

    returns -- A directory object for the expanded directory."""

    tar_file_path = os.path.realpath(tar_file_path)
    # Check that the tar file exists.
    if not os.path.isfile(tar_file_path):
        raise ValueError, "'%s' does not exist" % tar_file_path
    
    # Extract the name of the directory contained in the tar file, and
    # infer the compression type.
    base = os.path.basename(tar_file_path)
    if base.endswith(".tar.bz2"):
        compression = "bz2"
        base = base[: -8]
    elif base.endswith(".tar.gz"):
        compression = "gz"
        base = base[: -7]
    elif base.endswith(".tgz"):
        compression = "gz"
        base = base[: -4]
    elif base.endswith(".tar"):
        compression = None
        base = base[: -4]
    else:
        raise ValueError, "unrecongnized file name '%s'" % base

    # Put the expanded directory tree next to the tar file, if no path
    # was specified.
    if directory is None:
        directory = getdir(os.path.dirname(tar_file_path), writable=True)
    # Check whether the target exists.
    if directory.has_key(base):
        if replacedirs:
            # Clean up the existing one.
            directory.delete(base, deldirs=True)
        else:
            # Object.
            raise RuntimeError, \
                  "'%s' already exists" % directory.join(base)

    # Construct the base command.
    command_line = [
        "/bin/tar",
        "--get",
        "--file",
        tar_file_path,
        "--directory",
        directory.path,
        ] 
    # Add compression options.
    if compression == "bz2":
        command_line.append("--bzip")
    elif compression == "gz":
        command_line.append("--gzip")
    elif compression is None:
        pass
    else:
        raise ValueError, "unknown compression %r" % compression
    # Add additional caller-specified options.
    command_line += [ o for o in options.split(" ") if o.strip() != "" ]
    # Add the name of the directory to extract.
    command_line.append(base)

    # Run the command.
    exit_code = os.spawnve(os.P_WAIT, command_line[0], command_line, {})
    # Check the exit code.
    if exit_code != 0:
        raise RuntimeError, \
              "%s failed (exit code %d)" % (command_line[0], exit_code)
    # Return the extracted directory.
    return directory[base]


#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

root = FileSystemDirectory("/", False)

cwd = getcwd()
