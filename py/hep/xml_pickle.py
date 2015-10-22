#-----------------------------------------------------------------------
#
# module hep.xml_pickle
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Automatic storage and retrieval of Python objects as XML.

This module provides functions to partially or completely automate the
storage of Python objects in an XML format.  Used most simply, these
functions can transform Python objects into XML pickles which contain
enough type information to restore the pickles back into Python objects.
A class may also, by providing additional meta information about their
attributes, cause some type information to be omitted.  This can be used
to produce simpler, easier-to-read XML schema.

Currently, automatic handling of Python objects extends to the most but
not all common data types.  These are listed below.

As in the standard Python pickling, if an object appears more than once
within a single XML document, the second and subsequent appearances are
represented by a back reference to the original appearance.  This allows
the XML pickling to represent and restore arbitrary object relationship
graphs.

As with the standard Python pickling, a class instance is represented by
its class *name* and attributes only.  Therefore, the class itself
must be importable when the instance is restored from XML.

To represent a Python object as an XML file, use 'as_xml_file'.  Provide
the path to the XML file, the Python object, and a tag name to use for
the XML document element (which is arbitrary).  The 'from_xml_file'
function reverses this operation.  To generate only DOM trees instead of
XML files (for instance, for inclusion in a larger XML document), use
'as_dom_node' and 'from_dom_node'.


Each Python object or subobject is represented by an XML element.  The
element's tag name is *not* determined by the object itself; instead it
determined by context.  Most commonly, the for an object that is an
attribute of a containing class instance, the tag name is the object's
attribute name in the instance.  The tag name of the outermost element
(generally, the document element) is arbitrary.  The type and value of
the Python object are represented in the XML element's attributes and
contents. 

Below are listed the representations of the currently-supported Python
types.  For purpose of example, an element tag name of "foo" is used.
The 'id' attribute which appears in some of the examples is described
later.

  - 'None' is represented as

      <foo type='None'/>

  - A numerical value is given as text.  Its type given in the 'type'
    attribute, which can take the value 'int', 'float', or 'long int'.
    For long ints, the text representation does *not* end with a capital
    "L".  For example,

      <foo type='long int'>1234567890</foo>

  - A string is simply encoded with its value.  The 'type' attribute is
    permitted, with the value 'string', but this is not included
    automatically.  For example,

      <foo>I like Python.</foo>

  - The items of a list or tuple are given by 'item' subelements.  The
    'type' attribute is 'list' or 'tuple'.  For example,

      <foo type='tuple' type='item' id='object:135706768'>
       <item type='int'>42</item>
       <item>This is a string.</item>
      </foo>

  - The items of a dictionary are given by 'item' subelements, each of
    which contains one 'key' and one 'value' subelement.  The 'type'
    attribute is 'dictionary'.  For example,

      <foo type='dictionary' id='object:98274018'>
       <item>
        <key>pi</key>
        <value type='float'>3.14159</value>
       </item>
       <item>
        <key>e</key>
        <value type='float'>2.71828</value>
       </item>
      </foo>

  - For a class instance, the 'class' attribute holds the name of the
    class.  Each attribute in the instance dictionary ('__dict__') is
    represented by a similarly-named subelement.  For example, for 'foo'
    declared as such,

      class Foo:
          def __init__(self, value):
              self.public = value
              self.__private = "Hello, world!"

      foo = Foo(42)

    the XML representation would be,

      <foo class='mymodule.Foo' id='object:135044568'>
       <public type='int'>42</public>
       <_Foo__private>Hello, world!</_Foo__private>
      </foo>

    Note that Python's automatic mangling of attribute names beginning
    with two underscores is manifest here.

Elements representing non-atomic objects (lists, tuples, dictionaries,
instances) include an 'id' attribute.  The document represents the
second and subsequent appearances of an object with a back reference.
This saves space and allows the reconstruction of arbitrary object
relationship graphs.  A back reference looks like this:

    <foo idref='object:135044568'/>


A class may control which of its attributes are represented in XML by
defining '__xml_getstate__' and '__xml_setstate__' attribute functions,
similar to the standard Python pickler's '__setstate__' and
'__getstate__'.  The '__xml_getstate__' function should return a
dictionary whose keys are strings representing attribute names, and
whose values are the corresponding attribute values to pickle.  The
'__xml_setstate__' function is passed such a dictionary and is
responsible for reconstructing the instance's attribute dictionary.  The
'__init__' function is not called when restoring an instance.


