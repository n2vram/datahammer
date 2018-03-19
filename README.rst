datahammer
##########

`Version 0.9.4`

"When all you have is a hammer, everything looks like a nail." - *Anonymous*

----------

`Note that although the version is not yet at 1.0, the code is stable and full
test coverage.  The concern is primarily with the clarity and sufficiency of this
documentation.`

.. contents:: **Index**
   :depth: 2
   :local:

.. style table { border: 2px solid red; font-family: fujimoto; }

Summary
------------------

This module provides an easy way to filter, inspect, analyze and manipulate many similar data items.  It was
designed to handle plain data types, especially the output from parsing JSON.  It is designed to allow
operations to be done a concise fashion, and on all items in a simple parallel manner.

It mostly works on other data types, for either data as attributes, properties or with *[]*.

By design, concise usages was favored over speed of performance.  It was inspired by a need for a
concise data manipulation syntax and by the projects `jQuery <https://jquery.com/>`_ and
`jq <https://stedolan.github.io/sjq/>`_.


Details
-------

- Most operations on a *DataHammer* instance return a value or a new instance, they do not mutate the
  contained data, although a returned ITEM could be mutated by the calling code.

- The contained data can be retrieved with the invert operator (**~**).  It will be a **list**
  unless constructed with a single ITEM, in which case that ITEM will be returned.

- In order to allow accessing arbitrary ITEM attributes uses the dot notation, **public functions start
  with a single underscore**, in contrast to typical Python conventions.  See `Functions`_.

- It uses a **list** as its top-level container, and will convert a **tuple** and some generators into a
  **list**.

- When constructed with a single ITEM, that item will be wrapped in a **list** and *most* operations will
  be identitical to having been constructed with a list with that single ITEM.

- It uses '.' to access *dict* members or object attributes, using **None** for items where there is no key or
  attribute with the specified name, thus no *KeyError* or *AttributeError* will be raised.

- Almost all operations will silently ignore items that do not have a member with the "intended" key, attribute
  or index.

- There is a **Mutator** class returned by the **_mutator()** function that is designed to allow modifying the
  data in-place for some of the
  `Augmented Assignment statements <https://docs.python.org/3/reference/simple_stmts.html#grammar-token-augmented_assignment_stmt>`_.

Known Issues
^^^^^^^^^^^^

- Using "*ITEM in OBJ*" works as you probably expect, but avoid using "*OBJ in OTHER*" for iterable
  containers. [6]_

- By design and intent, the bitwise operators (`&`, `|`, `^`) actually create a new instance by applying
  the `and`, `or` and `xor` operators, respectively.  This is because those keyword operators cannot be
  overridden to return an object as we wish.

- There are missing operators that could be added. Among these are **del** (attribute or key),
  and the bitwise math operators.


Construction
^^^^^^^^^^^^

Creating a *DataHammer* can take several sources for its input.  It is designed for use on a **list** of items
with the same schema.

+--------------------+----------------------------------------------------------------+
|  **Parameters**    |     **Description**                                            |
+====================+================================================================+
| ``data``           | This must be one of:                                           |
|                    |                                                                |
|                    | * A `list` of ITEMS.                                           |
|                    | * A single, non-`list` ITEM.                                   |
|                    |                                                                |
|                    | If the **json** value is true, then `data` can be either of:   |
|                    |                                                                |
|                    | * A `file` object, from which *all* data is read, and the      |
|                    |   results are treated as TEXT, or...                           |
|                    | * TEXT to be parsed as JSON.                                   |
+--------------------+----------------------------------------------------------------+
| ``copy``           | If given and true, then a `deepcopy` will be made of `data`.   |
+--------------------+----------------------------------------------------------------+
| ``json``           | If provided, it should either be `True` or a dict of arguments |
|                    | to be passed to *JSON.loads()* for when `data` is of either    |
|                    | the `file` or `TEXT` forms.                                    |
+--------------------+----------------------------------------------------------------+


Operations
^^^^^^^^^^

This is a list of supported operations, including applying builtin Python functions. [1]_

