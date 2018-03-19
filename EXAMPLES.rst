
DataHammer Examples
###################

It is probably easier to show the utility of *DataHammer* with some examples.


1. To construct a *DataHammer* isntance you generally a list/tuple/iterable of items.  Many builtin functions operate
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


2. Accessing the sub-items uses a simple dot notation.  To allow irregular data,
   a `None` is used if a member is not present.

.. code:: python
    
    >>> ~dh.age
    [45, 57, 33, 21, 24, 60, 63, 33]
    >>> ~dh.name.last
    ['Stewart', 'Perry', 'Young', 'Lewis', 'Ward', 'Martinez', 'Evans', 'Moore']
    >>> ~dh.missingMember
    [None, None, None, None, None, None, None, None]


3. Indexing into a list item cannot be done with dot notation or slicing (eg: with `[]`), so the *_ind()* method is
   provided for this reason.  If an index is out of range then the value will be `None`.

.. code:: python
    
    # This is a *DataHammer* instance with the fourth item from each `rank` member, or `None`.
    >>> ~dh.ranks._ind(3)
    [None, 18, 155, None, None, 24, 64, None]

    # This is not even a *DataHammer* instance, it is just the `rank` member of the fourth item.
    >>> dh.ranks[3]
    [180, 190, 111]


4. To avoid collisions with item members, the public methods of a *DataHammer* instance are all prefixed with a single
   underscore, as is done for `collections.namedtuple` instances.  Methods that begin with a double underscore are not
   public.

.. code:: python
    
    >>> ~dh.ranks._apply(mean)
    [None, 70.33333333333333, 114.875, 160.33333333333334, 139.0, 40.2, 94.83333333333333, 97.0]
    >>> ~dh._splice(2, 4).name.first
    ['Addison', 'Katherine', 'Grace', 'Sophia']


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
    >>> sum(dh.gender == 'F')     # This counts occurences of True
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
   

8. There are methods for extracting parts of each item, including *_pick()*, *_tuples()* and *_toCSV()*. In addition,
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



Formatting Specification
========================

9. An extension is provided for formatting, using the **j** `type`.  Each item will be printed as JSON using
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
====================

10. Warning: To combine multiple instances with `bool` values you must use the `&` and `|`, and
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




Sample Data
===========

Note that this data is all randomly generated, no relationship to anyone is intended.

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
            "age":24,"gender":"M","location":{"city":"Oklahoma ","state":"Oklahoma"},
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


