# ======================================================================
#
# Copyright (c) 2017-2018 NVRAM <nvram@users.sourceforge.net>
#
# Released under the MIT License (https://opensource.org/licenses/MIT)
#
# ======================================================================
"""datahammer - a Python data container w/manipulator.

This module provides an easy way to manipulate and inspect lists of
data.  It was designed to handle plain data types, especially the
output from parsing JSON.  It allows simple operations to be done on
the items in parallel in a concise fashion.  Many features will also
work on other data types.
"""
import csv
import json
import operator
import sys

from copy import deepcopy, copy
from types import GeneratorType

version = '0.9.8'
_STR_TYPES = (basestring,) if sys.version_info[0] == 2 else (str,)  # noqa: F821

description = (
    'This module provides an easy way to manipulate and inspect lists of'
    ' data.  It was designed to handle plain data types, especially '
    'the output from parsing JSON.  It allows simple operations to be '
    'done on the items in parallel in a concise fashion.  Many features '
    'will also work on other data types.')

_NO_ARG = object()


def _tname(obj):
    return type(obj).__name__


def _deref(obj, key, dflt):
    try:
        if isinstance(obj, dict):
            return obj[key]
        elif isinstance(obj, (list, tuple)):
            return obj[int(key)]
        return getattr(obj, key)
    except (TypeError, KeyError, IndexError, AttributeError, ValueError):
        pass
    return dflt


class JEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return vars(obj)
        return repr(obj)

    @classmethod
    def dumps(cls, obj, *args, **kwds):
        kwds['sort_keys'] = True
        return json.dumps(obj, *args, cls=cls, **kwds)

    @classmethod
    def jload(cls, arg, extra):
        if not isinstance(extra, dict):
            extra = {}
        if isinstance(arg, _STR_TYPES) or isinstance(arg, bytes):
            return json.loads(arg, **extra)
        if callable(getattr(arg, 'read', None)):
            return json.load(arg, **extra)


