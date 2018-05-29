datahammer
##########

`Version 0.9.8`

"When all you have is a hammer, everything looks like a nail." - *Anonymous*

----------

*Note that although the version is not yet at 1.0 the code is production-ready.*
*It has 100% unit test coverage, is extensively document and has considerable examples.*
*The lower version is soley due to concern with the clarity of this documentation.*


**TL;DR:** Too anxious to see just what *DataHammer* can do? Check out the `DataHammer Examples`_.

----------

.. contents:: **Index**
   :depth: 2
   :local:

.. style table { border: 2px solid red; font-family: fujimoto; }

Summary
=======

This module provides an easy way to filter, inspect, analyze and manipulate many similar data items.  It was
designed to handle plain data types, especially the output from parsing JSON.  It is designed to allow
operations to be done a concise fashion, and on all items in a simple parallel manner.

It works on many data types, but excels at handling of *list*, *tuple* and *dict* values - and was designed
primarily for handling similar result objects from parsing JSON or XML.

In the design, concise usages was favored over speed of performance - although for data sets of less than a
million records it is still quite performant.  It was inspired by a need for a concise data manipulation
syntax and by the projects `jQuery <https://jquery.com/>`_ and `jq <https://stedolan.github.io/sjq/>`_,
and as such it also has no dependencies beyond a standar Python instance.


Details
=======

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


Build Status
------------

Current status:

.. image:: https://travis-ci.org/n2vram/datahammer.svg?master
    :alt: Build Status
    :target: https://travis-ci.org/n2vram/datahammer


Known Issues
------------

- Using "*ITEM in OBJ*" works as you probably expect, but avoid using "*OBJ in OTHER*" for iterable
  containers. [6]_

- By design and intent, the bitwise operators (`&`, `|`, `^`) actually create a new instance by applying
  the `and`, `or` and `xor` operators, respectively.  This is because those keyword operators cannot be
  overridden to return an object as we wish.

- There are missing operators that could be added. Among these are **del** (attribute or key),
  and the bitwise math operators.

- The ``OBJ._long()`` method was removed in version 0.9.6, since it was complicating the code and testing,
  and is identical to using: ``OBJ._apply(long)``  Apologies for the breakage, if you hit that.

- The ``OBJ._toCSV()`` method changed in version 0.9.7, since it wasn't using the builtin *csv* package,
  and was using a backslash to escape double-quotes within the quoted text, rather than a pair of
  consecutive double-quotes. For example, the previous output ``"Derrial \"Preacher\" Book"`` is now
  output as ``"Derrial ""Preacher"" Book"``.


Construction
------------

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

NOTE: The ``OBJ._long()`` method was removed in version 0.9.6, since it was complicating the code and testing,
and is identical to using: ``OBJ._apply(long)``

Functions
---------

This is a list of supported functions. [1]_

