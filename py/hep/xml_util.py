#-----------------------------------------------------------------------
#
# xml.py
#
# Copyright 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""XML utility functions."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import xml.dom.minidom as dom

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class ParseError(Exception):

    pass


#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def removeWhitespaceText(node):
    """Recursively remove text nodes containing only whitespace from 'node'."""

    children = list(node.childNodes)
    for child in children:
        if child.nodeType == child.TEXT_NODE \
           and str(child.nodeValue).strip() == "":
            node.removeChild(child)
        else:
            removeWhitespaceText(child)


def parseTextElement(node):
    """Parse an element node containing a single text node.

    'node' -- A DOM node.

    returns -- '(name, text)' where 'name' is the element name and
    'text' is the contents of the text node."""
    
    name = node.nodeName
    if len(node.childNodes) != 1:
        raise ParseError, "unexpected childen in text node"
    child = node.childNodes[0]
    if child.nodeType != child.TEXT_NODE:
        raise ParseError, "unexpected child in text node"
    text = child.nodeValue
    return str(name), str(text).strip()


def parseTextElements(node):
    """Parse an element containing several text elements.

    The node is assumed to contain zero or more child elements, each of
    which contains a single text node.  These subelements are collected
    into a dictionary, in which the keys are the child elements' names'
    and the values are the corresponding text node contents.

    No child element name may appear more than once; in case of a
    duplicate, a 'ParseError' is raised.

    'node' -- A DOM node.

    returns -- '(name, attributes, subelements)' where 'name' is the
    element name of 'node', 'attributes' contains attribute definitions,
    and 'subelements' contains the information in its children
    elements."""

    # Get the element name.
    name = node.nodeName
    # Collect attributes.
    attributes = {}
    for key in node.attributes.keys():
        attributes[str(key)] = str(node.attributes.get(key).nodeValue)
    # Collect subelements into a dictionary.
    subelements = {}
    for child in node.childNodes:
        # Get the child's text contents.
        child_name, child_text = parseTextElement(child)
        # Make sure this is not a duplicate name.
        if child_name in subelements:
            raise ParseError, \
                  "duplicate element %s in %s" % (child_name, name)
        # Store it.
        subelements[child_name] = child_text
        
    return name, attributes, subelements


def createElement(document, name, text):
    node = document.createElement(name)
    text_node = document.createTextNode(text)
    node.appendChild(text_node)
    return node


def loadAsDom(path):
    return dom.parse(file(path))
    

def makeDomDocument():
    return dom.Document()
