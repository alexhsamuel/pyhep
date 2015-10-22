#-----------------------------------------------------------------------
#
# module hep.mctruth
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Manipulation and management of Monte Carlo truth information.

This module assumes Monte Carlo (MC) truth information is stored in
tables with a specific schema.  Each particle in a decay is stored as
one row in the table.  Particles from multiple decays may be stored in
the same table, but generally all particles in a decay should be stored
in sequential rows.

  - The 'id' column contains the particle species identification, as a
    PDG ID number.

  - The 'cc_id' column contains the ID number of the charge conjugate
    particle, as a PDG ID number.

  - The 'parent_offset' column contains the *relative* row index of the
    particle's parent.  If the value is zero, the particle has no
    parent.  Otherwise, to obtain the row for a particle's parent, add
    the particle's own row index to 'parent_offset', and look up that
    row.

  - The 'child_begin_offset' and 'child_end_offset' columns contain the
    *relative* row indices of the first and one-past-the-last childred
    of the particle.  The children must be in consecutive rows.  As with
    'parent_offset', the paticle's own row index must be added to these
    values.  The number of children is 'child_end_offset -
    child_begin_offset', which may be zero if there are no children.

The 'parse' function parses a decay in indented textual notation.  Each
line contains the particle ID name for a child decay.  All of a
particle's children's names must be indented more than the particle's
name, and all by the same amount.  Each line may also include a label,
following an equals sign.  This label identifies that particular
particle in the decay.  If no label is provided, one is generated from
the ID name (and may not be unique).  Everything from a hash mark to the
end of a line is ignored as a comment.  For example,

   '# CP violation 'golden mode,' electron channel.
    B+
      J/psi
        e+        = electron
        e-        = positron
      K0  # Monte Carlo program decays K^0 -> Ks.
        K_S0
          pi+     = pi_plus
          pi-     = pi_minus
   '
   
Note that this example uses two-character indents, but any other indent
amount may be used as well.  Other than that, whitespace is ignored.
"""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   hep.bool import *
import hep.fn
from   hep.pdt import default as pdt
import hep.particle
import re

#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

# For internal use; used by 'parse'.

class Particle:

    def __init__(self, label, id):
        self.label = str(label)
        self.id = int(id)
        self.decay_products = []


    def __get_species(self):
        species = pdt.findId(self.id).name
        self.__dict__["species"] = species
        return species


    species = property(__get_species)



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def printTable(table, first_index=0, stable_decays=True):
    """Print MC truth from 'table' starting from particle at 'first_index'.

    Prints MC truth for the specified particle and its descendents in
    tabular format."""

    print "  row  ID                      parent  children"
    print "-----------------------------------------------"

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
        child_begin = i + row["child_offset"]
        child_end = child_begin + row["num_children"]
        # Append all children of this row.
        if stable_decays or not pdt.findId(row["id"]).is_stable:
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
        child_begin = i + row["child_offset"]
        child_end = child_begin + row["num_children"]
        print "%5d  %-20s   %5s %5d-%5d" \
              % (i, pdt.findId(row["id"]).name, parent,
                 child_begin, child_end)
    print


def _printTree(table, index, indent, stable_decays, labels):
    row = table[index]
    pdt_info = pdt.findId(row["id"])
    name = (indent * " ") + pdt_info.name
    child_begin = row["child_offset"] + index
    child_end = child_begin + row["num_children"]
    print "%5d  %-20s   %7.3f %7.3f %7.3f %7.3f   %s" \
          % (index, name, row["en"], row["px"], row["py"],
             row["pz"], str(labels.get(index, "")))
    # Recursively print children too.
    if stable_decays or not pdt_info.is_stable:
        for child_index in range(child_begin, child_end):
            _printTree(table, child_index, indent + 1, stable_decays, labels)
    

def printTree(table, index=0, stable_decays=True, labels={}):
    """Print MC truth from 'table' starting from particle at 'first_index'.

    Prints MC truth for the specified particle and its descendents in a
    tree format.  For each particle, print its row index, particle ID, and
    four-momentum.

    'table' -- A table containing MC truth info.

    'index' -- The index of the root particle to print.

    'stable_decays' -- Whether to include decays of stable particles (as
    determined from the particle data table).

    'labels' -- A map from row indices to strings.  For each row printed
    in the tree, if the row index is a key in this map, the
    corresponding label string is printed at the end of the row."""

    print "  row  ID                      energy    p_x     p_y     p_z"
    print "-------------------------------------------------------------"
    _printTree(table, index, 0, stable_decays, labels)
    print


def buildTable(decay, table, labels):
    """Construct an MC truth table from a 'Decay'.

    'decay' -- A 'Decay' instance.

    'table' -- A list to append to.  This will contain the constructed
    table. 

    'labels' -- A dictionary in which to store label information.  For
    each decay and subdecay, an entry is added whose key is the decay's
    label and whose value is the decay's index."""

    # Keep a work list of subdecays to process, along with the parent
    # index for each.
    work_list = [(decay, -1, )]
    while len(work_list) > 0:
        # Get the next decay to work on.
        decay, parent = work_list.pop(0)
        # Construct the entry.
        index = len(table)
        entry = {}
        entry["id"] = decay.id
        entry["cc_id"] = pdt.findId(decay.id).charge_conjugate.id
        if parent == -1:
            entry["parent_offset"] = 0
        else:
            entry["parent_offset"] = parent - index
        entry["child_begin_offset"] = len(work_list) + 1
        entry["child_end_offset"] = len(work_list) + 1 + len(decay.products)
        # Add it to the result.
        table.append(entry)
        # Update labels.
        labels[decay.label] = index
        # Add child decays to the work list.
        for product in decay.products:
            work_list.append((product, index))