+-------------------------------------------+---------------------------------------------------------------+
|            **Function**                   |     **Description**                                           |
+===========================================+===============================================================+
| | ``OBJ._ind(name)``                      | Attribute, index or *dict* key dereference. [2]_              |
| | ``OBJ._get(name)``                      |                                                               |
+-------------------------------------------+---------------------------------------------------------------+
| ``str(OBJ)``                              | Returns a JSON dump of the contained data.                    |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._contains(ARG)``                    | Return a *DataHammer* instance with the results of applying   |
|                                           | *ARG in ITEM* for each item.                                  |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._in(ARG)``                          | Return a *DataHammer* instance with the results of applying   |
|                                           | *ITEM in ARG* for each item.                                  |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._apply(FUNC, ARG, *ARGS, **KWDS)``  | Return a *DataHammer* instance with the results of applying   |
|                                           | ``FUNC(ITEM, ARG, *ARGS, **KWDS)`` to each item. [3]_         |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._strip(ARG)``                       | Return a *DataHammer* instance with only the desired items.   |
|                                           | Based on the type of ARG given, the new instance has only the |
|                                           | items for which the result is true of:                        |
|                                           | 1. If ARG is not given:  *bool(ITEM)*                         |
|                                           | 2. If ARG is a callable: *ARG(ITEM)*                          |
|                                           | 3. If ARG is a list, tuple or set: *(ITEM in ARG)*            |
|                                           | 4. Otherwise: *ITEM == ARG*                                   |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._insert(INDEX, ITEM)``              | Return a *DataHammer* instance with ITEM inserted at INDEX.   |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._extend(INDEX, ITEMS)``             | Return a *DataHammer* instance with ITEMS added at the end.   |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._splice(INDEX, DELNUM, *ITEM)``     | Return a *DataHammer* instance with DELNUM items deleted at   |
|                                           | INDEX, and with ITEM(s) inserted there. [5]_                  |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._slice(START [, END [, STEP ] ])``  | Return a *DataHammer* instance with the list sliced according |
|                                           | to the given indices (like *list* slicing works).             |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._flatten()``                        | Return a *DataHammer* instance with contained items that are  |
|                                           | the result of flattening *this* instance's contained items by |
|                                           | one level. Sub-items are added in iteration-order for items   |
|                                           | that are a *set*, *list* or *tuple* and for values from a     |
|                                           | *dict*.                                                       |
|                                           |                                                               |
|                                           | Other types are not flattened, and are added as-is.           |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._tuple(SELECTOR, SELECTOR, ...)``   | Return a tuple of results for each contained item, the result |
|                                           | will be a tuple of values from the items, dereferenced by the |
|                                           | *SELECTOR* parameters, in the same order. See [8]_            |
|                                           |                                                               |
|                                           | Only named *SELECTOR* parameters are allowed.                 |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._toCSV(SELECTOR, SELECTOR, ...)``   | Return a tuple of `str` like a `Comma Separated Values` file, |
|                                           | the first `str` represents the headers for each column, and   |
|                                           | each subsequent contains a CSV-style representation of the    |
|                                           | requested values from each item (which must be serializable). |
|                                           | See [8]_                                                      |
|                                           |                                                               |
|                                           | Both positional and named *SELECTOR* parameters are allowed.  |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._pick(SELECTOR, SELECTOR, ...)``    | Return a *DataHammer* instance of *dict* items made from one  |
|                                           | or more sub-items specified by the *SELECTOR*, as either      |
|                                           | positional or named parameters.                               |
|                                           | Parameters dictate the keys in the resulting items. See [8]_  |
|                                           |                                                               |
|                                           | Both positional and named *SELECTOR* parameters are allowed.  |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._groupby(GRP, VALS [, POST])``      | Return a *DataHammer* instance of *dict* items made by taking |
|                                           | all sub-items specified by `VALS` and combine them with other |
|                                           | items with the same `GRP` values.  It is similar to the `SQL` |
|                                           | **GROUP BY** clause.  See [8]_ and `Grouping`_.               |
|                                           |                                                               |
|                                           | Both positional and named *SELECTOR* parameters are allowed.  |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._join(KEYS, OBJ [,FLAGS][,MERGE])`` | Return a *DataHammer* instance of *dict* items from merging   |
|                                           | items from this instance and **OBJ**, joining on the values   |
|                                           | corresponding to the `KEYS`.  The `FLAGS` parameter controls  |
|                                           | specifics. Somewhat similar to the `SQL` **JOIN** operations. |
|                                           | See `Joining`_ and the `Deeper Examples`_.                    |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._unique(KEYS [,UNIQUE])``           | Return a *DataHammer* instance with items from this instance, |
|                                           | based on the uniqueness of the values for `KEYS`.  The        |
|                                           | `UNIQUE` parameter sets handling for items with duplicate key |
|                                           | values.                                                       |
|                                           |                                                               |
|                                           | See `Unique`_ and the `Deeper Examples`_.                     |
+-------------------------------------------+---------------------------------------------------------------+
| ``OBJ._mutator()``                        | Returns a *DataHammer.Mutator* instance to be used for making |
|                                           | modifications to the contained data.  See `Mutators`_.        |
+-------------------------------------------+---------------------------------------------------------------+


Indexing
--------

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
--------

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


Joining
-------

There is a method for joining two *DataHammer* instances, combining items for which the specified key values match,
this is partly inspired by the **JOIN** feature of SQL (`JOIN_PRODUCT`), and partly inspired by a use case where
one-to-one matches were needed.

With the two (2) flags [`JOIN_PRODUCT` or `JOIN_ORDERED`] for handling duplicates and the four (4) flags
[`JOIN_KEEP_NEITHER`, `JOIN_KEEP_LEFT`, `JOIN_KEEP_RIGHT` or `JOIN_KEEP_BOTH`] for handling unmatched items, there
are eight (8) different `flags` combinations.

**HANDLING OF ITEMS WITH DUPLICATE KEY VALUES**

Here, "duplicate" key-values means that a set of key-values occurs more than once in the same instance.

+-------------------+--------------------------------------------------------------------------------------+
|  "Mode" Flag Name |   Description                                                                        |
+-------------------+--------------------------------------------------------------------------------------+
| `JOIN_PRODUCT`    | Results are somewhat similar to SQL joins.  The name comes from the "Cartesian       |
|                   | Product" since the output contains an item produced from the each matching item the  |
|                   | left input and the right input.                                                      |
+-------------------+--------------------------------------------------------------------------------------+
| `JOIN_ORDERED`    | This pairs matching items from the left and the right, one-by-one.  Pairing is in    |
|                   | the same order as they were found in the input instances, and matching stops after   |
|                   | exhausting the matching items in either the right input or left input.               |
+-------------------+--------------------------------------------------------------------------------------+

