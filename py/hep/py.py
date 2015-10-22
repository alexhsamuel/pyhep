#-----------------------------------------------------------------------
#
# module hep.py
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Utilities for manipulating Python internals."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import imp
import string
import sys
import types

#-----------------------------------------------------------------------
# constants
#-----------------------------------------------------------------------

# FIXME: This is not strictly right.  See Py_InteractiveFlag and
# Py_FdIsInteractive() in pythonrun.c etc.
is_interactive = sys.stdin.isatty()
"""True if this appears to be an interactive Python session."""

#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def getCommonType(values):
    """Return the numerical necessary to represent all of 'values'.

    returns -- The type of the value obtained by coercing all elements
    in 'values' together."""
    
    return type(reduce(lambda a, b: coerce(a, b)[1], values))


def coerceTypes(*types):
    """Return 'types' coered to a common type."""

    # Check explicitly if all the types are bool.  If so, the result is
    # bool. 
    if not filter(lambda t: t is not bool, types):
        return bool

    values = [ t(0) for t in types ]
    coerced_value = reduce(lambda v1, v2: coerce(v1, v2)[0], values)
    return type(coerced_value)
    

def getPublicDict(instance):
    """Return a dictionary of non-private attributes of an instance.

    'instance' -- An instance.

    returns -- A dictionary of instance attributes, not including
    private attributes (i.e. those subject to typographic mangling, such
    as '_ClassName__attribute_name')."""

    # Mangled names start with this prefix.
    prefix = "_%s__" % instance.__class__.__name__
    # Copy the dictionary -- don't muck with the original!
    result = instance.__dict__.copy()
    # Delete private names.
    for key in result.keys():
        if key.startswith(prefix):
            del result[key]
    return result


def copyPublicAttributes(dst_object, src_object, omit_names=()):
    """Copy attributes from 'src_object' to 'dst_object'.

    Copies items from the '__dict__' of 'src_object' to the
    '__dict__' of 'dst_object'.  Attributes whose names begin with an
    underscore or appear in 'omit_names' are omitted."""

    src_dict = src_object.__dict__
    dst_dict = dst_object.__dict__
    for name in src_dict:
        if not name.startswith("_") \
           and name not in omit_names:
            dst_dict[name] = src_dict[name]


def load_module(name, path=sys.path):
    """Load a Python module.

    'name' -- The fully-qualified name of the module to load, for
    instance 'package.subpackage.module'.

    'path' -- A sequence of directory paths in which to search for the
    module, analogous to 'PYTHONPATH'.

    returns -- A module object.

    raises -- 'ImportError' if the module cannot be found."""

    # The implementation of this function follows the prescription in
    # the documentation for the standard Python 'imp' module.  See also
    # the 'knee' package included unofficially in the standard Python
    # library. 

    # Is the module already loaded?
    try:
        module = sys.modules[name]
        # It's listed; is there a module instance there?
        if module is not None:
            return module
        # Nope; go on loading.
    except KeyError:
        # No; that's OK.
        pass

    # The module may be in a package.  Split the module path into
    # components. 
    components = string.split(name, ".")
    if len(components) > 1:
        # The module is in a package.  Construct the name of the
        # containing package.
        parent_package = string.join(components[:-1], ".")
        # Load the containing package.
        package = load_module(parent_package, path)
        # Look for the module in the parent package.
        path = package.__path__
    else:
        # No containing package.
        package = None
    # The name of the module itself is the last component of the module
    # path.  
    module_name = components[-1]
    # Locate the module.
    file, file_name, description = imp.find_module(module_name, path)
    # Find the module.
    try:
        # While loading the module, add 'path' to Python's module path,
        # so that if the module references other modules, e.g. in the
        # same directory, Python can find them.  But remember the old
        # path so we can restore it afterwards.
        old_python_path = sys.path[:]
        sys.path = sys.path + path
        # Load the module.
        module = imp.load_module(name, file, file_name, description)
        # Restore the old path.
        sys.path = old_python_path
        # Loaded successfully.  If it's contained in a package, put it
        # into that package's name space.
        if package is not None:
            setattr(package, module_name, module)
        return module
    finally:
        # Close the module file, if one was opened.
        if file is not None:
            file.close()
        
        
def load_class(name, path=sys.path):
    """Load a Python class.

    'name' -- The fully-qualified (including package and module names)
    class name, for instance 'package.subpackage.module.MyClass'.  The
    class must be at the top level of the module's namespace, i.e. not
    nested in another class.

    'path' -- A sequence of directory paths in which to search for the
    containing module, analogous to 'sys.path'.

    returns -- A class object.

    raises -- 'ImportError' if the module containing the class can't be
    imported, or if there is no class with the specified name in that
    module, or if 'name' doesn't correspond to a class."""

    # Make sure the class name is fully-qualified.  It must at least be
    # in a top-level module, so there should be at least one module path
    # separator. 
    if not "." in name:
        raise ValueError, \
              "%s it not a fully-qualified class name" % name
    # Split the module path into components.
    components = string.split(name, ".")
    # Reconstruct the full path to the containing module.
    module_name = string.join(components[:-1], ".")
    # The last element is the name of the class.
    class_name = components[-1]
    # Load the containing module.
    module = load_module(module_name, path)
    # Exctract the requested class.
    try:
        klass = module.__dict__[class_name]
        if not isinstance(klass, types.ClassType):
            # There's something by that name, but it's not a class
            raise ImportError, "%s is not a class" % name
        return klass
    except KeyError:
        # There's no class with the requested name.
        raise ImportError, \
              "no class named %s in module %s" % (class_name, module_name)
    

def getTypeCode(type):
    """Return the type code for 'type'.

    'type' -- A type.

    returns -- The one-letter type code, ala the 'struct' and 'array'
    modules, for storing values of type 'type', or 'None' if there is
    none."""

    return {
        int: 'i',
        float: 'd',
        }.get(type, None)