def parse(input):
    """Parse a decay in indented textual notation.

    returns -- A MC truth table containing the decay."""

    if isinstance(input, str):
        input = input.splitlines()
    # Keep a stack of parent decays and their indentation.
    stack = []

    for line in input:
        # Strip comments from the line.
        if "#" in line:
            line = line[:line.index("#")]
        # Ignore blank lines.
        if line.strip() == "":
            continue

        # Count indentation for this line.
        indentation = 0
        while line[indentation] == " ":
            indentation += 1
        # If we are indented more than the previous line, we'll be
        # adding to the decay at the top of the stack.
        if len(stack) == 0 or indentation > stack[-1][0]:
            pass
        # If we are indentated the same as the previous line, this decay
        # will be a sibling of the decay at the top of the stack, so pop
        # it off so that we add to its parent.
        elif indentation == stack[-1][0]:
            stack.pop()
        # If this line is unindented, pop decays off the stack until we
        # reach the right indentation level.  Then pop one more so that
        # the parent is at the top of the stack.
        else:
            while indentation < stack[-1][0]:
                stack.pop()
            if indentation != stack[-1][0]:
                raise ValueError, "invalid indentation"
            stack.pop()

        # Grab the ID name, and the label if provided.
        if "=" in line:
            name, label = line.split("=")
            label = label.strip()
        else:
            name = line
            label = None
        # Look up the ID.
        id = pdt[name.strip()].id
        # Make up a label if none was given.
        if label is None:
            label = pdt.findId(id).symbol_name

        # Build the decay object.
        decay = Particle(label, id)
        # Add it as a decay product of the particle at the top of the
        # stack. 
        if len(stack) > 0:
            stack[-1][1].decay_products.append(decay)
        # Push it on to the stack.
        stack.append((indentation, decay))

    return stack[0][1]
    