If there are no duplicate entries in either input, then these modes function identically.


**HANDING OF UNMATCHED ITEMS**

An "unmatched" item is one whose key-values never occur in the items from the other instance.

Here, the INNER and OUTER join terminology is a remnant from SQL, the "KEEP" flags are equivalent and provided
since they describe the intended action.  These can be summarized thus:

+----------------------+--------------------+-----------------------------------------------------------------+
|  "Keep" Flag Name    | Inner/Outer Name   |   Deescription                                                  |
+----------------------+--------------------+-----------------------------------------------------------------+
| `JOIN_KEEP_NEITHER`  | `INNER_JOIN`       | Discard unmatched items from left and from the right.           |
+----------------------+--------------------+-----------------------------------------------------------------+
| `JOIN_KEEP_LEFT`     | `LEFT_OUTER_JOIN`  | Discard unmatched items from the right.                         |
+----------------------+--------------------+-----------------------------------------------------------------+
| `JOIN_KEEP_RIGHT`    | `RIGHT_OUTER_JOIN` | Discard unmatched items from the left.                          |
+----------------------+--------------------+-----------------------------------------------------------------+
| `JOIN_KEEP_BOTH`     | `FULL_OUTER_JOIN`  | Keep unmatched items from the left and from the right.          |
+----------------------+--------------------+-----------------------------------------------------------------+

**OUTPUT ORDER**

The order of items in the inputs dictates the order in the output.  The algorithm simply iterates over the left
input, producing zero or more outputs depending on the flags and presence of any matching items in the right input.
It then appends unmatched items from the right, if desired.

See the examples, or use it for yourself, if this is not sufficiently clear.

Notes:

  - With `JOIN_PRODUCT`, each matched item from the left will be paired with every matching item from the right, in
    the order that the right items occurred.

  - With `JOIN_ORDERED`, each item in the left will be paired with the corresponding order of the matching items in
    the right input.  After the items from the right are exhausted, the remaining items from the left input with that
    set of key-values are considered unmatched.  In addition, any items from the right input that are not consumed in
    this way are also considered unmatched.

  - With `JOIN_KEEP_LEFT` or `JOIN_KEEP_BOTH`, unmatched items from the left input will appear in the same order as
    they are found in the left input.

  - With `JOIN_KEEP_RIGHT` or `JOIN_KEEP_BOTH`, unmatched items from the right input will appear after all items
    produced from items in the left input.  They will be in the same order as they occurred the right input.



Unique
------------

The **_unique()** method allows eliminating items based on the uniqueness / duplication of key values.

Parameters are:

- `KEYS` should be a list/tuple of strings which are used as a `SELECTOR` into each item.  The associated
  values are used for the uniqueness test.  (If `KEYS` is a single string, it is handled as expected.)

  There is a special case when `KEYS` is **None**: if so, the hash of the item is used in lieu of key values.
  Obviously, all items must be hashable.

- `UNIQUE` determines which items to keep, based on key values.  `UNIQUE` may be:

  - 0 = Keep only those items that are unique, with no duplicates.
  - 1 = Keep the first item with key values, ignore subsequent duplicates.
  - 2 = Keep all instances of items that have duplicate key values.
 
In each case, the order of the items is preserved from the original data.

Note that with **unique = 2**, there will be multiple items that have the same key values; to remove those you filter
them a second time with the same `KEYS`:

    **OBJ._unique(KEYS, 2)._unique(KEYS)**


Mutators
--------

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

Installation
============

Install the package using **pip**, eg:

  `pip install --user datahammer`

Or for a specific version of Python:

  `python3 -m pip --user install datahammer`


To the source git repository, use:

  `git clone https://github.com/n2vram/datahammer.git`



Releases
--------

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
   |    0.9.5    | Moved EXAMPLES into (and reorganized) the README file. |
   |             | Configured for tests, coverage and style on Travis CI. |
   +-------------+--------------------------------------------------------+
   |    0.9.6    | Removed 'OBJ._long()' method, as it was Python2-only.  |
   +-------------+--------------------------------------------------------+
   |    0.9.7    | Added the 'OBJ._join()' and 'OBJ._fromCSV()' methods.  |
   +-------------+--------------------------------------------------------+
   |    0.9.8    | Added the 'OBJ._unique()' and 'OBJ._in()' methods.     |
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


DataHammer Examples
===================

It is probably easier to show the utility of *DataHammer* with some examples.


Simple Examples
---------------


1. To construct a *DataHammer* instance you generally a list/tuple/iterable of items.  Many builtin functions operate
   on the *DataHammer* instance as it would on the list of objects.  The original data can be returned using the tilde
   operator (`~`).

   See `Sample Data`_ for the **data** used here.

