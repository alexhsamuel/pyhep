#-----------------------------------------------------------------------
#
# module hep.fn
#
# Copyright 2003 by Alex Samuel.  All rights reserved.
#
#-----------------------------------------------------------------------

"""Functional programming support."""

#-----------------------------------------------------------------------
# imports
#-----------------------------------------------------------------------

from   __future__ import generators

from   hep import enumerate, Token

_NO_ARG = Token()

#-----------------------------------------------------------------------
# exceptions
#-----------------------------------------------------------------------

class NotFoundError(Exception):
    pass



#-----------------------------------------------------------------------
# classes
#-----------------------------------------------------------------------

class GroupingIterator:
    """An iterator which groups similar elements.

    A 'GroupingIterator' object returns groups of consecutive items from
    another iterator.  Each call to 'next' returns the next sequence of
    consecutive items from the underlying iterator which satisfy the
    grouping function."""


    def __init__(self, iterable, group_fn):
        """Construct a new grouping iterator.

        'iterable' -- An iterator or iterable object on which to base
        the grouping iterator.

        'group_fn' -- The grouping predicate.  This function is called
        with two arguments, and returns true if the items are considered
        in the same group.  This predicate should be commutative and
        transitive."""

        self.__iterator = iter(iterable)
        self.__group_fn = group_fn


    def __iter__(self):
        return self


    def next(self):
        """Returns the next group of items.

        Items are extracted and accumulated from underlying iterator as
        long as the items are in the same group.

        returns -- A sequence of items from the underlying iterator."""
        
        # Get the first item.  We may have one hanging around;
        # otherwise, get it from the underlying iterator.
        try:
            first_item = self.__next_item
            del self.__next_item
        except AttributeError:
            # If we get a 'StopIteration' while obtaining the first
            # item, the iteration is all finished, so let the exception
            # propagate up. 
            first_item = self.__iterator.next()
            
        # Keep getting items as long as they are in the same group.
        results = [first_item]
        while 1:
            try:
                another_item = self.__iterator.next()
            except StopIteration:
                # Out of additional items.
                return results

            # Is this item in the same group?
            if self.__group_fn(first_item, another_item):
                # Yes.  Add it to the accumulated results, and go on to
                # the next item.
                results.append(another_item)
            else:
                # No.  Save it for next time, and return the results not
                # including this most recent item.
                self.__next_item = another_item
                return results



#-----------------------------------------------------------------------

class Injector(object):

    def __init__(self, sequence, cyclic=False):
        self.sequence = sequence
        self.index = 0
        self.cyclic = cyclic


    def insert(self, value):
        if self.index >= len(self.sequence):
            if self.cyclic:
                self.index = 0
            else:
                raise StopIteration
        self.sequence[self.index] = value
        self.index += 1


    def __lshift__(self, value):
        return self.insert(value)



#-----------------------------------------------------------------------
# functions
#-----------------------------------------------------------------------

def first(sequence, predicate):
    """Return the first element of 'sequence' for which 'predicate' holds.

    'sequence' -- A sequence.

    'predicate' -- A callable that takes one argument.

    returns -- The first element of 'sequence' for which 'predicate'
    returns a true value.

    raises -- 'NotFoundError' if 'predicate' returns true for no element
    of 'sequence'."""

    for element in sequence:
        if predicate(element):
            return element
    raise NotFoundError


def firstIndex(sequence, predicate):
    """Finds the first element of 'sequence' for which 'predicate' holds.

    'sequence' -- A sequence.

    'predicate' -- A callable that takes one argument.

    returns -- The index of the first element of 'sequence' for which
    'predicate' returns a true value, or -1 if none is found."""

    for index in xrange(0, len(sequence)):
        if predicate(sequence[index]):
            return index
    return -1


def maxmap(sequence, score_fn):
    """Return the largest element of 'sequence' evaluated by 'score_fn'.

    'sequence' -- A non-empty sequence.

    'score_fn' -- A callable which takes one argument, an element of
    the sequence, and returns a score for that element.

    returns -- The element of 'sequence' for which 'score_fn' returns
    the largest value.  If there is a tie, the first such element is
    returned.

    raises -- 'ValueError' if 'sequence' is empty."""

    if len(sequence) == 0:
        raise ValueError, "max of empty sequence"

    best_element = None
    best_score = None
    for element in sequence:
        score = score_fn(element)
        if best_score is None \
           or score > best_score:
            best_element = element
            best_score = score

    return best_element


