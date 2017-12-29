datahammer
##########

"When all you have is a hammer, everything looks like a nail." - *Anonymous*

**Index:**

* `Summary`_
* `Details`_ (`Known Issues`_, `Construction`_, `Operations`_, `Functions`_, `Indexing`_, `Notes`_)
* `Installation`_ (`Releases`_)
* `Examples`_

Summary
------------------

This module provides an easy way to filter, inspect, analayze and manipulate many similar data items.
It was designed to handle plain data types, especially the output from parsing JSON.  It is designed to
allows operations to be done a concise fashion, and on all items in a simple parallel manner.

It mostly works on other data types, for either data as attributes, properties or with *[]*.

By design, concise usages was favored over speed of performance.  It was inspired by a need for a
concise data manipulation syntax and by the projects `jQuery <https://jquery.com/>`_ and `jq
<https://stedolan.github.io/sjq/>`_.


Details
-------

- Most operations on a *DataHammer* instance return a value or a new instance, they do not mutate the
  contained data.  Note that a returned ITEM could be mutated by the calling code.

- The contained data can be retrieved with the invert operator (**~**).  It will be a **list**
  unless constructed with a single ITEM, in which case that ITEM will be returned.

- In order to allow accessing arbitrary ITEM attributes uses the dot notation, **public functions start
  with a single underscore**, in contrast to typical Python conventions.  See `Functions`_.

- It uses a **list** as its top-level container, and will convert a **tuple** or most generators into a
  **list**.

- When constructed with a single ITEM, that item will be wrapped in a **list** and *most* operations will
  be identitical to having been constructed with a list with that single ITEM.

- It uses '.' access of  *dict* members and for attributes, the response is typically **None** if there
  is no such key or attribute (no *KeyError* or *AttributeError* is raised).

- Math and comparison operators work on the contained items, and return a new container with the
  results.

- There is a **Mutator** class returned by the **_mutator()** function that allow modifying the data
  in-place for some, but not all, of the
  `Augmented Assignment statements <https://docs.python.org/3/reference/simple_stmts.html#grammar-token-augmented_assignment_stmt>`_.


Known Issues
^^^^^^^^^^^^

- Using "*ITEM in OBJ*" works as you probably expect, but avoid using "*OBJ in OTHER*" for iterable
  containers (`Note 6`_).

- By design and intent, the bitwise operators (`&`, `|`, `^`) actually create a new instance by applying
  the `and`, `or` and `xor` operators, respectively.  This is because theose operators cannot be
  overridden to return an object as we wish.

- There are missing operators that could be added. Among these are **del** (attribute or key),
  and the bitwise math operators.


Construction
^^^^^^^^^^^^

Creating a *DataHammer* can take several types of input.  However, in all cases the operations are as if
it contains a **list** of items, presumably with a similar schema.

+--------------------+----------------------------------------------------------------+
|  **Parameters**    |     **Description**                                            |
+--------------------+----------------------------------------------------------------+
| ``data``           | This must be one of:                                           |
|                    |                                                                |
|                    | * A `list` of ITEMS.                                           |
|                    | * A single ITEM, a special case of the `list` of ITEMS.        |
|                    |                                                                |
|                    | If the **json** value true, then `data` can be either of:      |
|                    |                                                                |
|                    | * A `file` object, from which *all* data is read, and the      |
|                    |   results are treated as TEXT, or...                           |
|                    | * TEXT to be parsed as JSON.                                   |
+--------------------+----------------------------------------------------------------+
| ``copy``           | If true, then a `deepcopy` will be made of `data`.             |
+--------------------+----------------------------------------------------------------+
| ``json``           | If provided, it should either be `True` or a dict of arguments |
|                    | to be passed to *JSON.loads()* for when `data` is of either    |
|                    | the `file` or `TEXT` forms.                                    |
+--------------------+----------------------------------------------------------------+


Operations
^^^^^^^^^^

This is a list of supported operations, including applying builtin Python functions. (`Note 1`_)