.. code:: python
    
    >>> dh = DataHammer(data)
    >>> len(dh)
    8
    >>> dh
    <datahammer.DataHammer object at 0x7f258fac34e0>
    >>> type(~dh)
    <type 'list'>
    >>> type(dh[0])
    <type 'dict'>
    >>> type(dh[:3])
    <type 'list'>
    >>> ~dh == dh[:]
    True
    >>> bool(dh)
    True


2. Accessing the sub-items uses a simple dot notation.  To allow irregular data, a `None` will represent a
   member that was not present -- no `KeyError`, `AttributeError` or `IndexError` are raised.

.. code:: python
    
    >>> ~dh.age
    [45, 57, 33, 21, 24, 60, 63, 33]
    >>> ~dh.name.last
    ['Stewart', 'Perry', 'Young', 'Lewis', 'Ward', 'Martinez', 'Evans', 'Moore']
    # No KeyError
    >>> ~dh.missingMember
    [None, None, None, None, None, None, None, None]


3. Indexing into a list sub-item cannot be done with dot notation or slicing (eg: with `[]`), so the
   *_ind()* method is provided for this reason.  As for dot notation, if an index is out of range then the
   value will be `None`.

.. code:: python
    
    # This is not a DataHammer instance, it is just the `rank` member of the fourth item.
    >>> dh.ranks[3]
    [180, 190, 111]

    # This is a DataHammer instance with the fourth item from each `rank` member, or `None`.
    >>> ~dh.ranks._ind(3)
    [None, 18, 155, None, None, 24, 64, None]


4. To avoid collisions with item members, the public methods of a *DataHammer* instance are all prefixed
   with a single underscore, which may be confusing at first, but this is also done for
   `collections.namedtuple` instances.  Methods that begin with a double underscore are not public.

.. code:: python
    
    # This 'mean' function is defined in the Sample Data section, below.
    >>> ~dh.ranks._apply(mean)
    [None, 70.33333333333333, 114.875, 160.33333333333334, 139.0, 40.2, 94.83333333333333, 97.0]

    >>> ~dh._splice(2, 4).name.first
    ['Addison', 'Katherine', 'Grace', 'Sophia']

    >>> print("\n".join(dh._toCSV(FIRST='name.first', LAST='name.last', AGE='age')))
    "FIRST","LAST","AGE"
    "Addison","Stewart",45
    "Katherine","Perry",57
    "Jack","Young",33
    "Brianna","Lewis",21
    "Logan","Ward",24
    "Logan","Martinez",60
    "Grace","Evans",63
    "Sophia","Moore",33


5. Many operators are overridden to allow operating on the item with a simple syntax, returning a new *DataHammer*
   instance with the results.  Most operators work with another *DataHammer* instance, a list/tuple or scalar values.
   In the case of a list/tuple, the length of the resulting instance will be the shorter of the two arguments.

.. code:: python


    >>> ~(dh.gender == 'F')
    [True, True, False, True, False, False, True, True]
    >>> ~(dh.salary / 1000.0)
    [10.0, 18.59, 28.64, 8.0, 8.0, 33.7, 26.22, 14.12]
    >>> ~(dh.age > [50, 40, 30])
    [False, True, True]
    >>> ~(dh.salary * 1.0 / dh.age)   # Avoid integer math.
    [222.22222222222223, 326.140350877193, 867.8787878787879, 380.95238095238096,
     333.3333333333333, 561.6666666666666, 416.1904761904762, 427.8787878787879]


6. Using many builtin operations work as you would expect, as if passing a list/tuple of the item data instead.

.. code:: python

    >>> min(dh.age), max(dh.age)
    (21, 63)
    >>> sorted(dh.location.state)
    ['Maryland', 'Maryland', 'New Jersey', 'Oklahoma', 'Oregon', 'Oregon', 'Texas', 'Texas']
    >>> sum(dh.salary)
    147270
    >>> min(dh.salary), mean(dh.salary), max(dh.salary)
    (8000, 18408.75, 33700)

    # This gives number of females, by counting occurences of `True`.
    >>> sum(dh.gender == 'F')
    5


7. Indexing with another *DataHammer* instance is another powerful feature.  Also, indexing with integers allows
   arbitrary keeping a subset of, or reordering of, the items.
   
.. code:: python

    >>> len(dh.age < 30), sum(dh.age < 30)
    (8, 2)
    >>> twenties = (20 <= dh.age < 30)
    >>> ~twenties
    [False, False, False, True, True, False, False, False]
    >>> ~dh[twenties].name
    [{'first': 'Brianna', 'last': 'Lewis'}, {'first': 'Logan', 'last': 'Ward'}]
    >>> ~dh.name.last
    ['Stewart', 'Perry', 'Young', 'Lewis', 'Ward', 'Martinez', 'Evans', 'Moore']
    >>> ~dh[(0, 5, 3, 4)].name.last
    ['Stewart', 'Martinez', 'Lewis', 'Ward']
   