class Object(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class DataHammer(object):
    """A container for data items that allows inspecting and testing of each
    item in the contained list of data.
    """
    def __init__(self, data, copy=False, json=False, _nested=False):
        self.__nested = _nested
        if json:
            # JSON can be a dict of parameters to pass to json.loads()
            data = JEncoder.jload(data, json)
        if isinstance(data, DataHammer):
            data = data.__data
        if isinstance(data, GeneratorType):
            data = list(data)
        if isinstance(data, (list, tuple)):
            self.__data = list(deepcopy(data) if copy else data)
        else:
            self.__data = [deepcopy(data) if copy else data]
            self.__nested = True

    #
    # String methods
    #
    def __str__(self):
        # Function: str(OBJ) or print(OBJ) - a JSON dump of the contents.
        return JEncoder.dumps(self.__invert__())

    def __format__(self, fmt):
        """Formatting with the str.format option, "j" format, with optional sign and digits:
          "{:-5j}".format(OBJ)
             ||*-- the 'j' is for JSON.
             |*--- a width specifies an indent.
             *----- Leading '-' indicates newlines between top items."""
        joint = ','
        kwds = dict(sort_keys=True, separators=(',', ':'))
        if fmt.endswith('j'):
            if fmt.startswith('-'):
                joint = ',\n'
                fmt = fmt[1:]
            if fmt != 'j':
                kwds['indent'] = int(fmt[:-1])
        if self.__nested:
            return JEncoder.dumps(None if not self.__data else self.__data[0], **kwds)
        return "[" + joint.join(JEncoder.dumps(e, **kwds) for e in self.__data) + "]"

    #
    # List / item methods
    #
    def __getattr__(self, name):
        assert name != '__data'

        # We handle nested and empty-filtered.
        data = [_deref(e, name, None) for e in self.__data]
        return DataHammer(data if not self.__nested else data[0] if data else data)

    def __getitem__(self, indices):
        if isinstance(indices, DataHammer):
            indices = indices.__data
        if isinstance(indices, (slice, int)):
            return self.__data[indices]

        if isinstance(indices, (list, tuple)):
            # Check the first few items
            types = set(map(type, indices[:20]))
            if types == {int}:
                dlen = len(self.__data)
                data = [self.__data[i] for i in indices if -dlen < i < dlen]
            elif types == {bool}:
                data = [item for item, keep in zip(self.__data, indices) if keep]
            else:
                raise TypeError("Invalid index types: " + ",".join(e.__name__ for e in types))
        else:
            raise TypeError("Invalid index type: " + _tname(indices))
        return DataHammer(data, _nested=self.__nested)

    def _ind(self, index):
        # Function: OBJ._ind(name) - lookup by arbitrary index, key or attribute name
        return self.__getattr__(index)

    def _get(self, name):
        # Function: OBJ._get(name) - lookup by arbitrary index, key or attribute name
        return self.__getattr__(name)

    def __reversed__(self):
        # Operation: reversed(OBJ) - a new OBJ with ITEMs reversed
        if self.__nested or len(self.__data) == 1:
            return self
        return DataHammer(list(reversed(self.__data)), _nested=self.__nested)

    def __len__(self):
        # Operation: len(OBJ) - the length of the contained data
        return len(self.__data)

    def __invert__(self):
        # Operation: ~OBJ - the contained data
        return self.__data if not self.__nested else self.__data[0] if self.__data else None

    def __contains__(self, arg):
        # Operation:  ARG in OBJ  - bool, True if [ARG == ITEM] for any ITEM
        return any(arg == item for item in self.__data)

    def __hash__(self, *args, **kwds):
        # Operation: hash(OBJ) - a hash of the element hashes.  Each ITEM must be hashable.
        return hash(tuple(hash(ele) for ele in self.__data))

    def _contains(self, arg):
        # Function:  - new OBJ from [ARG in ITEM]
        return self._apply(operator.contains, arg)

    def _in(self, arg):
        # Function:  - new OBJ from [ITEM in ARG]
        return self._apply(lambda row: row in arg)

    #
    # Math / numeric methods.
    #
    def __mul__(self, arg):
        # Operation: OBJ * arg - new OBJ from [ITEM * ARG]
        return self._apply(operator.mul, arg)

    def __div__(self, arg):
        # Operation: OBJ / arg - new OBJ from [ITEM / ARG]
        return self._apply(lambda a, b: a / b, arg)

    def __rdiv__(self, arg):
        # Operation: OBJ / arg - new OBJ from [ARG / ITEM]
        return self._apply(lambda a, b: b / a, arg)

    def __floordiv__(self, arg):
        # Operation: OBJ // arg - new OBJ from [ITEM // ARG]
        return self._apply(operator.floordiv, arg)

    def __add__(self, arg):
        # Operation: OBJ + arg - new OBJ from [ITEM + ARG]
        return self._apply(operator.add, arg)

    def __sub__(self, arg):
        # Operation: OBJ - arg - new OBJ from [ITEM - ARG]
        return self._apply(operator.sub, arg)

    def __rsub__(self, arg):
        # Operation: OBJ - arg - new OBJ from [ARG - ITEM]
        return self._apply(lambda a, b: b - a, arg)

    def __mod__(self, arg):
        # Operation: OBJ % arg - new OBJ from [ITEM % ARG]
        return self._apply(operator.mod, arg)

    def __rmod__(self, arg):
        # Operation: arg % OBJ - new OBJ from [ITEM % ARG]
        return self._apply(lambda a, b: b % a, arg)

    def __pow__(self, arg):
        # Operation: OBJ ** arg - new OBJ from [ITEM ** ARG]
        return self._apply(operator.pow, arg)

    def __rfloordiv__(self, arg):
        # Operation: OBJ // arg - new OBJ from [ARG // ITEM]
        return self._apply(lambda a, b: b // a, arg)

    def __rpow__(self, arg):
        # Operation: OBJ ** arg - new OBJ from [ARG ** ITEM]
        return self._apply(lambda a, b: b ** a, arg)

    # Reverse of commutative operators, and Python2/3 synonyms except `matmul`.
    __radd__ = __add__
    __rmul__ = __mul__
    __truediv__ = __div__
    __rtruediv__ = __rdiv__

    #
    # Logical / comparison methods
    #
    def __gt__(self, arg):
        # Comparison: OBJ >= arg - new OBJ from [ITEM >= arg]
        return self._apply(operator.gt, arg)

    def __ge__(self, arg):
        # Comparison: OBJ > arg - new OBJ from [ITEM > arg]
        return self._apply(operator.ge, arg)

    def __eq__(self, arg):
        # Comparison: OBJ == arg - new OBJ from [ITEM == arg]
        if id(self) == id(arg):
            return True
        # To test equality of the total contents, use: arg == ~OBJ
        return self._apply(operator.eq, arg)

    def __ne__(self, arg):
        # Comparison: OBJ != arg - new OBJ from [ITEM != arg]
        return self._apply(operator.ne, arg)

    def __le__(self, arg):
        # Comparison: OBJ <= arg - new OBJ from [ITEM <= arg]
        return self._apply(operator.le, arg)

    def __lt__(self, arg):
        # Comparison: OBJ < arg - new OBJ from [ITEM < arg]
        return self._apply(operator.lt, arg)

    def __bool__(self):
        # Function: bool(x) - test for non-empty contained list.
        return bool(self.__data)

    def __neg__(self):
        # Operation: -OBJ - (unary minus) new OBJ from [not ITEM]
        return self._apply(operator.not_)

    __nonzero__ = __bool__

    #
    # Type conversions are provided with an underscore prefix.
    #
    def _bool(self):
        # Function: bool(OBJ) - new OBJ from [bool(ITEM)]
        return self._apply(bool)

    def _int(self):
        # Function: int(OBJ) - new OBJ from [int(ITEM)]
        return self._apply(int)

    def _float(self):
        # Function: float(OBJ) - new OBJ from [float(ITEM)]
        return self._apply(float)

    #
    # Bitwise logical operators do item-wise operations.
    #
    def __and__(self, arg):
        # Function: OBJ & arg - new OBJ from [OBJ(ITEM)]
        return self._apply(operator.and_, arg)

    def __or__(self, arg):
        # Function: OBJ | ARG - new OBJ from [ITEM or ARG]
        return self._apply(operator.or_, arg)

    def __xor__(self, arg):
        # Function: OBJ ^ ARG - new OBJ from [bool(ITEM) ^ bool(ARG)]
        return self._apply(lambda a, b: bool(a) ^ bool(b), arg)

    def __rand__(self, arg):
        # Function: ARG & OBJ - new OBJ from [ITEM and ARG]
        return self._apply(lambda a, b: b and a, arg)

    def __ror__(self, arg):
        # Function: ARG | OBJ - new OBJ from [ARG | ITEM]
        return self._apply(lambda a, b: b or a, arg)

    #
    # Special methods
    #
    def _apply(self, func, arg=_NO_ARG, *args, **kwds):
        # Function: OBJ._apply(func, *arg, **kwds) - new OBJ from [func(ARG, *ARGS, **KWDS)]
        if isinstance(arg, DataHammer):
            arg = ~arg
        if isinstance(arg, (list, tuple)):
            data = [func(*(row + args), **kwds) for row in zip(self.__data, arg)]
        else:
            args = (tuple() if arg is _NO_ARG else (arg,)) + args
            data = [func(item, *args, **kwds) for item in self.__data]
        result = DataHammer(data[0] if self.__nested and data else data)
        return result

    def _strip(self, arg=bool):
        # Function: OBJ._strip(ARG) - new OBJ from [ITEM] but not for all ITEMS:
        # 1. If ARG is not given:  *bool(ITEM)*
        # 2. If ARG is a callable: *ARG(ITEM)*
        # 3. If ARG is a list, tuple or set: *(ITEM in ARG)*
        # 4. Otherwise: *ITEM == ARG*
        """Return a copy with only the true items. With ARG, used that for
        filtering items, using '=='."""
        if isinstance(arg, DataHammer):
            arg = arg.__data
        if isinstance(arg, (list, tuple, set)):
            def func(item):
                return item not in arg
        elif callable(arg):
            func = arg
        else:
            def func(item):
                return item != arg
        return DataHammer([e for e in self.__data if func(e)], _nested=self.__nested)

    def __listop(self, method, *args, **kwds):
        if self.__nested:
            raise AttributeError("Cannot _insert into a non-list form.")
        data = copy(self.__data)
        method(data, *args, **kwds)
        return data

    def _insert(self, index, item):
        # Function: OBJ._insert(INDEX, ITEM) - new OBJ with ITEM inserted at INDEX.
        """Return a new DataHammer instance with ITEM at the given INDEX.
        This object is not changed."""
        return DataHammer(self.__listop(list.insert, index, item))

    def _extend(self, items):
        # Function: OBJ._extend(INDEX, ITEMS) - new OBJ with ITEMS appended to the list.
        """Return a new DataHammer instance with the given iterable of items appended.
        This object is not changed."""
        return DataHammer(self.__listop(list.extend, items))

    def _splice(self, index, delnum, *item):
        # Function: OBJ._splice(INDEX, DELNUM, *ITEM) - new OBJ but with DELNUM items deleted at
        # INDEX, and ITEM(s) inserted at INDEX.  See Javascript Array.splice()
        data = self.__data[:index] + list(item) + self.__data[index + delnum:]
        return DataHammer(data)

    def _slice(self, start, end=None, step=None):
        # Function: OBJ._slice(START [, END [, STEP]]) - new OBJ with the data list indexed
        # as with *[START:END:STEP]*
        if self.__nested:
            raise AttributeError("Cannot _slice a non-list.")
        return DataHammer(self.__data[start:end:step])

    @staticmethod
    def __freeze_names(obj):
        # Freeze the names for the keys and values
        return ((obj.split('.')[-1], obj), ) if isinstance(obj, _STR_TYPES) else \
            tuple(obj.items()) if isinstance(obj, dict) else \
            tuple((ele.split('.')[-1], ele) for ele in obj)

    def _pick(self, *names, **pairs):
        # Function: OBJ._pick(CHOICES)
        """Return a new DataHammer instance with dictionaries with only the given names.
        This is an easy way to retain/extract data items from the contained data.
        Positional parameters are names, keyword parameters allow renaming.

        For example:
           OBJ._pick('age', 'x.bank', cost='y1.y2.price', dividend='z1.z2.payout')
        Would return a new DataHammer instance where each contained datum has the keys:
             "age", "bank", "cost" and "dividend"
        With values from:   ITEM.age, ITEM.x.y.bank, ITEM.z.price, ITEM.

        Note: this method handles support numerical indexing in choices with raw decimal. Eg:
             age='x.3.age'  # The value for ITEM.x._ind(3).age

        This object is not changed."""
        data = []
        keys = self.__freeze_names(names) + self.__freeze_names(pairs)
        for item in self.__data:
            datum = {}
            for key, name in keys:
                datum[key] = self.__fetch(item, name)
            data.append(datum)
        return DataHammer(data)

    def _tuples(self, *names):
        # Function: OBJ._tuples(CHOICES)
        """Return a tuple of tuples; positional parameters are similar to `_pick()`.
        Named parameters are not allowed in order to guarantee ordering

        For example:
           OBJ._tuples('name.last', 'name.first', nick='name.common',
                      age='age', where='office.location')

        Might return a tuple like:
          (("O'herlihan","Rex","The Singing Cowboy",28,"The Range"),
           ("Frog","Kermit","",75,"The Swamp"),
           ("Scully","Dana","Starbuck",25,"Parts unknown"))

        This object is not changed."""
        data = []
        keys = self.__freeze_names(names)
        for row in self.__data:
            out = tuple(self.__fetch(row, name) for _, name in keys)
            data.append(out)
        return tuple(data)

    _DECIPHER = {"true": True, "false": False, "null": None, "": ""}

    def _toCSV(self, *names, **pairs):
        # Function: OBJ._toCSV(CHOICES)
        """Return a tuple of lines in CSV format; parameters are similar to `_pick()`.
        Positional parameters are names, keyword parameters allow renaming.

        The first line will be the headers: the names and pairs.keys()
        Note: for versions of Python before 3.6, the ordering of values specified in
        `pairs` is not necessarily preserved, but in all cases the order of the header
        and value lines are consistent.

        For example:
           OBJ._toCSV('name.last', 'name.first', nick='name.common',
                      age='age', where='office.location')

        Might return a tuple like:
          ("\"last\",\"first\",\"nick\",\"age\",\"where\"",
           "\"O'herlihan\",\"Rex\",\"The Singing Cowboy\",28,\"The Range\"",
           "\"Frog\",\"Kermit the\",\"\",75,\"The Swamp\"",
           "\"Scully\",\"Dana\",\"Starbuck\",25,\"Parts unknown\"")

        Note: this method handles support numerical indexing in choices with raw decimal. Eg:
             age='x.3.age'  # The value for ITEM.x._ind(3).age

        This object is not changed."""

        parts = self.__freeze_names(names) + self.__freeze_names(pairs)
        keys = tuple(k for k, v in parts)
        indices = tuple(v for k, v in parts)

        # Use an object with a 'write' method that appends to a list:
        result = []
        wrobj = Object(write=lambda row: result.append(row.rstrip()))
        writer = csv.writer(wrobj, delimiter=',', quotechar='"', lineterminator='',
                            quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(keys)
        for row in self.__data:
            out = []
            for key in indices:
                val = self.__fetch(row, key)
                out.append(val)
            writer.writerow(out)
        return tuple(result)

    @classmethod
    def _fromCSV(cls, source, sepr=',', handler=None):
        # Function: DataHammer._fromCSV(source, sepr=',')
        """Return a DataHammer instance after parsing the lines of SOURCE as CSV format.

        For example:
          >>> osource = '''first,last,age
          ... O'herlihan,Rex,28
          ... Frog,Kermit the,75
          ... Scully,Dana,25\n'''
          >>> obj = DataHammer._fromCSV(source)
          >>> csv = obj._toCSV('age', 'first', 'last')
          >>> print("\n".join(csv))
          "age","first","last"
          28,"Rex","O'herlihan"
          75,"Kermit the","Frog"
          25,"Dana","Scully"

        NOTE: The first row must be the member names.
        """
        if callable(getattr(source, 'read', None)):
            source = source.read()

        # Remove the trailing newline here, or split gives us a ghost line at the end.
        if source.endswith('\n'):
            source = source[:-1]
        lines = source.replace('\r', '').split('\n')

        def decipher(text):
            if text in cls._DECIPHER:
                return cls._DECIPHER[text]
            for func in (int, float):
                try:
                    return func(text)
                except ValueError:
                    pass
            return text

        # For each remaining line, handle the shorter of keys and data.
        reader = csv.reader(lines, delimiter=sepr)
        keys = next(reader)
        data = []
        for row in reader:
            item = {}
            for key, value in zip(keys, row):
                item[key] = decipher(value)
            if handler:
                item = handler(item)
            data.append(item)
        return DataHammer(data)

    def _groupby(self, group, values, combine=None):
        # Function: OBJ._groupby(GROUP, VALUES, COMBINE=None)
        """Return a new DataHammer instance after aggregating the named value(s) with similar key(s).
        The items in the returned object will have keys from 'group' and from 'values'.
        The values will be a list unless 'combine' is specified.

        This object is not changed.

        Both 'group' and 'values' can be either of:
        1. A tuple of strings, which are used to dereference each item.  Resulting key is the
           last element after a '.' in the string.
        2. A dict, the keys are the resulting keys and the values are used to dereference into
           the items.

        For example, to reduce a sample by state and gender, and get the average age and number
        of people in the sample, you could use:

           result = OBJ._aggregat(('state', 'gender'), ('age', ),
                                  combine=lambda ages: (statistics.mean(ages), len(ages)))

        NOTES:

        1. The current implementation requires that every 'key' value must be hashable.

        2. The order of the resulting ITEMS is the same order as the first occurence of each unique
           set of 'key' values.  And the order of values in the lists for each 'key' name is the same
           as the order in which those values occurred for the associate 'key' values.

        3. The 'combine' method must return a list or tuple, one entry per argument. For example, to
           combine values with 'sum' you could use:

              lambda values: [sum(values)]
        """
        key_names = self.__freeze_names(group)
        value_names = self.__freeze_names(values)
        key_group = tuple(k for k, _ in key_names)
        value_group = tuple(k for k, _ in value_names)

        # In order to group by the associated 'key' values, we need lookup key, so we use a hash
        # of the ordered values.  We store the key names in the 'names' map, and the values in
        # the 'values' map.
        names = {}
        values = {}
        ordered = []

        for row in self.__data:
            # Get the values associated with the key_names, in order:
            klist = []
            for kname, oname in key_names:
                klist.append(self.__fetch(row, oname))
            # This fails on unhashable 'key' values:
            index = hash(tuple(klist))
            # Save the name values, and add an empty list for every 'value' name:
            if index not in names:
                names[index] = klist
                values[index] = dict([(k, []) for k in value_group])
                ordered.append(index)
            # Now, append each item to the appropriate
            vdict = values[index]
            for vname, oname in value_names:
                vdict[vname].append(self.__fetch(row, oname))

        # Now, we have the dictionaries and must "unravel" them into a list.
        data = []
        for index in ordered:
            row = dict(zip([k for k in key_group], names[index]))
            vind = values[index]
            if combine:
                vals = [vind[k] for k in value_group]
                vind = zip(value_group, combine(*vals))
            row.update(vind)
            data.append(row)

        return DataHammer(data)

    def _unique(self, keys, unique=1):
        # Function: OBJ._unique(KEYS, UNIQUE=True)
        """Return a new DataHammer instance after removing all items with duplicate (or unique)
        values for the given 'keys'.

        - `keys` is a tuple of strings, which are used to dereference items. May be `None` if
          the values are scalars.
        - `unique` controls handling of items with duplicate key values, the values mean:
          0 = only those items are unique with their key values are kept, duplicates are dropped.
          1 = Default: the first item with the given key values is kept, subsequent items with
              the same key values will be dropped.
          2 = All items that have duplicate key values are kept, unique ones are dropped.

           In all cases the orginal order is preserved.

        NOTES:
        * The current implementation requires that every 'key' value value must be hashable
          (or the full item if 'keys' is `None`).
        """
        if isinstance(keys, _STR_TYPES):
            keys = (keys, )
        if keys is not None and (
                not isinstance(keys, (tuple, list)) or
                not all(isinstance(k, _STR_TYPES) for k in keys)):
            raise ValueError("'keys' must be a tuple of strings or `None`.")
        if unique not in (0, 1, 2):
            raise ValueError("'unique' must be 0, 1 or 2.")

        # Find all keys and their location(s) in the items.
        dups = set()
        values = []
        valset = set()
        for nth, row in enumerate(self.__data):
            vals = hash(row) if keys is None else tuple(self.__fetch(row, key) for key in keys)
            if vals not in valset:
                valset.add(vals)
            else:
                dups.add(vals)
            values.append(vals)
        # Iterate in order and keep the ones we want.
        data = []
        first = set()
        for nth, vals in enumerate(values):
            keep = False
            if unique == 0 and vals not in dups:
                keep = True
            elif unique == 1 and vals not in first:
                first.add(vals)
                keep = True
            elif unique == 2 and vals in dups:
                keep = True
            if keep:
                data.append(self.__data[nth])

        return DataHammer(data)

    def _flatten(self):
        # Function: OBJ._flatten()
        """Return a DataHammer instance with contained items that are the result of flattening
        this instance's contained items by one level. Sub-items are added in iteration-order
        for items that are a set, list or tuple and for the values from a dict.
        Other types are not flattened, and are added as-is.

        This object is not changed."""
        data = []
        for item in self.__data:
            if isinstance(item, dict):
                data.extend(item.values())
            elif isinstance(item, (list, tuple, set)):
                data.extend(item)
            else:
                data.append(item)
        return DataHammer(data)

    # ==================================================================================================================
    """
    Join Operations.

    NOTE: This is not all that complicated, but it is pretty hard to explain without diagrams.

    Most of the complexity comes from (a) unmatched items and (b) multiple items that have the same key values. This
    method allows choices for this.  Users that are familiar with SQL Joins will understand this issue.

    HANDLING OF ITEMS WITH DUPLICATE KEY-VALUES

       1. The JOIN_PRODUCT operations are similar to SQL joins.  The name comes from "Cartesian Product" - such that
          the output contains every item from the left paired with every matching item from the right.  See Examples.

       2. The JOIN_ORDERED simply pairs matching items from the left and the right, in the order they were found in the
          input instances.

    HANDING OF ITEMS WITH NO MATCHING ITEMS

     Here, the INNER and OUTER join terminology is a remnant from SQL, the 'JOIN_KEEP_' flags are equivalent and
     provided since they more explicit for users w/o an SQL background.  These can be summarized thus:

       1. JOIN_KEEP_NEITHER, INNER_JOIN     = discard unmatched items from left and from the right.

       2. JOIN_KEEP_LEFT, LEFT_OUTER_JOIN   = discard unmatched items from the right.

       3. JOIN_KEEP_RIGHT, RIGHT_OUTER_JOIN = discard unmatched items from the left.

       4. JOIN_KEEP_BOTH, FULL_OUTER_JOIN   = keep all unmatched items.

    PLEASE: See the README for how to file an issue if this explanation isn't clear. I also hate it when project
    documentation is insufficient, so I will do my best to clarify. """

    # JOIN Constants

    # These allow choosing between joining with the SQL-like (cartesian product) or in-order (1-by-1) methods
    # for when there are multiple matching items.
    JOIN_PRODUCT = 0x10
    JOIN_ORDERED = 0x20

    # These indicate how to handle unmatched items, and are used in conjunction with the above.
    JOIN_KEEP_NEITHER = INNER_JOIN = 0
    JOIN_KEEP_RIGHT = RIGHT_OUTER_JOIN = 1
    JOIN_KEEP_LEFT = LEFT_OUTER_JOIN = 2
    JOIN_KEEP_BOTH = FULL_OUTER_JOIN = 3

    __JOIN_KEEP_MASK = 0x07
    __JOIN_MODE_MASK = 0x30

    @classmethod
    def __decompose(self, data, keys):
        # Used internally for join methods. Returns a Object instance with the attributes:
        #  .ITEMS - dict[keyhash] = in-order list of items with those key-values
        #  .KEYORD - list of key hashes, in order first encountered
        #  .KEYIND - list of key hashes, in order of every times encountered

        # VALUES is a map of the keyhash
        items = {}
        keyord = []
        keyind = []
        for item in data:
            kval = tuple(self.__fetch(item, key) for key in keys)
            keyhash = hash(kval)
            if keyhash not in items:
                items[keyhash] = [item]
                keyord.append(keyhash)
            else:
                items[keyhash].append(item)
            keyind.append(keyhash)
        return Object(items=items, keyord=keyord, keyind=keyind)

    @staticmethod
    def __join_default_merge(left, right):
        out = deepcopy(left)
        out.update(deepcopy(right))
        return out

    def _join(self, keys, other, flags=None, merge=None):
        # Function: OBJ._join(KEYS, OTHER, FLAGS, MERGE)
        """Return a new DataHammer instance created by joining the items from this instance and another instance,
        joining where the values from KEYS (a list/tuple of key names).

        NOTES:
        1. This object is not changed.

        2. The current implementation requires that all 'key' values must be hashable.

        3. The top-level items of both instances must be a dict, objects with attributes ARE NOT supported.

        4. The 'flags' parameter should be the sum of two constants. This will dictate how unmatched and duplicate
           key-value items are handled.  Defaults are indicated with '*':
           a. JOIN_PRODUCT* or JOIN_ORDERED.
           b. JOIN_KEEP_NEITHER*, JOIN_KEEP_LEFT, JOIN_KEEP_RIGHT or JOIN_KEEP_BOTH

        5. If given, the 'merge' parameter should be a callable taking the parameters (LEFT, RIGHT) and returning
           the desired item. The default is equivalent to the following, which overwrites any members in the left
           that are also in the right.

              def _merge(left, right, _ignored):
                 out = copy.deepcopy(left)
                 out.update(copy.deepcopy(right))
                 return out

        WARNING: If JOIN_PRODUCT is used with large inputs and many duplicates, this can be very slow and consume a
        great deal of memory."""

        if flags is None:
            flags = (self.JOIN_PRODUCT + self.JOIN_KEEP_NEITHER)

        if isinstance(keys, _STR_TYPES):
            keys = (keys, )
        elif not isinstance(keys, (list, tuple)) or not all(isinstance(key, _STR_TYPES) for key in keys):
            raise TypeError("KEYS must be a list/tuple of strings")
        if not isinstance(other, (list, tuple, DataHammer)):
            raise TypeError("OTHER must be a DataHammer or list/tuple")
        if merge and not callable(merge):
            raise TypeError("MERGE must be a callable")
        if merge is None:
            merge = DataHammer.__join_default_merge

        left = self.__decompose(self.__data, keys)
        right = self.__decompose(other, keys)

        keep = flags & self.__JOIN_KEEP_MASK
        mode = flags & self.__JOIN_MODE_MASK

        # These bits are orthogonal.
        lkeep = bool(keep & self.__JOIN_KEEP_MASK & self.JOIN_KEEP_LEFT)
        rkeep = bool(keep & self.__JOIN_KEEP_MASK & self.JOIN_KEEP_RIGHT)
        combo = (mode & self.__JOIN_MODE_MASK) == self.JOIN_PRODUCT
        result = []
        rkeys = set(right.items)

        for keyhash in left.keyind:
            litem = left.items[keyhash].pop(0)

            if combo:  # JOIN_PRODUCT
                # Unmatched left items are kept as-is or not at all.
                rlist = right.items.get(keyhash, None)
                rkeys.discard(keyhash)

                # Output a row for every right matching item.
                if rlist:
                    for ritem in rlist:
                        result.append(merge(litem, ritem))

                elif lkeep:
                    result.append(deepcopy(litem))

            else:  # JOIN_ORDERED
                # Output a row a row with the first pair.
                if keyhash in right.items:
                    row = right.items[keyhash]
                    if row:
                        ritem = row.pop(0)
                        if not row:
                            # Remove the empty list so "not in" above will work.
                            del right.items[keyhash]
                        result.append(merge(litem, ritem))
                elif lkeep:
                    # Unmatched left items are kept as-is or not at all.
                    result.append(deepcopy(litem))

        # Add remaining unmatched items from right, if desired, in the order found.
        if rkeep:
            for keyhash in right.keyind:
                if keyhash in rkeys:
                    row = right.items.get(keyhash, [])
                    for ritem in row:
                        result.append(row.pop(0))

        return DataHammer(result)

    @classmethod
    def __fetch(cls, item, keys):
        if isinstance(keys, _STR_TYPES):
            keys = keys.split('.')
        for key in keys:
            if item is None:
                break
            item = _deref(item, key, None)
        return item

    class Mutator(object):
        def __init__(self, mdata, _keys=None):
            self.__mdata = mdata
            self.__keys = _keys or []

        def __clone(self, ndx, key):
            return self.__class__(self.__mdata, self.__keys + [(ndx, key)])

        def __str__(self):
            return "[Mutator(%s)]" % self.__keys

        __repr__ = __str__

        def __getattr__(self, name):
            if name == '_':
                return self
            return self.__clone(0, name)

        def __getitem__(self, index):
            return self.__clone(1, index)

        def _ind(self, index):
            return self.__clone(1, index)

        def _attr(self, name):
            return self.__clone(0, name)

        def _setall(self, val):
            # Only for setting/overwriting does the item not have to exist.
            return self.__handle(lambda *_: val, overwrite=True)

        def _set(self, val):
            if isinstance(val, type(DataHammer)) or not hasattr(val, '__getitem__'):
                return self._setall(val)
            source = iter(val)
            return self.__handle(lambda *_: next(source), overwrite=True)

        def _apply(self, func, *args, **kwds):
            return self.__handle(func, True, *args, **kwds)

        def __invert__(self):
            return ~self.__mdata

        def __iadd__(self, value):
            return self.__handle(operator.add, False, value)

        def __isub__(self, value):
            return self.__handle(operator.sub, False, value)

        def __imul__(self, value):
            return self.__handle(operator.mul, False, value)

        def __idiv__(self, value):
            return self.__handle(lambda a, b: a / b, False, value)

        __itruediv__ = __idiv__

        def __imod__(self, value):
            return self.__handle(operator.mod, False, value)

        def __ipow__(self, value):
            return self.__handle(operator.pow, False, value)

        def __ifloordiv__(self, value):
            return self.__handle(operator.floordiv, False, value)

        def __handle(self, modop, overwrite, *args, **kwds):
            assert self.__keys, "Modification of root items is not supported."
            target = ~self.__mdata

            for nth, item in enumerate(target):
                try:
                    # Follow the keys, but save the next-to-last for the LVAL.
                    for ndx, key in self.__keys[:-1]:
                        item = _deref(item, key, {})

                    # The final item must be altered in-place:
                    ndx, key = self.__keys[-1]
                    value = _deref(item, key, _NO_ARG)
                    if overwrite or value is not _NO_ARG:

                        if ndx or (hasattr(item, 'get') and (key in item or overwrite)):
                            value = modop(value, *args, **kwds)
                            item[key] = value

                        elif isinstance(key, _STR_TYPES) and hasattr(item, '__dict__' if overwrite else key):
                            value = modop(value, *args, **kwds)
                            setattr(item, key, value)

                except StopIteration:
                    # Handle a limited-length list/tuple/DataHammer
                    break

            return self

    def _mutate(self):
        return self.Mutator(self)

# The End.
