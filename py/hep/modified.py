#-----------------------------------------------------------------------
#
# modified.py
#
# Copyright (C) 2004 by Alex Samuel.
#
#-----------------------------------------------------------------------

"""Support for modification tracking."""

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Modified(object):
    """Mixin or base class for modification tracking.

    The 'is_modified' attribute can be checked or set to indicate
    whether this object was modified.

    In addition, the 'watch_modified' attribute contains a list of other
    objects to check when determining modification.  If any of them is
    modified, this object is also considered modified.  If the
    modification flag on this object is set to false, the same is done
    for all objects in the 'watch_modified' list too."""

    def __init__(self, modified=False):
        self.__is_modified = bool(modified)


    def __get_is_modified(self):
        is_modified = self.__is_modified
        try:
            watch_modified = self.watch_modified
        except AttributeError:
            pass
        else:
            is_modified = reduce(
                lambda s1, s2: s1 or s2,
                [ s.is_modified
                  for s in watch_modified
                  if hasattr(s, "is_modified") ],
                is_modified)
        return is_modified


    def __set_is_modified(self, modified):
        try:
            old_modified = self.__is_modified
        except AttributeError:
            return
        self.__is_modified = modified
        if not modified:
            try:
                watch_modified = self.watch_modified
            except AttributeError:
                pass
            else:
                for item in watch_modified:
                    if hasattr(item, "is_modified"):
                        item.is_modified = False


    is_modified = property(__get_is_modified, __set_is_modified)
    


#-----------------------------------------------------------------------

class Dict(dict, Modified):

    def __init__(self, *args):
        dict.__init__(self, *args)
        Modified.__init__(self)


    def __repr__(self):
        return "Dict({%s})" \
               % ", ".join([ "%r: %r" % i for i in self.items() ])


    watch_modified = property(lambda self: self.values())


    def __delitem__(self, key):
        self.is_modified = True
        dict.__delitem__(self, key)


    def __setitem__(self, key, value):
        self.is_modified = True
        dict.__setitem__(self, key, value)


    def clear(self):
        self.is_modified = True
        dict.clear(self)


    def pop(self, *args):
        self.is_modified = True
        return dict.pop(self, *args)


    def popitem(self):
        self.is_modified = True
        return dict.popitem(self)
    

    def setdefault(self, key, default):
        self.is_modified = True
        return dict.setdefault(self, key, value)


    def update(self, other):
        self.is_modified = True
        dict.update(self, other)



#-----------------------------------------------------------------------

class List(list, Modified):

    def __init__(self, *args):
        list.__init__(self, *args)
        Modified.__init__(self)


    def __repr__(self):
        return "hep.modified.List(%s)" % ", ".join(map(repr, self))


    def __str__(self):
        return "[" + ",".join(map(str, self)) + "]"


    watch_modified = property(lambda self: self)


    def __delitem__(self, item):
        self.is_modified = True
        list.__delitem__(self, item)


    def __delslice__(self, *args):
        self.is_modified = True
        list.__delslice__(self, *args)


    def __setitem__(self, i, value):
        self.is_modified = True
        list.__setitem__(self, i, value)


    def __setslice__(self, *args):
        self.is_modified = True
        list.__setslice__(self, *args)


    def append(self, value):
        self.is_modified = True
        list.append(self, value)


    def extend(self, more):
        self.is_modified = True
        list.extend(self, more)


    def insert(self, i, value):
        self.is_modified = True
        list.insert(self, i, value)


    def pop(self, *args):
        self.is_modified = True
        return list.pop(self, *args)


    def remove(self, value):
        self.is_modified = True
        list.remove(self, value)


    def reverse(self):
        self.is_modified = True
        list.reverse(self)


    def sort(self, *args):
        self.is_modified = True
        list.sort(self)



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def Property(name):
    """Return a 'property' object that sets the 'is_modified' flag.

    'name' -- The property name.

    returns -- A 'property' object with 'get' and 'set' methods.  The
    'set' method sets the 'is_modified' flag on the containing object to
    true when the property values is changed."""

    attr_name = "__" + name

    def get(self):
        try:
            return self.__dict__[attr_name]
        except KeyError:
            raise AttributeError, name

    def set(self, value):
        if attr_name not in self.__dict__ \
           or self.__dict__[attr_name] != value:
            self.__dict__[attr_name] = value
            self.is_modified = True

    return property(get, set)
        