Deeper Examples
---------------

These demonstrate the extracting and manipulating power of *DataHammer* instances.  Note that these examples and notes
are not trivial, so please read carefully so you can understand the functionality as it is designed.


8. There are methods for extracting parts of each item, including *_pick()*, *_tuples()* and *_toCSV()*. In addition
   the *_groupby()* method allows extracting only certain parts `and` combining them across the items that share
   certain values, similar to the **GROUP BY** syntax in SQL. 

   See the main README section for detailed *SELECTOR Syntax*, but the methods are demonstrated here:


   a. The *_tuples(SELECTOR [, SELECTOR ...])* method returns a tuple of tuples with extracted values in the same order
      as the names.  Only positional `SELECTOR` parameters are allowed.

    .. code:: python

        >>> dh._tuples('location.city', 'name.last', 'age')
        (('Baltimore', 'Stewart', 45),
         ('Baltimore', 'Perry', 57),
         ('Portland', 'Young', 33),
         ('San Antonio', 'Lewis', 21),
         ('Oklahoma ', 'Ward', 24),
         ('Portland', 'Martinez', 60),
         ('Jersey City', 'Evans', 63),
         ('San Antonio', 'Moore', 33))


   b. The *_toCSV(SELECTOR [, SELECTOR ...])* method returns a tuple of strings in a `Comma Separated Values`
      format. The first string is a header of the column names in order.  Each subsequent string represents the
      corresponding item in the data, in order.  Both positional and named `SELECTOR` parameters are allowed.

    .. code:: python

        >>> dh._toCSV('location.city', lname='name.last', yrs='age')
        ('"city","lname","yrs"',
         '"Baltimore","Stewart",45',
         '"Baltimore","Perry",57',
         '"Portland","Young",33',
         '"San Antonio","Lewis",21',
         '"Oklahoma ","Ward",24',
         '"Portland","Martinez",60',
         '"Jersey City","Evans",63',
         '"San Antonio","Moore",33')


   c. The *_pick(SELECTOR [, SELECTOR ...])* method returns a new *DataHammer* instance where each item is a dictionary
      with only the requested members.  Positional and named `SELECTOR` parameters are allowed.

    .. code:: python

        >>> ~dh._pick('location.state', ln='name.last', fn='name.first', years='age')
        [{'state': 'Maryland', 'ln': 'Stewart', 'fn': 'Addison', 'years': 45},
         {'state': 'Maryland', 'ln': 'Perry', 'fn': 'Katherine', 'years': 57},
         {'state': 'Oregon', 'ln': 'Young', 'fn': 'Jack', 'years': 33},
         {'state': 'Texas', 'ln': 'Lewis', 'fn': 'Brianna', 'years': 21},
         {'state': 'Oklahoma', 'ln': 'Ward', 'fn': 'Logan', 'years': 24},
         {'state': 'Oregon', 'ln': 'Martinez', 'fn': 'Logan', 'years': 60},
         {'state': 'New Jersey', 'ln': 'Evans', 'fn': 'Grace', 'years': 63},
         {'state': 'Texas', 'ln': 'Moore', 'fn': 'Sophia', 'years': 33}]


   d. The *_groupby(GROUP, VALUES [, POSTPROC])* method returns a new *DataHammer* instance, using the first list of
      keys for grouping by value, and the second list as the values to groupby. Like the **GROUP BY** functionality
      in SQL, there will be one item in the resulting instance for each unique set of values of the `GROUP` keys.

      Remember: even if passing a single key for `GROUP` or `VALUES`, it must be in a tuple or list.

    .. code:: python

        # An empty second parameter is allowed, too, the results is just the unique GROUP keys.
        >>> ~dh._groupby(['gender', 'title'], [])
        [{'gender': 'F', 'title': 'Systems Administrator'},
        {'gender': 'F', 'title': 'Bookkeeper'},
        {'gender': 'M', 'title': 'Controller'},
        {'gender': 'F', 'title': 'UX Designer'},
        {'gender': 'M', 'title': 'Web Developer'},
        {'gender': 'M', 'title': 'Assessor'},
        {'gender': 'F', 'title': 'Mobile Developer'}]

        >>> ~dh._groupby(['gender'], ('age', 'salary'))
        [{'gender': 'F', 'age': [45, 57, 21, 63, 33], 'salary': [10000, 18590, 8000, 26220, 14120]},
         {'gender': 'M', 'age': [33, 24, 60], 'salary': [28640, 8000, 33700]}]
    

     The third parameter is a callable that takes the constructed lists in `VALUES` key order, and
     returns a tuple with same number of items, in the same order.

    .. code:: python

        >>> def reductor(ages, salaries):
        ...    return (min(ages), max(ages)), (min(salaries), max(salaries))

        >>> ~dh._groupby(['gender'], ('age', 'salary'), reductor)
        [{'gender': 'F', 'age': (21, 63), 'salary': (8000, 26220)},
         {'gender': 'M', 'age': (24, 60), 'salary': (8000, 33700)}]