def match(decay, mc_truth_table, cc_mode=0, **candidates):
    """Attempt to match MC truth for final-state particles to a decay.

    'decay' -- A pair '(table, labels)', where 'table' contains the
    decay pattern and 'labels' is a dictionary mapping label names to
    rows in 'table'.  This is the return value of 'parse'.

    'mc_truth_table' - A table containing MC truth for an event.

    'cc_mode' -- How to match complex conjugate (CC) decays.  If 1,
    the MC truth must match 'decay'.  If -1, the MC truth must match the
    CC of 'decay'.  If 0, MC truth may match either decay or its CC.

    '**candidates' -- Assignments from label names to row indices in
    'mc_truth_tables'.  These are matched to the corresponding labelled
    rows in 'decay'.

    returns -- 'None' if the match fails.  If the match succeeds,
    returns a dictionary mapping labels of particles that were matched
    (a superset of labels in '**candidates') to the matched rows in the
    MC truth table.

    The match proceeds by associating rows the MC truth table given my
    '**candidates' to corresponding rows in the decay table by matching
    labels.  For each association, the particle ID must be the same.
    The match then continues to the parents of these particles.  If a
    particle is reached from more than one childr, the association from
    the MC truth table to the decay table must be the same along each
    path, and the particle ID must match for each association.  The
    match concludes successfully when all direct and indirect parent
    tracks in the decay table of those given by '**candidates' have been
    matched.

    Note that CC matches are always allowed for self-conjugate particles
    and their subdecay trees, regardless of the value of 'cc_mode'."""

    # Check arguments.
    assert cc_mode in (-1, 0, 1)
    
    # Unpack the decay.  
    decay_table, decay_labels = decay
    # Construct a map from row indices in the decay table to row indices
    # in the MC truth table.  There is an entry for each row in the
    # decay table.  Each entry is 'None', until an association to an MC
    # truth particle is made.
    map_decay_to_mc_truth = len(decay_table) * [None]

    # Construct a work list, which initially contains particles in
    # '**candidates'.  Each entry in the work list is a tuple containing
    # the index in the decay table, the corresponding index in the MC
    # truth table, and the CC mode in this branch.
    work_list = []
    # Loop over '**candidates', which contains initial associations from
    # labels to particles in the MC truth table.
    for label, mc_truth_index in candidates.items():
        # Bail if we don't have MC truth for any initial candidate.
        if mc_truth_index < 0:
            return None
        # Look up the decay table index for this label.
        decay_index = decay_labels[label]
        # Add it to the work list.
        work_list.append((decay_index, mc_truth_index, cc_mode, ))

    # Now process the work list.
    while len(work_list) > 0:
        # Get the next element.
        decay_index, mc_truth_index, cc_mode = work_list.pop()

        # Do we already have an associated MC truth table index for this
        # decay table index?
        expected_mc_truth_index = map_decay_to_mc_truth[decay_index]
        if expected_mc_truth_index is not None:
            # Yes -- we've already reached this particle along another
            # path.  
            if expected_mc_truth_index == mc_truth_index:
                # We have the same association, so everything's fine.
                # Continue on to the next particle.
                continue
            else:
                # The association is different, so the match fails.
                return None

        # If we've already associated this MC truth particle to a
        # different particle in the decay, stop now -- the same MC truth
        # shouldn't appear twice in a decay.
        if mc_truth_index in map_decay_to_mc_truth:
            return None

        # Look up the IDs in the decay table and the MC truth table for
        # this particle.
        decay_row = decay_table[decay_index]
        decay_id = decay_row["id"]
        decay_cc_id = decay_row["cc_id"]
        mc_truth_row = mc_truth_table[mc_truth_index]
        mc_truth_id = mc_truth_row["id"]

        if cc_mode == 1:
            # The match has to be to the ID given in the decay table.
            if decay_id != mc_truth_id:
                return None
            elif decay_cc_id == mc_truth_id:
                # It matched, but this particle ID is self-conjugate.
                # Revert to either CC match for its parents.
                cc_mode = 0
        elif cc_mode == -1:
            # This match has to be to the CC of the ID in the decay table.
            if decay_cc_id != mc_truth_id:
                return None
            elif decay_id == mc_truth_id:
                # It matched, but this particle ID is self-conjugate.
                # Revert to either CC match for its parents.
                cc_mode = 0
        elif cc_mode == 0:
            # We may match either the ID or its CC.
            if decay_id == mc_truth_id and decay_cc_id == mc_truth_id:
                # It matches, and is self-conjugate.  This doesn't
                # determine which CC mode we'll need for the parent.
                pass
            elif decay_id == mc_truth_id:
                # Matched the ID.  Disallow CC matches for the parent.
                cc_mode = 1
            elif decay_cc_id == mc_truth_id:
                # Matched the CC ID.  Disallow non-CC matches for the
                # parent. 
                cc_mode = -1
            else:
                # Matched neither ID nor its CC.
                return None

        # Store the association from decay table to MC truth.
        map_decay_to_mc_truth[decay_index] = mc_truth_index

        # Look up the parent in the decay table, if it has one.
        decay_parent_index = decay_row["parent_offset"]
        if decay_parent_index != 0:
            # Is their a corresponding parent in the MC truth table?
            mc_truth_parent_index = mc_truth_row["parent_offset"]
            if mc_truth_parent_index == 0:
                # Nope.  That's a mismatch.
                return None
            # Add the parent to the work list.
            work_list.append((decay_parent_index + decay_index,
                              mc_truth_parent_index + mc_truth_index,
                              cc_mode, ))

    # The match succeeded.  Return a dictionary mapping labels in the
    # decay table to rows in the MC truth table.
    result = {}
    for label, decay_index in decay_labels.items():
        result[label] = map_decay_to_mc_truth[decay_index]
    return result