def minmap(sequence, score_fn):
    """Return the smallest element of 'sequence' evaluated by 'score_fn'.

    'sequence' -- A non-empty sequence.

    'score_fn' -- A callabale which takes one argument, an element of
    the sequence, and returns a score for that element.

    returns -- The element of 'sequence' for which 'score_fn' returns
    the smallest value.  If there is a tie, the first such element is
    returned.

    raises -- 'ValueError' if 'sequence' is empty."""

    if len(sequence) == 0:
        raise ValueError, "min of empty sequence"

    best_element = None
    best_score = None
    for element in sequence:
        score = score_fn(element)
        if best_score is None \
           or score < best_score:
            best_element = element
            best_score = score

    return best_element


def minmax(score_fn, sequence):
    """Return the smallest and largest element of 'sequence'.

    'score_fn' -- A callabale which takes one argument, an element of
    the sequence, and returns a score for that element.

    'sequence' -- A non-empty sequence.

    returns -- The elements of 'sequence' for which 'score_fn' returns
    the smallest and largest values, respectively.

    raises -- 'ValueError' if 'sequence' is empty."""

    if score_fn is None:
        score_fn = lambda f: f
    if len(sequence) == 0:
        raise ValueError, "minmax of empty sequence"

    min_element = None
    min_score = None
    max_element = None
    max_score = None
    for element in sequence:
        score = score_fn(element)
        if min_score is None \
           or score < min_score:
            min_element = element
            min_score = score
        if max_score is None \
           or score > max_score:
            max_element = element
            max_score = score

    return min_element, max_element


def unique(sequence):
    """Return unique items in 'sequence'.

    'sequence' -- A sequence of items.

    returns -- A list of unique items in 'sequence', in order of their
    first occurrence in 'sequence'."""

    set = {}
    result = []
    for item in sequence:
        if item not in set:
            result.append(item)
            set[item] = None
    return result


def mapiter(function, iterable):
    """Adapter to map a function onto elements of an iterator.

    A 'mapiter' operates similarly to the 'map' function, except that
    it returns a generator.  The generator applies 'function' to each
    element from the iterator just in time.

    'function' -- A callable that takes one argument.

    'iterable' -- An iterable object.

    returns -- A generator which yields the result of calling 'function'
    on the next element of 'iterable's iterator."""

    next = iter(iterable).next
    while True:
        yield function(next())


def mapapply(function, iterable):
    """Apply 'function' to elements of an iterator.

    'mapapply' is like the built-in function 'map', except that each
    element is used as an argument list to 'function' instead of as its
    single argument."""

    return map(lambda args: apply(function, args), iterable)


def mapdict(function, iterable):
    """Make a dictionary using a function on elements of an iterator.

    'function' -- A callable that takes a single argument and returns a
    '(key, value)' pair.  The values of 'key' must be hashable.

    returns -- A dictionary whose key-value pairs are obtained by
    applying 'function' to elements of 'iterable'.  If a key is produced
    more than once, the last instance is used."""

    result = {}
    for element in iterable:
        key, value = function(element)
        result[key] = value
    return result


def permute(sequence):
    """Return an iterator over all permutations of 'sequence'."""

    length = len(sequence)
    # Handle end cases.
    if length == 0:
        yield ()
        return
    if length == 1:
        yield sequence
        return

    last = (sequence[-1], )
    # Recursively find permutations over a subsequence.
    for permutation in permute(sequence[:-1]):
        # Insert the missing element at all positions.
        for i in xrange(length):
            yield permutation[:i] + last + permutation[i:]


def count(iter, predicate=None):
    """Return the number of elements yielded by 'iter'.

    'predicate' -- Only count items for which the predicate is true.  If
    'None', count all items."""

    result = 0
    for item in iter:
        if predicate is None or predicate(item):
            result += 1
    return result


def zip(*iterables):
    """Like zip, except a generator."""
    
    iterables = map(iter, iterables)
    while True:
        yield [ i.next() for i in iterables ]