9. There is a method for joining two *DataHammer* instances, combining items for which the specified
   key values match.  The `JOIN_PRODUCT` mode is inspired by the **JOIN** feature of SQL, whiel
   `JOIN_ORDERED` was inspired by a use case where one-to-one matches were needed.

    .. code:: python

      >>> left = DataHammer([{"k": "A", "x": 1}, {"k": "B", "x": 2}, {"k": "C", "x": 3},
      ...     {"k": "C", "x": 4}, {"k": "D", "x": 5}])
      >>> right = DataHammer([{"k": "A", "y": 1}, {"k": "A", "y": 2}, {"k": "C", "y": 3},
      ...     {"k": "C", "y": 4}, {"k": "E", "y": 5}])

      # For JOIN_PRODUCT, each matched item from the left is paired with each the corresponding item
      # from the right.  Then the JOIN_KEEP_{...} flag determines unmatched item retention.

      # Default is ORDERED + NEITHER
      >>> ~left._join("k", right)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'A', 'x': 1, 'y': 2},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 3, 'y': 4},
       {'k': 'C', 'x': 4, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4}]

      >>> ~left._join("k", right, flags=DataHammer.JOIN_PRODUCT + DataHammer.JOIN_KEEP_NEITHER)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'A', 'x': 1, 'y': 2},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 3, 'y': 4},
       {'k': 'C', 'x': 4, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4}]

      >>> ~left._join("k", right, flags=DataHammer.JOIN_PRODUCT + DataHammer.JOIN_KEEP_RIGHT)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'A', 'x': 1, 'y': 2},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 3, 'y': 4},
       {'k': 'C', 'x': 4, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4},
       {'k': 'E', 'y': 5}]

      >>> ~left._join("k", right, flags=DataHammer.JOIN_PRODUCT + DataHammer.JOIN_KEEP_LEFT)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'A', 'x': 1, 'y': 2},
       {'k': 'B', 'x': 2},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 3, 'y': 4},
       {'k': 'C', 'x': 4, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4},
       {'k': 'D', 'x': 5}]

      >>> ~left._join("k", right, flags=DataHammer.JOIN_PRODUCT + DataHammer.JOIN_KEEP_BOTH)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'A', 'x': 1, 'y': 2},
       {'k': 'B', 'x': 2},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 3, 'y': 4},
       {'k': 'C', 'x': 4, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4},
       {'k': 'D', 'x': 5},
       {'k': 'E', 'y': 5}]

      # For JOIN_ORDERED, matched items from the left and right are paired, one-by-one, but only as
      # until either side is exhausted, the remaining items are 'unmatched' and the JOIN_KEEP_{...}
      # flag determines unmatched item retention.

      >>> ~left._join("k", right, flags=DataHammer.JOIN_ORDERED + DataHammer.JOIN_KEEP_NEITHER)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4}]

      >>> ~left._join("k", right, flags=DataHammer.JOIN_ORDERED + DataHammer.JOIN_KEEP_RIGHT)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4},
       {'k': 'A', 'y': 2},
       {'k': 'E', 'y': 5}]

      >>> ~left._join("k", right, flags=DataHammer.JOIN_ORDERED + DataHammer.JOIN_KEEP_LEFT)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'B', 'x': 2},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4},
       {'k': 'D', 'x': 5}]

      >>> ~left._join("k", right, flags=DataHammer.JOIN_ORDERED + DataHammer.JOIN_KEEP_BOTH)
      [{'k': 'A', 'x': 1, 'y': 1},
       {'k': 'B', 'x': 2},
       {'k': 'C', 'x': 3, 'y': 3},
       {'k': 'C', 'x': 4, 'y': 4},
       {'k': 'D', 'x': 5},
       {'k': 'A', 'y': 2},
       {'k': 'E', 'y': 5}]

  (*Obviously, the outputs above were reformmated for clarity.*)