def _matchTree(pattern, decay, cc_mode, matches):
    """Recursively match 'pattern' to 'decay', filling in 'matches'.

    returns -- 'is_match, match_cc_mode', where 'is_match' is true if
    the match succeeds, and if so, 'match_cc_mode' contains the actual
    CC mode of the match (which may be different from 'cc_mode', if
    'cc_mode' is zero)."""

    # Get the ID of the pattern particle and its CC.
    pattern_id = pattern.id
    pattern_cc_id = pdt.findId(pattern_id).charge_conjugate.id
    # Get the ID of the decay particle.
    decay_id = decay.id

    if False:
        print "_matchTree(%s, %s, %d)" \
              % (pdt.findId(pattern_id).name,
                 pdt.findId(decay_id).name, cc_mode)

    if cc_mode == 1:
        # The MC truth must match the decay's ID.
        if decay_id != pattern_id:
            return False, None
    elif cc_mode == -1:
        # The MC truth must match the decay's CC ID.
        if decay_id != pattern_cc_id:
            return False, None
    elif cc_mode == 0:
        # We may match either the ID or its CC.
        if decay_id == pattern_id and decay_id == pattern_cc_id:
            pass
        elif decay_id == pattern_id:
            # Matched the ID.  Disallow CC matches for the parent.
            cc_mode = 1
        elif decay_id == pattern_cc_id:
            # Matched the CC ID.  Disallow non-CC matches for the
            # parent.
            cc_mode = -1
        else:
            return False, None

    try:
        label = pattern.label
    except AttributeError:
        pass
    else:
        matches[label] = decay

    pattern_products = pattern.decay_products
    # If the pattern is missing decay information, assume the match is
    # OK.
    if pattern_products is None:
        return True, cc_mode
    num_products = len(pattern_products)

    decay_products = decay.decay_products
    # It must have the same number of children as in the decay pattern.
    if len(decay_products) != num_products:
        return False, None

    # Loop over all permutations of match-ups between children in the
    # decay pattern and children in MC truth.
    for permutations in hep.fn.permute(tuple(range(num_products))):
        success = True
        # In each permutation, match each of the children.
        for i in xrange(num_products):
            # FIXME: If cc_mode is zero, don't we need to require that
            # all children match in the same cc_mode (or zero), i.e.
            # that there aren't both children that match for cc_mode = 1
            # and children that match for cc_mode = -1 ?
            is_match, match_cc_mode = \
                _matchTree(pattern_products[permutations[i]],
                           decay_products[i], cc_mode, matches)
            if not is_match:
                # Match failed.  Bail on this permutation.
                success = False
                break
            elif cc_mode == -match_cc_mode:
                # It matched, but with the wrong CC mode.
                success = False
                break
        # If we went all the way through all the children and matched
        # each without a failure, we're golden.
        if success:
            return True, match_cc_mode
    # None of the permutations worked out.  The match fails.
    return False, None


