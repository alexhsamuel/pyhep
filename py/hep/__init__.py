#-----------------------------------------------------------------------
#
# module hep
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Module for general-purpose code."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

import os
import signal
import traceback

#-----------------------------------------------------------------------
# exceptions
#-----------------------------------------------------------------------

class TimeoutException(Exception):
    """A timeout occurred."""

    pass



class NotSupportedError(RuntimeError):
    """A feature is not supported."""

    pass



class SyntaxError(Exception):

    pass



#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Token:

    pass



class Timeout:

    def __timeout_handler(self, signal_number, frame):
        assert signal_number == signal.SIGALRM
        signal.signal(signal.SIGALRM, self.__old_handler)
        self.__active = 0
        raise TimeoutException, self.__message


    def __init__(self, time, message):
        self.__message = message
        self.__old_handler = \
            signal.signal(signal.SIGALRM, self.__timeout_handler)
        self.__active = 1
        signal.alarm(time)


    def cancel(self):
        if not self.__active:
            return
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        self.__active = 0



class MappingAsObject:
    """Implement the object attribute protocol using a mapping.

    A 'MappingAsObject' wraps an object satifying the mapping protocol.
    Attribute references are converted to item gets and sets in the
    underlying mapping."""

    def __init__(self, mapping):
        """Wrap 'mapping' in the object procotol."""
        
        self.__dict__["_MappingAsObject__mapping"] = mapping


    _mapping = property(lambda self: self.__mapping)
    """Read-only access to the underlying mapping."""


    def __getattr__(self, name):
        try:
            return self.__mapping[name]
        except KeyError:
            raise AttributeError, name


    def __setattr__(self, name, value):
        try:
            self.__mapping[name] = value
        except KeyError, exception:
            raise AttributeError, str(exception)



class NrBreitWigner:
    """A non-resonant Breit-Wigner line shape amplitude factor."""

    def __init__(self, mass, width):
        """Construct a non-relativistic Breit-Wigner function.

        'mass' -- The resonance mass.
        
        'width' -- The resonance width."""

        self.__mass = mass
        self.__width = width


    def __call__(self, s):
        """Return the amplitude at energy-squared 's'."""

        mass = self.__mass
        return 1 / (s - complex(mass * mass, mass * self.__width))



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

try:
    enumerate = __builtins__.enumerate
except AttributeError:
    def enumerate(iterable):
        count = 0
        for item in iter(iterable):
            yield count, item
            count += 1


try:
    sorted = __builtins__.sorted
except AttributeError:
    def sorted(iterable, cmp=cmp):
        result = list(iterable)
        result.sort(cmp)
        return result


try:
    reversed = __builtins__.reversed
except AttributeError:
    def reversed(iterable):
        result = list(iterable)
        result.reverse()
        return result
    

def sort(sequence, sort_fn=None):
    """Return a copy of 'sequence', sorted by 'sort_fn'.

    'sort_fn' -- The comparison function to use.  If 'None', the default
    (built-in 'cmp') is used."""

    sequence = list(sequence)
    if sort_fn is None:
        sort_fn = cmp
    sequence.sort(sort_fn)
    return sequence


def binarySearch(sequence, value, compare=cmp):
    """Find 'value' in sorted 'sequence' by binary search.

    'sequence' -- A sequence of values.  It is assumed to be sorted by
    'compare'.

    'compare' -- A comparison function.

    returns -- The index of the largest element in 'sequence' smaller
    than 'value', or -1 if there is no such element."""

    if len(sequence) == 0:
        return -1
    if compare(value, sequence[0]) < 0:
        return -1
    if compare(value, sequence[-1]) > 0:
        return len(squence) - 1

    i0 = 0
    i2 = len(sequence) - 1
    while True:
        if i2 <= i0 + 1:
            return i2 - 1
        i1 = (i0 + i2) // 2
        if compare(value, sequence[i1]) < 0:
            i2 = i1
        else:
            i0 = i1


def mapFromKeys(key_sequence, value_function):
    """Construct a map from a sequence of keys.

    A map is created whose keys are the elements of 'key_sequence'.  For
    each key, the corresponding value is constructed from the key using
    'value_function'.  If 'sequence' contains a particular key more than
    once, only one is placed in the map (which one is undefined).

    'key_sequence' -- A sequence of key values.

    'value_function' -- A callable for determining the value for each
    element of the sequence.  It is invoked for each key, passing the
    kay as the single argument."""
    
    result = {}
    for key in key_sequence:
        result[key] = value_function(key)
    return result


def mapFromValues(key_function, value_sequence):
    """Construct a map from a sequence of values.

    A map is created whose values are the elements of 'value_sequence'.
    For each value, the corresponding key is constructed from the value
    using 'key_function'.  If 'key_function' assigns the same key to
    more than one element of the sequence, only one element is actually
    used in the map (which one is undefined).

    'key_function' -- A callable for determining the key for each
    element of the sequence.  It is invoked for each value, passing
    the value as the single argument.

    'value_sequence' -- A sequence of values."""
    
    result = {}
    for value in value_sequence:
        result[key_function(value)] = value
    return result


def invertMap(map):
    """Produce a dictionary by inverting keys and values of 'map'."""

    return dict([ (value, key) for key, value in map.items() ])


def remove(dict, key):
    """Get and remove a dictionary item.

    'dict' -- The dictionary from which to get and remove the item.

    'key' -- The key of the item to get and remove.

    returns -- The value corresponding to 'key' in 'dict'.  

    raises -- 'KeyError' if 'dict' has no key 'key'."""
    
    value = dict[key]
    del dict[key]
    return value


def popkey(map, key, default=None):
    """Get and remove a dictionary item.

    'dict' -- The dictionary from which to get and remove the item.

    'key' -- The key of the item to get and remove.

    'default' -- The value to return if 'key' is not in 'map'.

    returns -- The value corresponding to 'key' in 'dict', or 'default'
    if none."""

    if key in map:
        result = map[key]
        del map[key]
        return result
    else:
        return default


def getHostName():
    """Return the name of this host."""

    import socket

    try:
        return socket.gethostbyname_ex(socket.gethostname())[0]
    except socket.error:
        return "(unknown)"


def isMap(object):
    """Determine whether an object satisfies the mapping protocol.

    returns -- True if 'object' satisfies the map protocol as
    specified.""" 

    # FIXME.  There probably is a more consistent way to do this.

    # If the object is an instance of the standard 'dict' class (or a
    # subclass of it), it must satisfy the mapping protocol.
    if isinstance(object, dict):
        return True
    # Check for the required methods.
    for method_name in ("get", "__getitem__", "__len__", ):
        if not hasattr(object, method_name):
            return False
    # The object checks out.
    return 1


def mkdirRecursively(path):
    """Create a directory, including parent directories if necessary."""

    parent, name = os.path.split(path)
    if parent != "" and not os.path.isdir(parent):
        mkdirRecursively(parent)
    os.mkdir(path)


def rmRecursively(path):
    """Remove the file or directory at 'path'.

    If 'path' is a directory, its contents are removed first."""

    if os.path.isdir(path):
        # Construct a list of contents of the directory.
        contents = map(lambda e, path=path: os.path.join(path, e),
                       os.listdir(path))
        # Remove them all.
        map(rmRecursively, contents)
        # Remove the directory itself.
        os.rmdir(path)
    else:
        os.unlink(path)