def partition(iterator, size):
    """Divide items in 'iterator' into partitions of 'size' items."""

    iterator = iter(iterator)
    group = ()
    try:
        while True:
            for i in xrange(size):
                group += (iterator.next(), )
            yield group
            group = ()
    except StopIteration:
        if group:
            yield group


def parseRange(arg):
    """Parse a range of numbers.

    Parses 'arg', a specification of one or more ranges of nonnegative
    integers.  'arg' is one or more ranges, separated by commas.  Each
    range may be a single nonnegative number; or, it may be a pair of
    nonnegative numbers separated by a hyphen, which is expanded to the
    consecutive integers including the first but excluding the second.

    returns -- The resulting sequence of integers, sorted and with
    duplicates removed."""

    parts = arg.split(",")
    result = []
    for part in parts:
        # Count hyphens in this part.
        num_hyphens = part.count("-")

        if num_hyphens == 0:
            # No hyphens.  Treat it as a single value.
            try:
                result.append(int(part))
            except ValueError:
                raise SyntaxError, part

        elif num_hyphens == 1:
            # One hyphen.  Expand it as a range.
            first, last = part.split("-", 1)
            # Convert limits to integers.
            try:
                first = int(first)
            except ValueError:
                raise SyntaxError, first
            try:
                last = int(last)
            except ValueError:
                raise SyntaxError, last
            # Create the range, ascending or descending as necessary.
            if last >= first:
                part = range(first, last)
            else:
                part = range(first, last, -1)
            # Append values in the range.
            result.extend(part)

        else:
            # Two or more hypens -- a syntax error.
            raise SyntaxError, part

    # Sort and remove duplicates.
    result.sort()
    return unique(result)


def combinationsl(*sequences):
    """Generate all combinations of choices from 'sequences'.

    Each argument is a sequence.  Generates all combinations of tuples
    consisting of one choice from each of 'sequences'.  If '*sequences'
    is empty, generates one empty tuple.

    The first (leftmost) item varies most slowy; the last (rightmost)
    item varies most quickly."""

    if not sequences:
        yield ()
        return
    for item in iter(sequences[0]):
        for rest in combinationsl(*sequences[1 :]):
            yield (item, ) + rest


combinations = combinationsl


def combinationsr(*sequences):
    """Generate all combinations of choices from 'sequences'.

    Each argument is a sequence.  Generates all combinations of tuples
    consisting of one choice from each of 'sequences'.  If '*sequences'
    is empty, generates one empty tuple.

    The first (leftmost) item varies most quickly; the last (rightmost)
    item varies most slowly."""

    if not sequences:
        yield ()
        return
    for item in iter(sequences[-1]):
        for rest in combinationsr(*sequences[: -1]):
            yield rest + (item, )


def scan(function, iterable, initial=_NO_ARG):
    """Like 'reduce', but produces partial results.

    Generates a sequence of results of applying binary 'function'
    successively to items from 'iterable'.  The result of 'function' is
    used as the first argument to the next call.

    'initial' -- If provided the initial value to use as the first
    argument of the first call to 'function'.  If not provided, the
    first item in 'iterable' is used.

    yields -- Successive results of calling 'function' on items in
    'iterable'."""

    items = iter(iterable)
    if initial == _NO_ARG:
        value = items.next()
    else:
        value = initial

    for item in items:
        value = function(value, item)
        yield value


def compose_cmp(*cmps):
    """Compose comparison functions.

    Given multiple comparison functions, returns a composed comparison
    function that applies each of them sequentially, returning the
    result of the first one that returns non-zero.  If all return zero,
    the composed comparison function returns zero.  In effect, the
    comparison functions are successive tie-breakers.  

    '*cmps' -- A sequence of comparison functions, such as the build-in
    'cmp'.  Each takes two arguments and returns zero if the arguments
    compare equal, or -1 or +1 otherwise to indicate their relative
    ordering.

    returns -- The composed comparison function."""

    def composed(x, y):
        for cmp in cmps:
            c = cmp(x, y)
            if c != 0:
                return c
        return 0

    return composed


def chain(iteriter):
    """Chain together interators.

    Returns an iterator whose elements are those generated by elements
    of 'iteriter', each of which must be interable."""

    for iter_item in iteriter:
        for item in iter_item:
            yield item


def select(predicate, iterable):
    """Yield items in 'iterable' for which 'predicate' is true."""

    for item in iterable:
        if predicate(item):
            yield item