The default XML representation for objects includes the 'type', 'id',
and 'class' attributes to encode enough information to reconstruct the
Python objects automatically.  For some applications, though, the
generated XML files are too cluttered.  To obviate this, a class may
suppress the type information for an object by converting it to a
string, or by wrapping it in an instance of the 'Object' class.  The XML
generated for an object wrapped in an 'Object' instance will encode the
object's value but not its type

For example, this class defines '__xml_getstate__' to suppress type
information.

    class Foo:
        def __init__(self, value, names):
            self.__value = value
            self.__names = list(names)

        def __xml_getstate__(self):
            return {
                'value': str(self.__value),
                'names': Object(self.__names)
                }

Then this object

    foo = Foo(42, ['Bob', 'Mary', 'Joe'])

is represented as

    <foo class='mymodule.Foo' id='object:12345678'>
     <value>42</value>
     <names>
      <item>Bob</item>
      <item>Mary</item>
      <item>Joe</item>
     </names>
    </foo>
    
When the XML is loaded back, composite objects (lists, tuples,
dictionaries, instances) that do not include type information are
represented by an 'UnknownObject' instance.  The 'UnknownObject' class
includes methods for converting the object to the appropriate Python
type.  For example, class 'Foo' would include this '__xml_setstate__'
method to match the '__xml_getstate__' shown above:

        def __xml_setstate__(self, state):
            self.__value = int(state['value'])
            self.__names = state['names'].asList()

Note the use of the 'asList' method of the value of the names attribute,
which is an 'UnknownObject' instance since type information is not
provided. 