+---------------------------------------+---------------------------------------------------------------+
|             **Operation**             |     **Description**                                           |
+---------------------------------------+---------------------------------------------------------------+
| ``~OBJ``                              | Returns the contained data.                                   |
+---------------------------------------+---------------------------------------------------------------+
| ``OBJ.index``                         | Creates a list by applying the *index* (an *int* for *list*   |
|                                       | items a key for *dict* items, or the name of an *attribute*   |
| ``OBJ._ind(index)``                   | or *property*), then creates an instance from that list.      |
|                                       |                                                               |
| ``OBJ._get(index)``                   | (`Note 2`_)                                                   |
+---------------------------------------+---------------------------------------------------------------+
| ``OBJ`` *op* ``OTHER``                | Return a *DataHammer* instance with a bool result from the    |
|                                       | comparison of each ITEM with OTHER.  (`Note 3`_)              |
| *op* can be:   ``< <= == != >= >``    |                                                               |
|                                       | To test equality of contents, use: *~OBJ == OTHER*            |
+---------------------------------------+---------------------------------------------------------------+
| ``OBJ`` *bitop* ``OTHER``             | Return a *DataHammer* instance with the results of applying   |
|                                       | `and`, `or` and a "bool-xor" to each *ITEM* and *OTHER*, or   |
| ``OTHER`` *bitop* ``OBJ``             | (*OTHER* and *ITEM*).  These are needed since those keywords  |
|                                       | cannot be overridden in the desired fashion.                  |
| *bitop* can be:  ``& ^ |``            | (`Note 4`_)                                                   |
+---------------------------------------+---------------------------------------------------------------+
| ``OBJ`` *mathop* ``OTHER``            | Return a *DataHammer* instance with the results of applying   |
|                                       | a math operators as: *OTHER mathop ITEM*.  (`Note 3`_)        |
| *mathop* can be:  ``+ - * / // ** %`` |                                                               |
+---------------------------------------+---------------------------------------------------------------+
| ``OTHER`` *mathop* ``OBJ``            | Return a *DataHammer* instance with the results of applying   |
|                                       | a math operators as: *OTHER mathop ITEM*.  (`Note 3`_)        |
| ``*mathop* can be:  + - * / // ** %`` |                                                               |
+---------------------------------------+---------------------------------------------------------------+
| ``OBJ[indexes]``                      | Depending on the argument, returns a *DataHammer* instance, a |
|                                       | single contained ITEM, or a list of ITEMs.                    |
|                                       | See `Indexing`_ and `Note 4`_, for more information.          |
+---------------------------------------+---------------------------------------------------------------+
| ``OBJ._bool()``                       | Return a *DataHammer* instance with the results of applying   |
| ``OBJ._int()``                        | the builtin type (*of the same name w/o the underscore*) to   |
| ``OBJ._float()``                      | each item in the list.                                        |
| ``OBJ._long()``                       | *(Use of 'long' is only allowed for Python 2)*                |
+---------------------------------------+---------------------------------------------------------------+
| ``reversed(OBJ)``                     | Return a *DataHammer* instance with the contained data in     |
|                                       | reversed order.                                               |
+---------------------------------------+---------------------------------------------------------------+
| ``len(OBJ)``                          | Return an *int* for the number of contained data ITEMs.       |
+---------------------------------------+---------------------------------------------------------------+
| ``hash(OBJ)``                         | Return an *int* that is the hash of the tuple of the hash of  |
|                                       | every ITEM.                                                   |
|                                       | This will raise an exception if *any* ITEM cannot be hashed.  |
+---------------------------------------+---------------------------------------------------------------+
| ``ARG in OBJ``                        | Return a bool, which is `True` if any *ITEM == OBJ*.          |
|                                       | (`Note 3`_ applies with regard to limiting the items tested.) |
+---------------------------------------+---------------------------------------------------------------+
| ``OBJ in ARG``                        | *This is almost never what you want!*  Return a single bool,  |
|                                       | ignoring of contents of ARG or OBJ.  The result is `True` if  |
|                                       | neither ARG nor OBJ are empty, and `False` if they both are.  |
+---------------------------------------+---------------------------------------------------------------+
| ``-OBJ``    *(unary minus)*           | Return a *DataHammer* instance with the results of applying   |
|                                       | *not ITEM* for each item.                                     |
+---------------------------------------+---------------------------------------------------------------+


Functions
^^^^^^^^^

This is a list of supported functions (`Note 1`_).