def matchTree(pattern, particle, cc_mode=0):
    """Attempt to match MC truth for a particle's decay tree.

    Determine whether a pattern (a fragment of a particle decay tree),
    matches a particular particle and its decay products.  The tree
    stricture and particle species in 'pattern' must match those in the
    'particle' exactly (up to charge conjugation, if 'cc_mode' is zero).

    The match begins by comparing the specified row in the decay pattern
    to the MC truth particle.  If the IDs match and the particle in the
    decay pattern has children, the children must match recursively the
    children of the MC truth particle as well.  All match permutations
    of the children in the decay pattern to the children of the MC truth
    particle are attempted.

    'pattern' -- A 'Particle' object, with at least 'id' and
    'decay_products' information, contianing the pattern to match.

    'particle' -- A 'Particle' object.

    'cc_mode' -- How to match charge conjugate (CC) decays.  If 1, the
    species in the 'particle' decay tree must match those in the decay
    pattern.  If -1, the matches must be to CC of the species in decay
    pattern.  If 0, 'particle' may match either the decay pattern or its
    CC.

    returns -- If the match succeeds, a dictionary mapping labels in the
    pattern to particles in the decay tree rooted at 'Particle'.  If the
    match fails, 'None'."""

    matches = {}
    is_match, match_cc_mode = \
        _matchTree(pattern, particle, cc_mode, matches)
    if is_match:
        return matches
    else:
        return None


def findTree(pattern, particle, cc_mode=0):
    for particle in hep.particle.TreeIter(particle):
        matches = matchTree(pattern, particle, cc_mode)
        if matches is not None:
            return matches
    return None


def _parseSpecies(species):
    if ":" in species:
        species, label = species.split(":", 1)
    else:
        label = species
    id = pdt[species].id

    return id, label


def _parseDecay(tokens):
    if tokens[0] == "[":
        del tokens[0]
        
        if tokens[0] in ("[", "]", ):
            raise ValueError, "missing species"

        species = tokens[0]
        del tokens[0]
            
        id, label = _parseSpecies(species)
        decay = hep.mctruth.Particle(label, id)

        while tokens[0] != "]":
            subdecay, tokens = _parseDecay(tokens)
            decay.decay_products.append(subdecay)

        del tokens[0]

        return decay, tokens

    elif tokens[0] == "]":
        raise ValueError, "unmatched ']'"

    else:
        species = tokens[0]
        id, label = _parseSpecies(species)
        del tokens[0]

        decay = hep.mctruth.Particle(label, id)
        decay.decay_products = None

        return decay, tokens


def parseDecay(decay_string):
    decay_string = re.sub("\s", "", decay_string)
    tokens = filter(None, re.split("(]|\[)|,", decay_string))
    decay, tokens = _parseDecay(tokens)
    if tokens:
        raise ValueError, "extra text"
    return decay


def formatDecay(particle):
    if hasattr(particle, "label") \
        and particle.species != particle.label:
        species = "%s:%s" % (particle.species, particle.label)
    else:
        species = particle.species
    children = map(formatDecay, particle.decay_products)
    return "[%s]" % ",".join([species, ] + children)


#-----------------------------------------------------------------------
# script
#-----------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    table, labels = parse(sys.stdin.read())
    printTable(table)
    print labels
