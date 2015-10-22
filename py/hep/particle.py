#-----------------------------------------------------------------------
#
# particle.py
#
# Copyright (C) 2004 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Tools for working with particles and decay trees."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from __future__ import generators

from   hep.bool import *
from   hep.lorentz import lab
from   hep.pdt import default as pdt
from   hep.text import center, pad, indent
import sys

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class StdhepParticle(object):

    def __init__(self, row):
        self.stdhep = row["_table"]
        self.index = row["_index"]
        self.row = row
        self.momentum = \
            lab.Momentum(row["en"], row["px"], row["py"], row["pz"])
        self.position = \
            lab.Vector(row["t"], row["x"], row["y"], row["z"])
        self.id = row["id"]


    def __str__(self):
        e, px, py, pz = lab.coordinatesOf(self.momentum)
        return "STDHEP particle %s, momentum=(%.1f, %.1f, %.1f, %.1f)" \
               % (self.species, e, px, py, pz)


    def __get_species(self):
        species = pdt.findId(self.id).name
        self.__dict__["species"] = species
        return species


    species = property(__get_species)


    def __get_parent(self):
        offset = self.row["parent_offset"]
        if offset == 0:
            return None
        else:
            return StdhepParticle(self.stdhep[self.index + offset])


    parent = property(__get_parent)


    def __get_parent2(self):
        try:
            offset = self.row["parent2_offset"]
        except KeyError:
            return None
        if offset == 0:
            return None
        else:
            return StdhepParticle(self.stdhep[index + offset])


    parent2 = property(__get_parent2)


    def __get_decay_products(self):
        row = self.row
        stdhep = self.stdhep
        index = self.index
        start = row["child_offset"]
        end = start + row["num_children"]
        products = [ StdhepParticle(stdhep[offset + index])
                     for offset in xrange(start, end) ]
        self.__dict__["decay_products"] = products
        return products


    decay_products = property(__get_decay_products)



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def StdhepIter(stdhep):
    """An iterator over root particles in a STDHEP table.

    The iterator yields all parentless particles in 'stdhep'."""

    iter = stdhep.select("parent_offset == 0")
    while True:
        yield StdhepParticle(iter.next())


def TreeIter(particle):
    """An iterator over direct and indirect decay products of 'particle'.

    The iterator yields 'particle', its decay products, and recursively
    their decay products."""

    yield particle
    for child in particle.decay_products:
        child_iter = TreeIter(child)
        while True:
            yield child_iter.next()


def printTree(particle, indentation=0, momenta=True, positions=False,
              omit_stable=False, index=False, heading=True, labels={},
              output=sys.stdout):
    """Print the decay tree for 'particle'.

    'particle' -- A 'Paritcle' object.

    'indentation' -- The number of spaces to indent the output.

    'momenta' -- If true, print particles' four-momentum components in
    the lab frame.

    'positions' -- If true, print particles' four-position components in
    the lab frame.

    'omit_stable' -- If true, don't show decays of particles categorized
    as stable in the particle data table.

    'index -- If true, show the table row index for each particle.  Each
    'Particle' object must have an 'index' attribute.

    'heading' -- If true, print a heading on the decay tree."""

    line = ""
    head_line = ""
    if index:
        line += "%5d " % particle.index
        head_line += "index "
    line += indent(particle.species, indentation, 20)
    head_line += center("species", 20)
    if momenta:
        e, px, py, pz = lab.coordinatesOf(particle.momentum)
        line += " %7.3f %7.3f %7.3f %7.3f" % (e, px, py, pz)
        head_line += center(" lab momentum", 32)
    if positions:
        t, x, y, z = lab.coordinatesOf(particle.position)
        line += " %7.3f %7.3f %7.3f %7.3f" % (t, x, y, z)
        head_line += center(" lab position", 32)
        
    label_list = []
    if hasattr(particle, "label"):
        label_list.append(particle.label)
    for key, value in labels.items():
        if value == particle:
            label_list.append(key)
    line += "  " + ",".join(label_list)
    head_line += center(" labels", 12)

    if heading:
        print >> output, head_line
        print >> output, "-" * len(head_line)
    print >> output, line
    # Recursively print children too.
    if (not omit_stable or not pdt_info.is_stable) \
        and particle.decay_products:
        for child in particle.decay_products:
            printTree(child, indentation + 1, momenta, positions,
                      omit_stable, index, heading=False, labels=labels,
                      output=output)


def getRoot(particle):
    """Return the root anscestor of 'particle'.

    returns -- The direct or indirect parent of 'particle' which itself
    is parentless."""

    while particle.parent is not None:
        particle = particle.parent
    return particle


def printStdhep(table, first_index):
    """Print an MC truth table for a particle decay tree.

    'table' -- A STDHEP table.

    'first_index' -- The index of the parent particle whose tree to print.

    Prints MC truth for the specified particle and its descendents in
    tabular format."""

    print "  row  species                    parents     children"
    print "------------------------------------------------------"

    # First collect the indices of rows that need to be included.  These
    # rows include that given by 'first_index', and its direct and
    # indirect descendents.  Build the result here.  
    indices = [first_index]
    # 'indices' doubles as our worklist, and 'position' is the start of
    # the worklist.
    position = 0
    # Loop until we've considered all the rows we need to.
    while position < len(indices):
        i = indices[position]
        # Get the row.
        row = table[i]
        child_begin = i + row["child_begin_offset"]
        child_end = i + row["child_end_offset"]
        # Append all children of this row.
        for j in range(child_begin, child_end):
            indices.append(j)
        # Done with this row.
        position += 1
    # Put the rows into numerical order.
    indices.sort()

    # Print the rows.
    for i in indices:
        row = table[i]
        if row["parent_offset"] == 0:
            parent = "   "
        else:
            parent = "%5d" % (i + row["parent_offset"])
        if row["parent2_offset"] == 0:
            parent2 = "   "
        else:
            parent2 = "%5d" % (i + row["parent2_offset"])
        child_begin = i + row["child_begin_offset"]
        child_end = i + row["child_end_offset"]
        if child_begin == child_end:
            children = "      -     "
        else:
            children = "%5d -%5d" % (child_begin, child_end)
        print "%5d  %-20s   %5s %5s %s" \
              % (i, pdt.findId(row["id"]).name, parent, parent2,
                 children)
    print