+------------------------------------------+---------------------------------------------------------------+
|            **Function**                  |     **Description**                                           |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._ind(name)``                       | (`Note 2`_)                                                   |
|                                          |                                                               |
| ``OBJ._get(name)``                       |                                                               |
+------------------------------------------+---------------------------------------------------------------+
| ``str(OBJ)``                             | Returns a JSON dump of the contained data.                    |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._contains(ARG)``                   | Return a *DataHammer* instance with the results of applying   |
|                                          | *ARG in ITEM* for each item.                                  |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._apply(FUNC, ARG, *ARGS, **KWDS)`` | Return a *DataHammer* instance with the results of applying   |
|                                          | ``FUNC(ITEM, ARG, *ARGS, **KWDS)`` to each item.  (`Note 3`_) |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._strip(ARG)``                      | Return a *DataHammer* instance with only the desired items.   |
|                                          | Based on the type of ARG given, the new instance has only the |
|                                          | items for which the result is true of:                        |
|                                          | 1. If ARG is not given:  *bool(ITEM)*                         |
|                                          | 2. If ARG is a callable: *ARG(ITEM)*                          |
|                                          | 3. If ARG is a list, tuple or set: *(ITEM in ARG)*            |
|                                          | 4. Otherwise: *ITEM == ARG*                                   |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._insert(INDEX, ITEM)``             | Return a *DataHammer* instance with ITEM inserted at INDEX.   |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._extend(INDEX, ITEMS)``            | Return a *DataHammer* instance with ITEMS added at the end.   |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._splice(INDEX, DELNUM, *ITEM)``    | Return a *DataHammer* instance with DELNUM items deleted at   |
|                                          | INDEX, and with ITEM(s) inserted there. (`Note 5`_)           |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._slice(START [, END [, STEP ] ])`` | Return a *DataHammer* instance with the list sliced according |
|                                          | to the given indices (like *list* slicing works).             |
+------------------------------------------+---------------------------------------------------------------+


Indexing
^^^^^^^^

Indexing a *DataHammer* instance with *[]* allows simple access to items from the contained data, but
there are various types of parameters types allowed.  See `Note 4`_.

1. Indexing with an **int** or a **slice** object works identical to a **list**, and is literally
   identical to **(~OBJ)[...]**.

   * A single item is returned with an **int** argument, and can raise an IndexError.
   * A (possibly empty) list of items is returned with either:

     * An explicit **slice** argument, eg:   OBJ[slice(1, None, 5)]
     * An implicit **slice** argument, eg:   OBJ[1::5]
   
2. Indexing with a **list**, **tuple** or a *DataHammer* instance, will return another *DataHammer*
   instance.  (See `Note 3`_.)  The parameter must either be all **bool** or all **int**, and they
   dictate *which* items are used to construct the new instance:

   * For **bool** indexes, each bool in the argument indicates if the corresponding item in the
     *DataHammer* is included in the new instance.

   * For **int** indexes, each int is used to index into the contained data, and which item is include
     in the new instance.  This allows both filtering and reordering of data.

Indexing Examples:

     .. code:: python

        >>> OBJ = DataHammer(list(range(10, 15)))

        # Note that the following dereference the instance with "~" to show the contents:

        >>> ~OBJ
        [10, 11, 12, 13, 14]
        >>> ~OBJ[(True, False, True, True, False, True)]
        [10, 12, 13]      # The last/6th `True` is ignored since len(OBJ)==5
        >>> ~OBJ[(4, 2, 1, 40, -1, 3, 1)]
        [14, 12, 11, 14, 13, 11]    # 40 is ignored.

        # Note these DO NOT dereference the result, they are not a DataHammer instance.

        >>> type(OBJ[1])
        <type 'int'>
        >>> type(OBJ[:5])
        <type 'list'>
        >>> type(OBJ[slice(3)])
        <type 'list'>
        >>> OBJ[::3]
        [10, 13]


Notes
^^^^^

Note 1
""""""

In these examples, *OBJ* refers to a *DataHammer* instance, *LIST* refers to the list of
contained items, and *ITEM* refers to an item in the contained list or directly in the
*OBJ*.


Note 2
""""""

An attribute dereference (eg: *OBJ.index*) and the methods *OBJ._ind(index)* and *OBJ._get(index)* all
function identically, returning a new **DataHammer** instance.  The latter are provided for use when
*index* is an *int* or otherwise not a valid string identifier.


Note 3
""""""

For most operations and functions that return a new instance, when a *DataHammer* instance is combined
with a list, tuple or other *DataHammer* instance, the length of the new instance will be limited by the
length of the shorter of the two operands.  For example:

  - Using a shorter operand, the result will be shortened as if the *DataHammer* instance had only that
    many items.

  - Using a longer operand, the result will be as if the *DataHammer* instance had only as many items as
    that other operand.

  .. code:: python

     >>> dh1 = DataHammer(range(8))
     >>> ~(dh1 + (10, 20))
     [10, 21]
     >>> dh2 = DataHammer((3, 1, 4))
     >>> ~(dh1 == dh2)
     [False, True, False]
     >>> ~(dh1[dh2])
     [3, 1, 4]


Note 4
""""""

