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
import json
import operator
import sys

from copy import deepcopy, copy
from types import GeneratorType

version = '0.9.5'
_STR_TYPES = (basestring,) if sys.version_info[0] == 2 else (str,)

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

    def _long(self):
        # Function: long(OBJ) - new OBJ from [long(ITEM)]
        return self._apply(long)

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

        data = [",".join('"%s"' % e.split('.')[-1] for e in (list(names) + list(pairs.keys())))]
        keys = list(names) + list(pairs.values())
        for row in self.__data:
            out = []
            for col, key in enumerate(keys):
                datum = self.__fetch(row, key)
                if isinstance(datum, (int, float, bool)):
                    text = json.dumps(datum)
                elif datum in (None, ""):
                    text = ""
                else:
                    text = json.dumps(str(datum))
                out.append(text)
            data.append(",".join(out))
        return tuple(data)

    def _groupby(self, group, values, combine=None):
        # Function: OBJ._groupby(GROUP, VALUES, COMBINE=None)
        """Return a new DataHammer instance after aggregating the named VALUE(s) with similar KEY(s).
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