"""

# FIXME: To do:
#
#  - Escape text adequately.
#
#  - Support additional data types.

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import cStringIO
import hep
import new
import string
import sys
import types
import xml.dom
# import xml.dom.DOMImplementation
import xml.dom.minidom
import xml.sax

#-----------------------------------------------------------------------
# exceptions
#-----------------------------------------------------------------------

class SyntaxError(Exception):
    """A syntax error occurred while parsing an XML document."""

    pass



#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Object:
    """An object whose type is not explicit in the XML representation.

    When an object provides its state via '__xml_getstate__', it may
    specify instances of 'Object' to indicate that an object (a class
    instance, dictionary, tuple, or list) should be included without any
    explicit type information.

    The representation of the object is the same as it would be if the
    object was provided itself without wrapping it in an 'Object'
    instance, except that the object's type is not encoded in the
    element attributes.

    When the object is loaded back from XML, it will have the type
    'UnknownObject'.  It is up to '__xml_setstate__' to specify the
    correct type."""

    def __init__(self, object):
        """Wrap an object 'object' for inclusion without type information.

        'object' -- An instance, list, tuple, or dictionary."""

        if type(object) not in [types.InstanceType,
                                types.ListType,
                                types.DictionaryType,
                                types.TupleType]:
            raise ValueError, \
                "wrapped object may not be a %s" % str(type(object))
        self.__object = object
        

    def getObject(self):
        """Return the wrapped object."""

        return self.__object



class UnknownObject:
    """An object retrieved from XML whose type is not known.

    An 'UnknownObject' instance represents an object that was stored as
    XML without any type information, and subsequently retrieved.  To
    complete the construction of a proper Python object, call the
    appropriate method to specify the correct type."""

    def __init__(self, node):
        self.__node = node


    def asInstance(self, klass):
        """Convert the unknown object to a class instance.

        'klass' -- The Python class of which the object is an
        instance."""
        
        return instance_from_dom_node(klass, self.__node)


    def asList(self):
        """Convert the unknown object to a list."""

        return list_from_dom_node(self.__node)


    def asTuple(self):
        """Convert the unknown object to a tuple."""

        return tuple_from_dom_node(self.__node)


    def asDictionary(self):
        """Convert the unknown object to a dictionary."""

        return dictionary_from_dom_node(self.__node)
    


#-----------------------------------------------------------------------
# helper functions
#-----------------------------------------------------------------------

def _node_filter(node):
    """Return 'None' if 'node' is an ingnorable node.

    When parsing an unvalidated XML document, spurious empty text nodes
    are included.  This filter is used to remove them.

    returns -- 'None' if 'node' is a node that can be ignored, or 'node'
    itself otherwise."""

    if node.nodeType == xml.dom.Node.TEXT_NODE \
       and len(string.strip(node.data)) == 0:
        return None
    else:
        return node


def _get_child_nodes(node):
    """Return non-ignorable child nodes of 'node'.

    returns -- Child nodes of 'node' that pass '_node_filter'."""

    return filter(None, map(_node_filter, node.childNodes))


def _get_item_nodes(nodes):
    """Return items of 'nodes' which correspond to items in a container.

    'nodes' -- A sequence of DOM nodes.

    returns -- A subset of 'nodes' which represents items in a list,
    tuple, or dictionary.

    raises -- 'SyntaxError' if 'nodes' contains an unexpected node."""

    # Filter out ignorable nodes.
    nodes = filter(None, map(_node_filter, nodes))
    for node in nodes:
        # Look at element nodes.
        if node.nodeType == xml.dom.Node.ELEMENT_NODE:
            # They should have the tag "item".  Others are erroneous.
            if node.tagName == "item":
                continue
            else:
                raise SyntaxError, \
                      "unexpected item element '%s'" % node.tagName
        # Other node types are erroneous.
        elif node.nodeType == xml.dom.Node.TEXT_NODE:
            raise SyntaxError, "unexpected text in item list"
        else:
            raise SyntaxError, "unexpected node in item list"
    return nodes


def _get_dom_text(node):
    """Return the text in DOM node 'node'.

    'node' -- A DOM element node, which has either no children or a
    single text node child.

    returns -- An empty string, if 'node' is empty.  Otherwise, the text
    contained in the child node of 'node'."""

    if node.nodeType != xml.dom.Node.ELEMENT_NODE:
        raise ValueError
    if len(node.childNodes) == 0:
        # No child node -- an empty string.
        return ""
    # Extract text from children.
    child_nodes = _get_child_nodes(node)
    for child in child_nodes:
        if child.nodeType != xml.dom.Node.TEXT_NODE:
            raise ValueError
    text = string.join(map(lambda n: n.data, child_nodes), "")
    # Convert the text from a Unicode string to an 8-bit string.
    return str(text)


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def add_to_dom_node(node, value):
    """Add a representation of a Python object to a DOM element.

    Adds children to 'node' to represent 'value'.

    'node' -- A DOM element node.

    'value' -- The Python object to represent."""

    document = node.ownerDocument

    # Objects wrapped in an 'Object' instance are special.  We don't
    # encode any type information about them.
    if isinstance(value, Object):
        # Extract the wrapped object, and use it henceforth.
        value = value.getObject()
        include_type_info = 0
    else:
        include_type_info = 1

    # What type of object is it?
    value_type = type(value)

    # For some types (and only if type info is included), we add an 'id'
    # attribute for the first appearance of an object, and refer back to
    # it by ID on subsequent appearances.
    if include_type_info \
       and value_type in [
        types.DictionaryType,
        types.InstanceType,
        types.ListType,
        types.TupleType,
        ]:
        # Generate an XML ID for this instance from the internal Python
        # ID.
        value_id = "object:%s" % str(id(value))
        # Get the object ID dictionary, if this feature is enabled.
        try:
            object_dict = document.__object_dict
        except AttributeError:
            # It's not.  That's OK.
            pass
        else:
            # Have we already represented this instance in this DOM
            # document?
            if object_dict.has_key(value_id):
                # Yes.  Refer back to the previous representation.
                node.setAttribute("idref", value_id)
                # No need to represent it again.
                return node
            else:
                # No, this is the first appearance.  Store the ID so
                # that the next time this instance arises in this DOM
                # document, we can simply refer back.
                node.setAttribute("id", value_id)
                object_dict[value_id] = None

    if value_type is types.StringType:
        # A string.
        if len(value) > 0:
            # A non-empty string is simply encoded as a text node
            # without further ado.
            text_node = document.createTextNode(value)
            node.appendChild(text_node)
        else:
            # An empty string is represented by an empty element.
            pass

    elif value_type is types.InstanceType:
        # A class instance.
        if include_type_info:
            # Store the fully-qualified name of the instance's class.
            try:
                # If the instance or its class defines the
                # '__class_name__' attribute, use its value.
                class_name = value.__class_name__
            except AttributeError:
                # Otherwise, try to guess it.
                class_name = value.__class__.__module__ \
                             + "." + value.__class__.__name__
            node.setAttribute("class", class_name)

        try:
            # Does the object or its class define the '__xml_getstate__'
            # method? 
            xml_getstate_fn = value.__xml_getstate__
        except AttributeError:
            # No.  Just use the instance dictionary as the instance's
            # state. 
            state_dict = value.__dict__
        else:
            # Yes.  Call it to retrieve the instance's state dictionary.
            state_dict = xml_getstate_fn()
            
        # For each element of the state dictionary, generate a child
        # node. 
        for attr_name, attr_value in state_dict.items():
            attr_node = as_dom_node(document, attr_name, attr_value)
            node.appendChild(attr_node)

    else:
        # All other Python types.

        # Store the name of the type, if needed.
        if include_type_info:
            node.setAttribute("type", value_type.__name__)

        if value_type is types.NoneType:
            # Nothing additional needs to be stored for 'None'.
            pass

        elif value_type in [types.ListType, types.TupleType]:
            # For a sequence, add an item child node for each item in
            # the sequence.
            for item in value:
                item_node = as_dom_node(document, "item", item)
                node.appendChild(item_node)

        elif value_type is types.DictionaryType:
            # For a dictionary, add an item for each key-value item.  
            for item_key, item_value in value.items():
                item_node = document.createElement("item")
                item_node.appendChild(
                    as_dom_node(document, "key", item_key))
                item_node.appendChild(
                    as_dom_node(document, "value", item_value))
                node.appendChild(item_node)
        else:
            # Everything else just convert to a string and store.
            content = str(value)
            # Trim the 'L' off the end of the representation of a long
            # int.
            if value_type is types.LongType:
                assert content[:-1] == "L"
                content = content[:-1]
            content_node = document.createTextNode(content)
            node.appendChild(content_node)

    return node


# _dom_implementation = xml.dom.DOMImplementation.DOMImplementation()
_dom_implementation = xml.dom.minidom.DOMImplementation()

def as_dom_node(document, name, value):
    """Construct a DOM element node from a Python object.

    'document' -- The document in which to create the DOM node.

    'name' -- The element tag name.

    'value' -- The Python object to represent.

    returns -- A DOM node object."""

    node = document.createElement(name)
    return add_to_dom_node(node, value)


def as_dom_document(name, value, store_ids):
    """Construct a DOM document from a Python object.

    'name' -- The tag name of the document element.

    'value' -- The Python object to represent.

    'store_ids' -- If true, inclue object IDs to enable representation
    of relationship graphs.

    returns -- A DOM document object."""

    document = _dom_implementation.createDocument(
        namespaceURI=None, qualifiedName=name, doctype=None)
    if store_ids:
        document.__object_dict = {}
    add_to_dom_node(document.documentElement, value)
    return document


def as_xml_file(file, name, value, store_ids=0):
    """Generate an XML file from a Python object.

    'file' -- The file object to which to write the XML.

    'name' -- The tag name of the document element of the XML file.

    'value' -- The Python object to write.

    'store_ids' -- If true, inclue object IDs to enable representation
    of relationship graphs."""

    document = as_dom_document(name, value, store_ids=store_ids)
    # file.write(document.toprettyxml(indent=" ", newl="\n"))
    document.writexml(file)
    # xml.dom.ext.PrettyPrint(
    #    document, file, indent=" ", encoding="ISO-8859-1")


def as_xml_string(name, value, store_ids=0):
    """Generate an XML string from a Python object.

    'name' -- The tag name of the document element of the XML file.

    'value' -- The Python object to write.

    'store_ids' -- If true, inclue object IDs to enable representation
    of relationship graphs."""
    
    file = cStringIO.StringIO()
    as_xml_file(file, name, value, store_ids=store_ids)
    return file.getvalue()


def list_from_dom_node(node):
    """Construct a list from a DOM node."""

    return map(from_dom_node, _get_item_nodes(node.childNodes))


def tuple_from_dom_node(node):
    """Construct a tuple from a DOM node."""

    return reduce(
        lambda t, i: t + (from_dom_node(i), ),
        _get_item_nodes(node.childNodes),
        ())


def dictionary_from_dom_node(node):
    """Construct a dictionary from a DOM node."""

    NO_DEFAULT = hep.Token()

    result = {}
    # Scan over children.  Each represents an item in the dictionary.
    for child_node in _get_item_nodes(node.childNodes):
        # Scan over child elements of the item.  We should find one key
        # element and one value element.
        item_key = NO_DEFAULT
        item_value = NO_DEFAULT
        sub_nodes = filter(None, map(_node_filter, child_node.childNodes))
        for sub_node in sub_nodes:
            if sub_node.nodeType == xml.dom.Node.ELEMENT_NODE:
                tag = sub_node.tagName
                if tag == "key":
                    item_key = from_dom_node(sub_node)
                elif tag == "value":
                    item_value = from_dom_node(sub_node)
                else:
                    # Another element tag is an error.
                    raise SyntaxError, \
                          "unknown element in dictionary item: '%s'" % tag
            else:
                # Another node type is an error.
                raise SyntaxError, "unknow node in dictionary item"
        # Make sure both the key and value were found.
        if item_key is NO_DEFAULT:
            raise SyntaxError, "no key for dictionary item"
        if item_value is NO_DEFAULT:
            raise SyntaxError, "no value for dictionary item"
        # Add the item.
        result[item_key] = item_value

    return result


def instance_from_dom_node(klass, node):
    """Reconstruct a class instance from a DOM node.

    'klass' -- The Python class of which the DOM node represents an
    instance.

    'node' -- A DOM element node.

    returns -- An instance of 'klass'."""

    # Extract the state dictionary of the instance.
    dictionary = {}
    for child_node in _get_child_nodes(node):
        # Each element represents an attribute.  The element's tag name
        # is the attribute name.
        if child_node.nodeType == xml.dom.Node.ELEMENT_NODE:
            attr_name = child_node.tagName
            attr_value = from_dom_node(child_node)
            dictionary[attr_name] = attr_value
        elif child_node.nodeType == xml.dom.Node.TEXT_NODE:
            raise SyntaxError, "unexpected text in instance"
        else:
            raise SyntaxError, "unexpected node in instance: '%s'" \
                  % str(child.nodeType)

    # Now reconstruct the instance.
    try:
        # Does the class have an '__xml_setstate__' method?
        xml_setstate_fn = klass.__xml_setstate__
    except AttributeError:
        # No.  Smush the state into the instance's dictionary.
        instance = new.instance(klass, dictionary)
    else:
        # Yes.  Construct an incomplete instance with an empty
        # dictionary.  Then call the '__xml_setstate__' method to set up
        # the instance. 
        instance = new.instance(klass, {})
        xml_setstate_fn(instance, dictionary)

    return instance


def from_dom_node(node):
    """Reconstruct a Python object from a DOM node.

    'node' -- A DOM element node.

    returns -- A Python object."""

    # Is the node a reference to a previous object?
    if node.hasAttribute("idref"):
        # Yes.  Look up and return the previous object.
        value_id = node.getAttribute("idref")
        return node.ownerDocument.__object_dict[value_id]

    # Is this an instance with an explicit Python class specified?
    elif node.hasAttribute("class"):
        # Yes.  Get the class name and load the class itself.
        class_name = node.getAttribute("class")
        try:
            klass = util.py.load_class(class_name)
        except ImportError, exception:
            raise SyntaxError, "cannot load class '%s': %s" \
                  % (class_name, str(exception))
        # Reconstruct the instance.
        value = instance_from_dom_node(klass, node)

    # Is a Python type specified explicitly?
    elif node.hasAttribute("type"):
        # Yes.  Reconstruct the object as appropriate.
        value_type = node.getAttribute("type")
        if value_type == "dict":
            value = dictionary_from_dom_node(node)
        elif value_type == "float":
            value = float(_get_dom_text(node))
        elif value_type == "int":
            value = int(_get_dom_text(node))
        elif value_type == "list":
            value = list_from_dom_node(node)
        elif value_type == "long int":
            value = long(_get_dom_text(node))
        elif value_type == "tuple":
            value = tuple_from_dom_node(node)
        elif value_type == "None":
            assert len(node.childNodes) == 0
            value = None
        elif value_type == "string":
            value = _get_dom_text(node)
        else:
            raise SyntaxError, "unsupported type '%s'" % value_type
        
    # No type was specified.
    else:
        try:
            # Try to treat it as a string.  
            value = _get_dom_text(node)
        except ValueError:
            # Didn't work.  Return it to the caller as an unknown
            # object.  The caller may complete the reconstruction if it
            # knows the correct type from context.
            return UnknownObject(node)

    # If an object ID was specified, associate this object with it
    # so future references in this document can be resolved.
    if node.hasAttribute("id"):
        value_id = node.getAttribute("id")
        node.ownerDocument.__object_dict[value_id] = value

    return value


def from_xml_file(file):
    """Load a Python object from a file object.

    'file' -- The file object.

    returns -- The pair ('tagName', 'object'), where 'tagName' is the
    tag name of the document element, and 'object' is the object
    constructed from it."""

    # Construct an XML parser.
    try:
        # Parse the document.
        document = xml.dom.minidom.parse(file)
    except xml.sax.SAXParseException, exception:
        # Something went wrong.
        raise SyntaxError, "parse error at %s:%d:%d: %s" \
              % (path,
                 exception.getLineNumber(),
                 exception.getColumnNumber(),
                 exception._msg)

    # Add a dictionary to the document in which we'll reference all
    # objects for which an ID was recorded.  This allows us to
    # reconstruct object graphs.
    document.__object_dict = {}

    # Construct a Python object from the document element.
    node = document.documentElement
    tag_name = str(node.tagName)
    value = from_dom_node(node)
    
    del document.__object_dict
    del node
    document.unlink()
    del document

    return tag_name, value


def from_xml_string(text):
    """Load a Python object from an XML string.

    'text' -- A string containing the XML representation of the object.

    returns -- The pair ('tagName', 'object'), where 'tagName' is the
    tag name of the document element, and 'object' is the object
    constructed from it."""

    return from_xml_file(cStringIO.StringIO(text))


#-----------------------------------------------------------------------
# test code
#-----------------------------------------------------------------------

class Axis:

    def __init__(self, bins, lo, hi):
        self.__bins = bins
        self.__lo = lo
        self.__hi = hi


    def __str__(self):
        return "<Axis %d %f %f>" % (self.__bins, self.__lo, self.__hi)


    def __xml_getstate__(self):
        state = util.py.getPublicDict(self)
        state.update({
            "bins": str(self.__bins),
            "low": str(self.__lo),
            "high": str(self.__hi),
            })
        return state


    def __xml_setstate__(self, state):
        self.__bins = int(util.remove(state, "bins"))
        self.__lo = float(util.remove(state, "low"))
        self.__hi = float(util.remove(state, "high"))
        self.__dict__.update(state)
        


class Histogram:

    def __init__(self, name, bins, lo, hi):
        self.__name = name
        self.__x_axis = Axis(bins, lo, hi)


    def __str__(self):
        return "<Histogram '%s' %s>" % (self.__name, str(self.__x_axis))


    def setAxisTitle(self, title):
        self.__x_axis.title = title


    def __xml_getstate__(self):
        state = util.py.getPublicDict(self)
        state.update({
            "name": self.__name,
            "x-axis": Object(self.__x_axis),
            })
        return state


    def __xml_setstate__(self, state):
        self.__name = util.remove(state, "name")
        self.__x_axis = util.remove(state, "x-axis").asInstance(Axis)
        self.__dict__.update(state)



if __name__ == "__main__":

    import util
    obj = util.Token()
    hist = Histogram("hello", 10, 0.0, 1.0)
    hist.setAxisTitle("photon energy")
    hist.title = "My Nice Histogram"
    x = [1, 2, 3]
    # as_xml_file(open("hist.xml", "w"), "histogram", Object(hist))
    as_xml_file(open("hist.xml", "w"), "histogram", hist)
    del hist

    # hist = from_xml_file(open("hist.xml"))[1].asInstance(Histogram)
    hist = from_xml_file(open("hist.xml"))[1]
    print str(hist)