Because the **[]** syntax is used for `Indexing`_ and returns an ITEM or list, we cannot use this syntax
for chaining or to create another instance as we do for dotted-attribute access.  This is why there is a
**_ind()** method, to allow

  .. code:: python

     >>> dh = DataHammer([[i, i*i] for i in range(10, 15)])
     >>> ~dh
     [[10, 100], [11, 121], [12, 144], [13, 169], [14, 196]]
     >>> ~dh._ind(1)
     [100, 121, 144, 169, 196]
     >>> ~(dh._ind(1) > 125)
     [False, False, True, True, True]
     >>> ~dh[dh._ind(1) > 125]
     [[12, 144], [13, 169], [14, 196]]
     >>> dh = DataHammer([dict(a=i, b=tuple(range(i, i*2))) for i in range(6)])

     # 'dh.b' returns a DataHammer of N-tuples, then '[3]' retrieves the 4th of these tuples as a `tuple`.
     >>> dh.b[2]
     (2, 3)

     # Here 'dh.b' gives a DataHammer instance of N-tuples, but '_ind(2)' returns another DataHammer
     # with the 3rd item from those N-tuples.  Note the `None` for slots where the tuple length.
     >>> dh.b._ind(2)
     <datahammer.DataHammer object at 0x7f79eb1a9c10>
     >>> ~dh.b._ind(2)
     [None, None, None, 5, 6, 7]


Note 5
""""""

This works similar to the *slice* method of the
`Javascript Array <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/slice>`_
class.


Note 6
""""""

Using "*ITEM in OBJ*" returns True if ITEM matches one of the items in OBJ, using the operator **==**
for the test.  However, using *OBJ in OTHER* for an iterable containers *OTHER*, is useless.
useless.

Using "*OBJ in OTHER*" will evaluate the expression "**X == OBJ**" for each item X in OTHER,, resulting
in a list of bool.  Unless either *OTHER* or *OBJ* are empty, this means a non-empty list will be
converted to **True** even if all of the comparisons fail.


Installation
------------
Install the package using **pip**, eg:

  `sudo pip install datahammer`

Or for a specific version:

  `sudo python3 -m pip install datahammer`



Releases
^^^^^^^^

   +-------------+--------------------------------------------------------+
   | **Version** | **Description**                                        |
   +-------------+--------------------------------------------------------+
   |      1.0    | Initial release                                        |
   +-------------+--------------------------------------------------------+

Examples
--------


Given a JSON file that has metadata separated from the data values, we can easily
combine these, and find the ones which match criteria we want.

  .. code:: python

      >>> from datahammer import DataHammer
      >>> from six.moves.urllib import request
      >>> from collections import Counter

      >>> URL = 'https://data.ny.gov/api/views/pxa9-czw8/rows.json?accessType=DOWNLOAD'
      >>> req = request.urlopen(URL)
      >>> jobs = DataHammer(req, json=dict(encoding='utf-8'))

      # Grab the contained data in order to find its keys.
      >>> (~jobs).keys()
      dict_keys(['meta', 'data'])
      >>> names = jobs.meta.view.columns.name
      >>> norm = DataHammer(dict(zip(names, row)) for row in jobs.data)

      # Here 'norm' contains 840 items, each a dict with the same schema.
      >>> len(norm)
      840
      >>> print(norm[0])
      {'sid': 1, 'id': 'A0447302-02D8-4EFD-AB68-777680645F02', 'position': 1,
       'created_at': 1437380960, 'created_meta': '707861', 'updated_at': 1437380960,
       'updated_meta': '707861', 'meta': None, 'Year': '2012', 'Region': 'Capital Region',
       'NAICS Code': '11', 'Industry': 'Agriculture, Forestry, Fishing and Hunting',
       'Jobs': '2183'}

      # Use collections.Counter to count the number of instances of values:
      >>> Counter(norm.Year)
      Counter({'2012': 210, '2013': 210, '2014': 210, '2015': 210})
      >>> Counter(norm._get('NAICS Code'))
      Counter({'11': 40, '21': 40, '22': 40, '23': 40, '42': 40, '51': 40, '52': 40,
               '53': 40, '54': 40, '55': 40, '56': 40, '61': 40, '62': 40, '71': 40,
               '72': 40, '81': 40, '90': 40, '99': 40, '31-33': 30, '44-45': 30,
               '48-49': 30, '31': 10, '44': 10, '48': 10})

      # Use '&' to require both conditions.
      >>> fish3 = norm[(norm.Year == '2013') & norm.Region._contains('Capital Region')]
      >>> len(fish3)
      21
      >>> keepers = norm.Jobs._int() > 500000
      >>> sum(keepers)
      8
      >>> large = norm[keepers]
      >>> len(large)
      8