10. There is a method for easily dealing with duplicate values on particular keys.
    Once again the idea of *key values* is used to determine what is considered.

    Note that if KEYS is a string, it is handled correctly.

    .. code:: python

      >>> dh = DataHammer(data)
      >>> keys = 'location.city'
      >>> Counter(dh.location.city)
      Counter({'Baltimore': 2, 'Portland': 2, 'San Antonio': 2, 'Oklahoma ': 1, 'Jersey City': 1})

      # Zero (0) gives only the unique items, where count was 1 -- all but "Mobile Developer".
      >>> ~dh._unique(keys, 0).location.city
      ['Oklahoma City', 'Jersey City']

      # The default (one, 1) gives all key values, but only the first item with the value(s)
      >>> ~dh._unique(keys).location.city
      ['Baltimore', 'Portland', 'San Antonio', 'Oklahoma City', 'Jersey City']
      >>> ~dh._unique(keys, 1).name
      [{'first': 'Addison', 'last': 'Stewart'}, {'first': 'Jack', 'last': 'Young'},
       {'first': 'Brianna', 'last': 'Lewis'}, {'first': 'Logan', 'last': 'Ward'},
       {'first': 'Grace', 'last': 'Evans'}]

      # Two (2) gives only those items that have a duplicate (of 'location.city').
      >>> ~dh._unique(keys, 2)._pick('name', keys)
      [{'name': {'first': 'Addison', 'last': 'Stewart'}, 'city': 'Baltimore'},
       {'name': {'first': 'Katherine', 'last': 'Perry'}, 'city': 'Baltimore'},
       {'name': {'first': 'Jack', 'last': 'Young'}, 'city': 'Portland'},
       {'name': {'first': 'Brianna', 'last': 'Lewis'}, 'city': 'San Antonio'},
       {'name': {'first': 'Logan', 'last': 'Martinez'}, 'city': 'Portland'},
       {'name': {'first': 'Sophia', 'last': 'Moore'}, 'city': 'San Antonio'}]

      # To get the unique set of duplicated values for a given set of keys, you can use a second
      # pass, using the default (1) for `unique`.
      >>> ~dh._unique(keys, 2)._unique(keys).location
      [{'city': 'Baltimore', 'state': 'Maryland'},
       {'city': 'Portland', 'state': 'Oregon'},
       {'city': 'San Antonio', 'state': 'Texas'}]


Formatting Specification
------------------------

11. An extension is provided for formatting, using the **j** `type`.  Each item will be printed as JSON using
    *json.dumps()*.  In particular, the only allowed parts to the *format_spec* are:

   a. A negative `sign` will cause a newline to be inserted between the item outputs.
   b. A non-zero `width` causes the item JSON is used as the indent within the item output
   c. The only `type` supported is "**j**".

.. code:: python 

    >>> dh.location[0:2]
    [{'city': 'Baltimore', 'state': 'Maryland'}, {'city': 'Madison', 'state': 'Wisconsin'}]
    >>> print("{:-j}".format(dh.location._slice(0,2)))
    [{"city":"Baltimore","state":"Maryland"},
    {"city":"Madison","state":"Wisconsin"}]
    >>> print("{:-3j}".format(dh.location._slice(0,2)))
    [{
       "city":"Baltimore",
       "state":"Maryland"
    },
    {
       "city":"Madison",
       "state":"Wisconsin"
    }]


Warnings and Caveats
--------------------

12. Warning: To combine multiple instances with `bool` values you must use the `&` and `|`, and
    *not* use `and` and `or` as you would with Python `bool` values.

 .. code:: python

    >>> dh1 = DataHammer([False, False, True, True])
    >>> dh2 = DataHammer([False, True, False, True])

    # These are item-wise correct results
    >>> ~(dh1 & dh2)
    [False, False, False, True]
    >>> ~(dh1 | dh2)
    [False, True, True, True]

    # Since the objects are not empty, 'or' returns the first, 'and' returns the second:
    >>> (dh1 or dh2) == dh1
    True
    >>> (dh1 and dh2) == dh2
    True


Other Examples
--------------

13. Given a JSON file that has metadata separated from the data values, we can easily
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

      # Here 'norm' contains 1260 items, each a dict with the same schema.
      >>> len(norm)
      1260
      >>> print(norm[0])
      {'sid': 1, 'id': 'A0447302-02D8-4EFD-AB68-777680645F02', 'position': 1,
       'created_at': 1437380960, 'created_meta': '707861', 'updated_at': 1437380960,
       'updated_meta': '707861', 'meta': None, 'Year': '2012', 'Region': 'Capital Region',
       'NAICS Code': '11', 'Industry': 'Agriculture, Forestry, Fishing and Hunting',
       'Jobs': '2183'}

      # Use collections.Counter to count the number of instances of values:
      >>> Counter(norm.Year)
      Counter({'2012': 210, '2013': 210, '2014': 210, '2015': 210, '2017': 210, '2016': 210})
      >>> Counter(norm._get('NAICS Code'))
      Counter({'11': 60, '21': 60, '22': 60, '23': 60, '42': 60, '51': 60, '52': 60,
               '53': 60, '54': 60, '55': 60, '56': 60, '61': 60, '62': 60, '71': 60,
               '72': 60, '81': 60, '90': 60, '99': 60, '31-33': 30, '44-45': 30,
               '48-49': 30, '31': 30, '44': 30, '48': 30})

      # Use '&' to require both conditions, it is a row-wise `and` of the separate tests.
      >>> cap2013 = norm[(norm.Year == '2013') & norm.Region._contains('Capital Region')]
      >>> len(cap2013)
      21
      >>> keepers = norm.Jobs._int() > 500000
      >>> sum(keepers)
      12
      >>> large = norm[keepers]
      >>> len(large)
      12
      >>> large[0]
      {'sid': 121, 'id': '98A53A4E-712C-47A9-9106-C9062DB8CBBD', 'position': 121,
       'created_at': 1437380961, 'created_meta': '707861', 'updated_at': 1437380961,
       'updated_meta': '707861', 'meta': None, 'Year': '2012', 'Region': 'New York City',
       'NAICS Code': '62', 'Industry': 'Health Care and Social Assistance', 'Jobs': '591686'}
      >>> ~norm.Region._unique(None)
      ['Capital Region', 'Central New York', 'Finger Lakes', 'Long Island', 'Mid-Hudson',
       'New York City', 'North Country', 'Southern Tier ', 'Western New York ', 'Mohawk Valley',
       'Southern Tier', 'Western New York']
      >>> Counter(norm.Region)
      Counter({'Capital Region': 126, 'Central New York': 126, 'Finger Lakes': 126,
               'Long Island': 126, 'Mid-Hudson': 126, 'New York City': 126, 'North Country': 126,
               'Mohawk Valley': 126, 'Southern Tier ': 63, 'Western New York ': 63,
               'Southern Tier': 63, 'Western New York': 63})
      >>> sum(norm.Region._in(['Mohawk Valley', 'Southern Tier']))
      189