+------------------------------------------+---------------------------------------------------------------+
|             **Operation**                |     **Description**                                           |
+==========================================+===============================================================+
| ``~OBJ``                                 | Returns the contained data.                                   |
+------------------------------------------+---------------------------------------------------------------+
| | ``OBJ.index``                          | Creates a list by applying the *index* (an *int* for *list*   |
| | ``OBJ._ind(index)``                    | items, a key for *dict* items, or the name of an *attribute*  |
| | ``OBJ._get(index)``                    | or *property*), returning a *DataHammer* instance created     |
|                                          | using that list. [2]_                                         |
+------------------------------------------+---------------------------------------------------------------+
| | ``OBJ`` *op* ``OTHER``                 | Return a *DataHammer* instance with a bool result from the    |
| |  *op* can be: ``< <= == != >= >``      | comparison of each ITEM with OTHER. [3]_                      |
|                                          |                                                               |
|                                          | To test equality of contents, use: *~OBJ == OTHER*            |
+------------------------------------------+---------------------------------------------------------------+
| | ``OBJ`` *bitop* ``OTHER``              | Return a *DataHammer* instance with the results of applying   |
| | ``OTHER`` *bitop* ``OBJ``              | `and`, `or` and a "bool-xor" to each *ITEM* and *OTHER*, or   |
| |  *bitop* can be: ``& ^ |``             | (*OTHER* and *ITEM*).  These are needed since those keywords  |
|                                          | cannot be overridden in the desired fashion. [4]_             |
+------------------------------------------+---------------------------------------------------------------+
| | ``OBJ`` *mathop* ``OTHER``             | Return a *DataHammer* instance with the results of applying   |
| |  *mathop* can be: ``+ - * / // ** %``  | a math operators in: *ITEM mathop OTHER*. [3]_                |
+------------------------------------------+---------------------------------------------------------------+
| | ``OTHER`` *mathop* ``OBJ``             | Return a *DataHammer* instance with the results of applying   |
| |  *mathop* can be: ``+ - * / // ** %``  | a math operators in: *OTHER mathop ITEM*. [3]_                |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ[indexes]``                         | Depending on the argument, returns a *DataHammer* instance, a |
|                                          | single contained ITEM, or a list of ITEMs. [4]_               |
|                                          | See `Indexing`_, for more information.                        |
+------------------------------------------+---------------------------------------------------------------+
| | ``OBJ._bool()``                        | Return a *DataHammer* instance with the results of applying   |
| | ``OBJ._int()``                         | the builtin type (*of the same name w/o the underscore*) to   |
| | ``OBJ._float()``                       | each item in the list.                                        |
| | ``OBJ._long()``                        | *(Use of 'long' is only allowed for Python 2)*                |
+------------------------------------------+---------------------------------------------------------------+
| ``reversed(OBJ)``                        | Return a *DataHammer* instance with the contained data in     |
|                                          | reversed order.                                               |
+------------------------------------------+---------------------------------------------------------------+
| ``len(OBJ)``                             | Return an *int* for the number of contained data ITEMs.       |
+------------------------------------------+---------------------------------------------------------------+
| ``hash(OBJ)``                            | Return an *int* that is the hash of the tuple of the hash of  |
|                                          | every ITEM.                                                   |
|                                          | This will raise an exception if *any* ITEM cannot be hashed.  |
+------------------------------------------+---------------------------------------------------------------+
| ``ARG in OBJ``                           | Return a bool, which is `True` if any *ITEM == OBJ*.          |
|                                          | With regard to limiting the items tested. [3]_                |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ in ARG``                           | *This is almost never what you want!*  Return a single bool,  |
|                                          | ignoring of contents of ARG or OBJ.  The result is `True` if  |
|                                          | neither ARG nor OBJ are empty, and `False` if they both are.  |
+------------------------------------------+---------------------------------------------------------------+
| ``-OBJ``    *(unary minus)*              | Return a *DataHammer* instance with the results of applying   |
|                                          | *not ITEM* on each item.                                      |
+------------------------------------------+---------------------------------------------------------------+


Functions
^^^^^^^^^

This is a list of supported functions. [1]_

