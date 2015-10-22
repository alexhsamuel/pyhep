#-----------------------------------------------------------------------
#
# module pdt.py
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Particle data information.

Contains classes for representing particle properties data, including
both fundamental physical properties (such as mass, width, and spin)
and other attributes (such as Monte Carlo identification numers).

Includes functions for loading particle data from standard file formats.
"""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

import copy
from   hep.bool import *
import hep.config
import os
import re
import sys

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class Decay:
    """A decay mode of a particle.

    Attributes of a 'Decay' include,

    'fraction' -- The branching fraction of this decay.

    'parent' -- The name of the decaying particle.

    'products' -- A sequence of particle names of the decay products.
    """

    def __init__(self, parent, products, fraction):
        self.parent = parent
        self.products = tuple(products)
        self.fraction = fraction


    def __repr__(self):
        return "Decay(%s, %s, %f)" \
               % (repr(self.parent), repr(self.products), self.fraction)


    def __str__(self):
        return "%s -> %s (BF=%f)" \
               % (self.parent, " ".join(self.products), self.fraction)



class Particle:
    """A particle species.

    Attributes of a 'Particle' include,

    'name' -- The particle's canonical name.

    'aliases' -- A list of additional names by which this particle is
    known.

    'isStable' -- Non-zero if the particle is stable.

    'type' -- A string representing the particle's type.

    'id' -- The particle's LUND Monte Carlo ID number.

    Also physical quantities such as 'mass', 'width', 'charge', 'spin',
    'lifetime', etc. """

    def __init__(self, name, **attributes):
        """Construct a particle species record.

        'name' -- The particle's canonical name.

        '**attributes' -- Additional attributes with which to initialize
        the particle."""

        self.name = name
        self.aliases = []
        self.symbol_name = _makeSymbolName(name)
        self.__dict__.update(attributes)


    def __repr__(self):
        return "Particle(%s)" % self.name


    def __str__(self):
        return self.name


    def addAlias(self, alias_name):
        """Add a new alias for this particle."""

        try:
            aliases = self.aliases
        except AttributeError:
            aliases = []
            self.aliases = aliases
        aliases.append(alias_name)



class Table(dict):

    def update(self, other):
        """Update particle data from dictionary 'other'.

        If 'other' is a 'Table' instance, individual particles are
        merged together."""

        if isinstance(other, Table):
            for name, other_particle in other.iteritems():
                try:
                    particle = self[name]
                except KeyError:
                    self[name] = copy.copy(other_particle)
                else:
                    particle.__dict__.update(other_particle.__dict__)
        else:
            dict.update(self, other)


    def add(self, particle):
        """Add a new particle to the table.

        'particle' -- A 'Particle' instance."""
        
        self[particle.name] = particle
    

    def getdefault(self, name):
        """Look up a particle by name, or create a new one.

        'name' -- A particle name.

        returns -- The particle named 'name' in the table.  If there is
        not one, one is added and returned."""

        try:
            return self[name]
        except KeyError:
            particle = Particle(name)
            self[name] = particle
            return particle


    def findId(self, id):
        """Find a particle in the table with a specified ID.

        'id' -- An ID value.

        returns -- A particle in the table whose 'id' attribute is as
        specified.  If there is more than one such particle, an
        (undefined) single one is returned.

        raises -- 'KeyError' if there is no particle in the table with
        specified ID."""

        for particle in self.itervalues():
            try:
                value = particle.id
            except AttributeError:
                pass
            else:
                if value == id:
                    return particle

        raise KeyError, "no particle with ID %d" % id



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def _warning(message):
    print >> sys.stderr, "warning: %s" % message


def _sloppyConvertString(text):
    """Attempt to convert a string to a numerical value.

    'text' -- A string.

    returns -- 'text' converted to a numerical value, if possible.
    First 'int' is attempted, then 'long', then 'float'.  If 'text'
    cannot be converted to a numerical value, it is returned as a
    string."""

    try:
        return int(text)
    except ValueError:
        pass
    try:
        return long(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return str(text)


def _makeSymbolName(name):
    if name.startswith("anti-"):
        name = name[5:] + "_bar"
    name = name.replace("*", "_star")
    name = name.replace("'", "_prime")
    name = name.replace("+", "_plus")
    name = name.replace("-", "_minus")
    name = name.replace("(", "_")
    name = name.replace(")", "")
    name = name.replace("-", "_")
    name = name.replace("/", "")
    return name


def loadPdtFile(path):
    """Load particle data from a PDT table file.

    'path' -- The path to a PDT table file (typically named "pdt.table"
    or similar.

    returns -- A 'Table' instance containing the particle data."""

    # Start with a blank table.
    table = Table()

    # Process each line in the file.
    for line in open(path):
        if line.startswith("end"):
            # Stop processing at the "end" line.
            break
        if line.strip() == "":
            # Empty line; skip it.
            continue
        if line.startswith("*"):
            # Comment line; skip it.
            continue

        # Break the line into parts at whitespace.
        parts = line.split()
        # The first part tells what kind of line this is.
        command = parts[0]

        if command == "add":
            if parts[1] == "p":
                # Add a new particle
                table.add(Particle(
                    type=parts[2],
                    name=parts[3],
                    id=int(parts[4]),
                    mass=float(parts[5]),
                    width=float(parts[6]),
                    max_Dm=float(parts[7]),
                    charge=int(parts[8]) / 3.,
                    spin=int(parts[9]) / 2.,
                    range=float(parts[10]) * 0.001,
                    is_stable=False,
                    ))
            else:
                _warning("add of unknown object '%s'" % parts[1])

        elif command == "sets":
            if parts[1] == "p":
                # Set an attribute of an existing particle.
                name = parts[2]
                try:
                    particle = table[name]
                except KeyError:
                    _warning("no such particle '%s' in sets" % name)
                else:
                    if parts[3] == "isStable":
                        setattr(particle, "is_stable",
                                bool(int(parts[4])))
                    else:
                        setattr(particle, parts[3],
                                _sloppyConvertString(parts[4]))
            else:
                _warning("sets of unknown object '%s'" % parts[1])

        else:
            _warning("unknown command '%s'" % command)

    for particle in table.values():
        id = particle.id
        try:
            particle.charge_conjugate = table.findId(-id)
        except:
            particle.charge_conjugate = particle

    return table

        
def parseDecay(str):
    """Parse a decay string into names of parent and decay products.

    'str' -- The string representing the decay, of the form
    "PARENT -> PRODUCT1 PRODUCT2 ...".

    returns -- '(parent, products)', where 'parent' is the name of the
    decaying particle, and 'products' is a sequence of names of decay
    products.

    throws -- 'ValueError' if the syntax of 'str' is incorrect."""

    try:
        parent, products = str.split("->")
    except ValueError:
        raise ValueError, "syntax error"

    parent = parent.strip()
    products = products.strip().split(" ")
    return parent, products


#-----------------------------------------------------------------------
# data
#-----------------------------------------------------------------------

default = None

pickle_path = os.path.join(hep.config.data_dir, "pdt.pickle")
if not os.path.isfile(pickle_path):
    sys.stderr.write("WARNING: particle data file %s does not exist"
                     % pickle_path)
else:
    try:
        import cPickle
        default = cPickle.load(open(pickle_path))
    except Exception, ex:
        sys.stderr.write(
            "WARNING: could not read particle data file %s:\n  %s\n"
            % (pickle_path, str(ex)))


#-----------------------------------------------------------------------
# standalone script
#-----------------------------------------------------------------------

if __name__ == "__main__":
    # Use the default table.
    table = default

    if len(sys.argv) not in (1, 2, 3):
        print >> sys.stderr, "Usage: particle_data.py NAME [ ATTRIBUTE ]"
        sys.exit(1)

    if len(sys.argv) == 1:
        # Print the names of known particles.
        names = table.keys()
        names.sort()
        print " ".join(names)
        sys.exit(0)
        
    name = sys.argv[1]
    try:
        particle = table[name]
    except KeyError:
        print >> sys.stderr, "no particle '%s' found" % name
        sys.exit(2)

    if len(sys.argv) == 2:
        # Print the name first.
        print "%-12s %s" % ("name:", name)
        # Now other attributes.
        for key, value in particle.__dict__.iteritems():
            # Already printed the name; skip it here.
            if key == "name":
                continue
            # Format decays specially.
            elif key == "decays":
                # Sort the decays in order of decreasing branching
                # fraction. 
                decays = value[:]
                decays.sort(lambda d1, d2: -cmp(d1.fraction, d2.fraction))
                # Print them out.
                prefix = "decays:     "
                for decay in decays:
                    fraction = decay.fraction
                    # If the fraction is at least 1%, write as percent.
                    if fraction >= 0.01:
                        fraction = "%5.2f %%  " % (fraction * 100)
                    # Otherwise, use scientific notation.
                    else:
                        fraction = "%9.2e" % fraction
                    print "%s %s  %s" \
                          % (prefix, fraction, " ".join(decay.products))
                    prefix = "            "
            # Just print out other attributes.
            else:
                print "%-12s %s" % (key + ":", str(value))

    elif len(sys.argv) == 3:
        attribute = sys.argv[2]
        try:
            value = getattr(particle, attribute)
        except AttributeError:
            print >> sys.stderr, \
                  "particle has no attribute '%s'" % attribute
            sys.exit(3)
        else:
            if attribute == "decays":
                for decay in value:
                    print "%9.2e  %s" \
                          % (decay.fraction, " ".join(decay.products))
            else:
                print value