SELECTOR Examples
-----------------
     
- The positional parameter **"b.b1"** would dererence a value like *OBJ.b.b1*, and the resulting key would be
  the part after the last dot: **"b1"**.

- The named parameter **animal="b.b2"** would dererence like *OBJ.b.b2*, and the resulting key would be
  **"animal"**.

.. code:: python

    >>> dh = DataHammer([
          {"a": 100, "b": {"b1": [101, 102, 103], "b2": "ape"}, "c": ["Apple", "Anise"]},
          {"a": 200, "b": {"b1": [201, 202, 203], "b2": "bat"}, "c": ["Banana", "Basil"]},
          {"a": 300, "b": {"b1": [301, 302, 303], "b2": "cat"}, "c": ["Cherry", "Cayenne"]}
        ])
  
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


Sample Data
-----------

Note that the data used here is randomly generated, no relationship to
anyone living, dead or undead is intended.

.. code:: python
    
    >>> from datahammer import DataHammer
    >>> mean = lambda nums: (sum(nums) * 1.0 / len(nums)) if nums else None
    >>> data = [
        {
            "age":45,"gender":"F","location":{"city":"Baltimore","state":"Maryland"},
            "name":{"first":"Addison","last":"Stewart"},"phone":"575-917-9109",
            "ranks":[],"salary":10000,"title":"Systems Administrator"
        },
        {
            "age":57,"gender":"F","location":{"city":"Baltimore","state":"Maryland"},
            "name":{"first":"Katherine","last":"Perry"},"phone":"524-133-3495",
            "ranks":[157,200,2,18,18,27],"salary":18590,"title":"Bookkeeper"
        },
        {
            "age":33,"gender":"M","location":{"city":"Portland","state":"Oregon"},
            "name":{"first":"Jack","last":"Young"},"phone":"803-435-5879",
            "ranks":[9,157,197,155,190,56,58,97],"salary":28640,"title":"Controller"
        },
        {
            "age":21,"gender":"F","location":{"city":"San Antonio","state":"Texas"},
            "name":{"first":"Brianna","last":"Lewis"},"phone":"364-549-0753",
            "ranks":[180,190,111],"salary":8000,"title":"UX Designer"
        },
        {
            "age":24,"gender":"M","location":{"city":"Oklahoma City","state":"Oklahoma"},
            "name":{"first":"Logan","last":"Ward"},"phone":"734-410-1116",
            "ranks":[116,162],"salary":8000,"title":"Web Developer"
        },
        {
            "age":60,"gender":"M","location":{"city":"Portland","state":"Oregon"},
            "name":{"first":"Logan","last":"Martinez"},"phone":"652-193-9184",
            "ranks":[70,16,59,24,32],"salary":33700,"title":"Assessor"
        },
        {
            "age":63,"gender":"F","location":{"city":"Jersey City","state":"New Jersey"},
            "name":{"first":"Grace","last":"Evans"},"phone":"955-466-6227",
            "ranks":[123,126,118,64,110,28],"salary":26220,"title":"Mobile Developer"
        },
        {
            "age":33,"gender":"F","location":{"city":"San Antonio","state":"Texas"},
            "name":{"first":"Sophia","last":"Moore"},"phone":"636-269-3573",
            "ranks":[97],"salary":14120,"title":"Mobile Developer"
        }]


Foot Notes
==========

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
See `SELECTOR Examples`_.

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