+------------------------------------------+---------------------------------------------------------------+
|            **Function**                  |     **Description**                                           |
+==========================================+===============================================================+
| | ``OBJ._ind(name)``                     | Attribute, index or *dict* key dereference. [2]_              |
| | ``OBJ._get(name)``                     |                                                               |
+------------------------------------------+---------------------------------------------------------------+
| ``str(OBJ)``                             | Returns a JSON dump of the contained data.                    |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._contains(ARG)``                   | Return a *DataHammer* instance with the results of applying   |
|                                          | *ARG in ITEM* for each item.                                  |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._apply(FUNC, ARG, *ARGS, **KWDS)`` | Return a *DataHammer* instance with the results of applying   |
|                                          | ``FUNC(ITEM, ARG, *ARGS, **KWDS)`` to each item. [3]_         |
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
|                                          | INDEX, and with ITEM(s) inserted there. [5]_                  |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._slice(START [, END [, STEP ] ])`` | Return a *DataHammer* instance with the list sliced according |
|                                          | to the given indices (like *list* slicing works).             |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._flatten()``                       | Return a *DataHammer* instance with contained items that are  |
|                                          | the result of flattening *this* instance's contained items by |
|                                          | one level. Sub-items are added in iteration-order for items   |
|                                          | that are a *set*, *list* or *tuple* and for values from a     |
|                                          | *dict*.                                                       |
|                                          |                                                               |
|                                          | Other types are not flattened, and are added as-is.           |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._tuple(SELECTOR, SELECTOR, ...)``  | Return a tuple of results for each contained item, the result |
|                                          | will be a tuple of values from the items, dereferenced by the |
|                                          | *SELECTOR* parameters, in the same order. See [8]_            |
|                                          |                                                               |
|                                          | Only named *SELECTOR* parameters are allowed.                 |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._toCSV(SELECTOR, SELECTOR, ...)``  | Return a tuple of `str` like a `Comma Separated Values` file, |
|                                          | the first `str` represents the headers for each column, and   |
|                                          | each subsequent contains a CSV-style representation of the    |
|                                          | requested values from each item (which must be serializable). |
|                                          | See [8]_                                                      |
|                                          |                                                               |
|                                          | Both positional and named *SELECTOR* parameters are allowed.  |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._pick(SELECTOR, SELECTOR, ...)``   | Return a *DataHammer* instance of *dict* items made from one  |
|                                          | or more sub-items specified by the *SELECTOR*, as either      |
|                                          | positional or named parameters.                               |
|                                          | Parameters dictate the keys in the resulting items. See [8]_  |
|                                          |                                                               |
|                                          | Both positional and named *SELECTOR* parameters are allowed.  |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._groupby(GRP, VALS [, POST])``     | Return a *DataHammer* instance of *dict* items made by taking |
|                                          | all sub-items specified by `VALS` and combine them with other |
|                                          | items with the same `GRP` values.  It is similar to the `SQL` |
|                                          | **GROUP BY** clause.  See [8]_ and [Grouping]_.               |
|                                          |                                                               |
|                                          | Both positional and named *SELECTOR* parameters are allowed.  |
+------------------------------------------+---------------------------------------------------------------+
| ``OBJ._mutator()``                       | Returns a *DataHammer.Mutator* instance to be used for making |
|                                          | modifications to the contained data.  See `Mutators`_.        |
+------------------------------------------+---------------------------------------------------------------+


Indexing
^^^^^^^^

Indexing a *DataHammer* instance with *[]* allows simple access to items from the contained data, but
there are various types of parameters types allowed. [4]_

1. Indexing with an **int** or an implicit or explicit **slice** object works like indexing **list**; the
   result is identical to **(~OBJ)[...]**.

   * A single item is returned with an **int** argument, and can raise an IndexError.
   * A (possibly empty) list of items is returned with either:

     * An explicit **slice** argument, eg:   OBJ[slice(1, None, 5)]
     * An implicit **slice** argument, eg:   OBJ[1::5]

2. Indexing with a **list**, **tuple** or a *DataHammer* instance, will return another *DataHammer*
   instance. [3]_  The parameter must either be all **bool** or all **int**, and they
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


Grouping
^^^^^^^^

The *_groupby(GROUP, VALUES [, POSTPROC])* method creates a new *DataHammer* instance, grouping values from
multiple source items.  It functions somewhat like the **GROUP BY** feature of SQL, however rather than
necessarily combining column values, a the list of values is created.

The `GROUP` and `VALUES` parameters should be either a list/tuple or a dict.

- Strings in the list/tuple are treated like named `SELECTOR` parameters
- Items in a dict are treated like named `SELECTOR` parameters.

For each unique sets of values for the `GROUP` keys, one item will exist in the resulting instance. Each of
the new items will contain the grouping values and a value per `VALUES` key.  The `GROUP` and `VALUES`
parameters may be either a list/tuple or a dict of `SELECTOR` parameters (see above).

For every key in the `VALUES` parameter, a list is built with the corresponding values, one list for each
set of `GROUP` values.

The `POSTPROC` parameter parameter, is optional and unless provided: each resulting item will contain the
corresponding list for each key in `VALUES`.  If `FUNC` is provided, it will be called once per resulting
item.  The lists are passed parameters in the same order as the keys in `VALUES`.

Note that the order of the resulting items will be the same as the order of the first occurence of that set
of `GROUP` keys in the source items.  And the order of the list of values for each `VALUES` key is the same
as the order that those occurred in the source items.


Mutators
^^^^^^^^

There is some support for making modifications to the data contained within a *DataHammer*, beyond
direct access.  This is done with the *DataHammer._mutator* method on the instance.

Here **MUT** is used as a shorthand for **OBJ._mutator()** - which returns a *DataHammer.Mutator*
instance, and the name *Mutator* is also used for *DataHammer.Mutator*.


+-----------------------------------------+----------------------------------------------------------------+
|    **Functions and Operation**          |     **Description**                                            |
+=========================================+================================================================+
| ``MUT = OBJ._mutator()``                | Returns a new *Mutator* for the given *DataHammer* instance.   |
+-----------------------------------------+----------------------------------------------------------------+
| ``~MUT``                                | Returns the *DataHammer* instance for this *Mutator*.          |
+-----------------------------------------+----------------------------------------------------------------+
| | ``MUT.index``                         | Returns a new *Mutator* instance useful for modifying the      |
| | ``MUT[index]``                        | key, attribute or list item at *index*. [7]_                   |
| | ``MUT._get(index)``                   |                                                                |
| | ``MUT._ind(index)``                   | Note that *all of these forms work identically*, though the    |
|                                         | first form can only be used with valid identifier names. This  |
|                                         | is in contrast with **[]** on a *DataHammer* instance where    |
|                                         | it returns an item from the contained data.                    |
+-----------------------------------------+----------------------------------------------------------------+
| | ``MUT`` *op* ``OTHER``                | Update the item member for the given *Mutator* instance, with  |
| |  *op* can be: ``+= -= *= /= **= //=`` | the given operation, which should be number (or object that    |
|                                         | supports that operation).                                      |
+-----------------------------------------+----------------------------------------------------------------+
| ``MUT._set(OTHER)``                     | Update the value designated by the given *Mutator* instance,   |
|                                         | overwriting with the given value(s).  If *OTHER* is a list,    |
|                                         | tuple or *DataHammer* instance, then an interator is used,     |
|                                         | and application stops when the end is reached. [3]_            |
+-----------------------------------------+----------------------------------------------------------------+
| ``MUT._setall(OTHER)``                  | Like ``MUT._set(OTHER)`` but regardless of the type, *OTHER*   |
|                                         | is used without iterating.  Used to set all rows to the same   |
|                                         | *list* or *tuple* value, but can be used with any value/type.  |
+-----------------------------------------+----------------------------------------------------------------+
| ``MUT._apply(FUNC, *ARGS, **KWDS)``     | Update the value designated by the given *Mutator* instance,   |
|                                         | overwriting with the the *return value* from calling:          |
|                                         | **``FUNC(VALUE, *ARGS, **KWDS)``**.                            |
+-----------------------------------------+----------------------------------------------------------------+

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


Installation
------------
Install the package using **pip**, eg:

  `pip install --user datahammer`

Or for a specific version of Python:

  `python3 -m pip --user install datahammer`


To the source git repository, use:

  `git clone https://github.com/n2vram/datahammer.git`


Releases
^^^^^^^^

   +-------------+--------------------------------------------------------+
   | **Version** | **Description**                                        |
   +=============+========================================================+
   |     0.9     | Initial release, documentation prototyping.            |
   +-------------+--------------------------------------------------------+
   |    0.9.1    | Addition of "_pick" method.                            |
   +-------------+--------------------------------------------------------+
   |    0.9.2    | Addition of "_flatten" and "_toCSV" methods.           |
   +-------------+--------------------------------------------------------+
   |    0.9.4    | Addition of "_groupby" and "_tuples" methods.          |
   +-------------+--------------------------------------------------------+


Reporting Issues, Contributing
------------------------------

As an open source project, *DataHammer* welcomes contributions and feedback.

1. Report any issues, including with the functionality or with the documentation
   via the GitHub project: https://github.com/n2vram/datahammer/issues

2. To contribute to the source code, please use a GitHub pull request for the
   project, making sure to include full/extensive unit tests for any changes.  Note
   that if you cannot create a PR, then open an issue and attach a `diff` output
   there. https://github.com/n2vram/datahammer/

3. To translate the documentation, please follow the same process as for source
   code contributions.


Foot Notes
----------

.. [1]  Tokens

In these examples, *OBJ* refers to a *DataHammer* instance, *LIST* refers to the list of
contained items, and *ITEM* refers to an item in the contained list or directly in the *OBJ*.


.. [2]  Dereferences

An attribute dereference (eg: *OBJ.index*) and the methods *OBJ._ind(index)* and *OBJ._get(index)* all
function identically, returning a new **DataHammer** instance.  The latter are provided for use when
*index* is an *int* or otherwise not a valid string identifier.


.. [3]  Scalars, Vectors and DataHammers

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


.. [4]  Bracket Indexing

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


.. [5]  Slicing

This works similar to the *slice* method of the
`Javascript Array <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/slice>`_
class.


.. [6]  In / Contains

Using "*ITEM in OBJ*" returns True if ITEM matches one of the items in OBJ, using the operator **==**
for the test.  However, using *OBJ in OTHER* for an iterable containers *OTHER*, is useless.
useless.

Using "*OBJ in OTHER*" will evaluate the expression "**X == OBJ**" for each item X in OTHER,, resulting
in a list of bool.  Unless either *OTHER* or *OBJ* are empty, this means a non-empty list will be
converted to **True** even if all of the comparisons fail.


.. [7]  Mutator

*Mutator* operations dereference items based on the type of an item, regardless of the type of other items in
the contained data.  Meaning: if a *DataHammer* with two items contains a `dict` with a key "foo" and an object
with an attribute "foo", then using **OBJ._mutator().foo** will update differently.


.. [8] *SELECTOR* Syntax.

The value of a *SELECTOR* must be a `str`, but depending on the method can be named or positional.

1. For positional parameters, the text after the last dot, if any, is used for the resulting key.
2. For named parameters, the value will be used to fetch the value, and the parameter name will be used for
   the key in the resulting item.
3. For both, a dot (`.`) indicates a sub-key, like normal dot notation and/or the *_ind()* method.

*Caveats*:

4. If there are multiple parameters that result in the same key, the result is undefined.
5. Currently, positional parameters are processed in order before the named parameters,
   but that is not guaranteed to be true in future releases.
6. Currently, a bare int (in decimal form) is used to index into lists, but that syntax is not
   guaranteed to be true in future releases.  If a bare int is used as the last component of a
   postitional parameter value, the resulting key will be a `str` - the decimal value.


Examples:
^^^^^^^^^
     
- The positional parameter **"b.b1"** would dererence a value like *OBJ.b.b1*, and the resulting key would be
  the part after the last dot: **"b1"**.

- The named parameter **animal="b.b2"** would dererence like *OBJ.b.b2*, and the resulting key would be
  **"animal"**.

.. code:: python

    >>> dh = DataHammer([
    ...   {"a": 100, "b": {"b1": [101, 102, 103], "b2": "ape"}, "c": ["Apple", "Anise"]},
    ...   {"a": 200, "b": {"b1": [201, 202, 203], "b2": "bat"}, "c": ["Banana", "Basil"]},
    ...   {"a": 300, "b": {"b1": [301, 302, 303], "b2": "cat"}, "c": ["Cherry", "Cayenne"]}
    ... ])
  
    >>> ~dh._pick('a', 'b.b1', animal='b.b2', food='c', nil='this.is.missing')
    [{'a': 100, 'b1': [101, 102, 103], 'animal': 'ape', 'food': ['Apple', 'Anise'], 'nil': None},
     {'a': 200, 'b1': [201, 202, 203], 'animal': 'bat', 'food': ['Banana', 'Basil'], 'nil': None},
     {'a': 300, 'b1': [301, 302, 303], 'animal': 'cat', 'food': ['Cherry', 'Cayenne'], 'nil': None}]         

    #### Result is undefined due to the key collision.
    >>> ~dh._pick('b.b1', b1='c')

    ## This '.0' syntax *might* change in future releases.
    >>> ~dh._pick(animal='b.b2', fruit='c.0')
    [{'animal': 'ape', 'fruit': 'Apple'},
     {'animal': 'bat', 'fruit': 'Banana'},
     {'animal': 'cat', 'fruit': 'Carmel'}]


