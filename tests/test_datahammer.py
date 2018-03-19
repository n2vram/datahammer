import collections
import copy
import datetime
import gzip
import json
import logging
import os
import pytest
import random
import re
import six
import time

from datahammer import DataHammer, tname, JEncoder

logging.basicConfig(level=logging.DEBUG)


def open_file(name, mode='r', gz=False):
    path = os.path.join(os.path.dirname(__file__), 'files', name)
    return gzip.GzipFile(path, mode) if gz else open(path, mode)


def lrange(*args):
    return list(range(*args))


def dump(*args):
    for tag, obj in zip(args[::2], args[1::2]):
        logging.info("Dump: %s <%s> = %s" % (tag, tname(obj), obj))
    return obj


def compare(ecode, rcode):
    expect = eval(ecode)
    dump(ecode, expect)
    result = eval(rcode)
    dump(rcode, result)
    assert expect == ~result


def mean(numbers):
    return float(sum(numbers)) / len(numbers)


class Obj(object):
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

    def __eq__(self, other):
        return vars(self) == (vars(other) if isinstance(other, Obj) else other)

    def __repr__(self):
        return JEncoder.dumps(self.__dict__, sort_keys=1)

    __str__ = __repr__


Dictless = collections.namedtuple('Dictless', ('a', 'b'))


class Timer(object):
    def __init__(self, tag):
        self.name = tag
        self.tag = self.limit = self.start = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        took = time.time() - self.start
        if self.limit:
            return self.compare(took)

        # Limit is 3.5 seconds more than twice the parse time.
        self.limit = 3.5 + took * 2
        logging.info("It took %.3f for '%s' max=%.3f", took, self.name, self.limit)

    def compare(self, took):
        assert took <= self.limit, "Took %.3f for '%s' (max %.3f)" % (took, self.tag, self.limit)
        logging.info("Took %.3f for '%s' (vs %.3f for %s)...", took, self.tag, self.limit, self.name)

    def __call__(self, tag, func=None, *args, **kwds):
        # Subsequent calls.
        if func is None:
            self.tag = tag
            self.start = time.time()
            return self
        start = time.time()
        try:
            return func(*args, **kwds)
        finally:
            self.compare(time.time() - start)


IDENTIFIER = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')


class TestDataHammer(object):

    # Just some data used for the following tests.  Note the sizes don't have to match.
    ADATA = list(lrange(10, 30))
    BDATA = [x / 3.5 for x in lrange(100, 60, -3)]
    ZIPPED = tuple(zip(ADATA, BDATA))

    JOBS_ORIG = json.load(open_file('jobsdata.json'))
    JOBS_DATA = json.load(open_file('jobs.json'))

    PEEP_DATA = (
        dict(name=dict(first='Rex', last="O'herlihan", common='The Singing Cowboy'),
             office=dict(location='The Range', active=False), age=28),
        dict(name=dict(first='Kermit "the"', last="Frog", common=None),
             office=dict(location='The Swamp', active=True), age=75),
        dict(name=dict(first='Dana', last="Scully", common='Starbuck'),
             office=dict(location='Parts unknown', active=True), age=25))

    def test_speed(self):
        fname = os.environ.get('SPEED_TEST_JSON')
        if not fname or not os.path.isfile(fname):
            pytest.skip("Set $SPEED_TEST_JSON to manually run speed test.")

        with Timer('Read/parse') as limit:
            raw_data = open_file(fname).read()
            world = json.loads(raw_data)

        # Repeat it....
        for nloop in lrange(3):
            logging.info("Perf test loop: #%d", nloop)

            with limit("Constructor"):
                magic = DataHammer(world)

            with limit("Reconstructor"):
                DataHammer(magic)

            with limit("Fetch project_abstract"):
                magic.project_abstract

            with limit("Fetch mjsector_namecode.code"):
                magic.mjsector_namecode

            with limit("Fetch unknown keys"):
                magic.unknown_key1.unknown_key2.unknown_key3.unknown_key4

    def test_readme(self):
        obj = DataHammer(list(range(10, 15)))
        assert [10, 11, 12, 13, 14] == ~obj
        assert [10, 12, 13] == ~obj[(True, False, True, True, False, True)]
        assert [14, 12, 11, 14, 13, 11] == ~obj[(4, 2, 1, 40, -1, 3, 1)]
        assert isinstance(obj[1], int)
        assert isinstance(obj[:5], list)
        assert isinstance(obj[slice(3)], list)
        assert [10, 13] == obj[::3]
        dh1 = DataHammer(lrange(8))
        assert [10, 21] == ~(dh1 + (10, 20))
        dh2 = DataHammer((3, 1, 4))
        assert [False, True, False] == ~(dh1 == dh2)
        assert [3, 1, 4] == ~(dh1[dh2])

        dh = DataHammer([[i, i*i] for i in range(10, 15)])
        assert [[10, 100], [11, 121], [12, 144], [13, 169], [14, 196]] == ~dh
        assert [100, 121, 144, 169, 196] == ~dh._ind(1)
        assert [False, False, True, True, True] == ~(dh._ind(1) > 125)
        assert [[12, 144], [13, 169], [14, 196]] == ~dh[dh._ind(1) > 125]
        dh = DataHammer([dict(a=i, b=tuple(range(i, i*2))) for i in range(6)])
        assert (2, 3) == dh.b[2]
        dh2 = dh.b._ind(2)
        assert isinstance(dh2, DataHammer)
        assert[None, None, None, 5, 6, 7] == ~dh2

    def test_copies(self):
        original = list(dict(key="K%02d" % num, nums=tuple(lrange(num, num+10)),
                             embed=dict(foo="%d-bar" % num, bar="foo-%d" % (num/5.0)),
                             base=num, nmax=num+10) for num in lrange(100, 115, 3))

        logging.info("Original:%s", original)
        mutable = copy.deepcopy(original)
        magic = DataHammer(mutable, copy=True)
        assert ~magic == original
        mutable[0]['key'] = 'junk'
        assert mutable != ~magic
        assert ~magic != mutable
        assert original == ~magic
        assert ~magic == original

        def check(name, value, source=original):
            assert len(~value) == len(source)
            assert ~value == [e[name] for e in source]
            assert isinstance(value, DataHammer)

        check('key', magic.key)
        check('nums', magic.nums)
        check('base', magic.base)
        check('nmax', magic.nmax)
        source = [e['embed'] for e in original]
        check('bar', magic.embed.bar, source=source)
        check('foo', magic.embed.foo, source=source)

        clone = DataHammer(magic)
        assert clone == magic
        assert (~clone) == (~magic)

    def test_from_json(self):
        text = json.dumps(self.JOBS_ORIG)
        fdes = open_file('jobsdata.json')
        ham1 = DataHammer(self.JOBS_ORIG)
        ham2 = DataHammer(text, json=True)
        ham3 = DataHammer(fdes, json=dict(encoding='utf-8'))

        assert ~ham1 == self.JOBS_ORIG
        assert ~ham2 == self.JOBS_ORIG
        assert ~ham3 == self.JOBS_ORIG

    def test_iters(self):
        gener = (dict(ss=str(num), nn=num) for num in lrange(20))
        values = [dict(ss=str(num), nn=num) for num in lrange(20)]
        magic = DataHammer(gener)
        assert len(magic) == 20
        assert values == ~magic

    def test_simple_attrs(self):
        data = dict(foo='bar', bar='foo', sub=dict(foo='FOO', bar='BAR'),
                    emp=[], one=['one'], num=842.375, yes=True, lemp=[[]],
                    nil=None, no=False, zero=0, estr='')
        magic = DataHammer(copy.deepcopy(data))

        # '~' is after than '.'
        dump("~(magic.sub).foo", ~(magic.sub).foo, "~(magic.sub.foo)", ~(magic.sub.foo))
        assert ~(magic.sub).foo == ~(magic.sub.foo)
        assert ~(magic).sub.foo == ~magic.sub.foo

        # Simple dereferences...
        dump("~(magic.foo)", ~(magic.foo), "data['foo']", data['foo'])
        assert ~(magic.foo) == data['foo']
        dump("~(magic.bar)", ~(magic.bar), "data['bar']", data['bar'])
        assert ~(magic.bar) == data['bar']
        dump("~(magic.sub)", ~(magic.sub), "data['sub']", data['sub'])
        assert ~(magic.sub) == data['sub']
        dump("~(magic.sub.foo)", ~(magic.sub.foo), "data['sub']['foo']", data['sub']['foo'])
        assert ~(magic.sub.foo) == data['sub']['foo']
        dump("~(magic.sub.bar)", ~(magic.sub.bar), "data['sub']['bar']", data['sub']['bar'])
        assert ~(magic.sub.bar) == data['sub']['bar']
        dump("~(magic.num)", ~(magic.num), "data['num']", data['num'])
        assert ~(magic.num) == data['num']

        assert magic._get('num') == magic.num

        # Empty, 1-item lists work. Including a list of an empty list.
        dump("~(magic.emp)", ~(magic.emp), "data['emp']", data['emp'])
        assert ~(magic.emp) == data['emp']
        dump("~(magic.one)", ~(magic.one), "data['one']", data['one'])
        assert ~(magic.one) == data['one']
        dump("~(magic.lemp)", ~(magic.lemp), "data['lemp']", data['lemp'])
        assert ~(magic.lemp) == data['lemp']

        dump("~(magic.yes)", ~(magic.yes), "data['yes']", data['yes'])
        assert ~(magic.yes) == data['yes']

        gt_func = magic.__gt__
        assert callable(gt_func)
        assert gt_func.__name__ == '__gt__'

    def test_filtering2(self):

        def trim(a):
            return [e for e in a if e]

        ten = [10, 0, 20, 0, 30, 800]
        foo = [0, 'foo', 1.5, {}, 0, '']
        abc = ['a', '', 'b', '', 'c', None]
        nil = [set(), tuple(), {}, list(), "", False]

        data = [dict(ten=t, foo=f, abc=a, nil=n)
                for t, f, a, n in zip(ten, foo, abc, nil)]

        magic = DataHammer(data)
        assert ten == ~magic.ten
        assert foo == ~magic.foo
        assert abc == ~magic.abc
        assert nil == ~magic.nil
        assert trim(ten) == ~magic.ten._strip()
        assert trim(foo) == ~magic.foo._strip()
        assert trim(abc) == ~magic.abc._strip()
        assert trim(nil) == ~magic.nil._strip()

    def test_recurse_keys(self):
        def recurse(data, magic, crumbs, level=0):
            assert isinstance(magic, DataHammer)
            logging.info("Checking %s  <%s>.....\n--> %s\n==> %s",
                         crumbs, tname(data), json.dumps(data), magic)
            assert level < 30

            contents = ~magic
            if data:
                assert contents == data, "Failed at %s" % crumbs

            if isinstance(data, list):
                for nth, item in enumerate(data):
                    logging.info("Checking %s[%s]: %s", crumbs, nth, item)
                    recurse(item, DataHammer(magic[nth]), "{}[{}]".format(crumbs, nth), level+1)

            elif isinstance(data, dict):
                for key, value in sorted(data.items()):
                    logging.info("Checking<%s> key '%s'...", tname(value), key)
                    if IDENTIFIER.match(key):
                        pull = eval("magic.%s" % key)
                    else:
                        pull = magic._get(key)
                    recurse(value, pull, "{}[.{}]".format(crumbs, key), level+1)

        total = json.load(open_file('mrl.json'))
        magic = DataHammer(total)

        mpart = magic.paths.market_research_library.get.parameters

        tpart = total['paths']
        tpart = tpart['market_research_library']
        tpart = tpart['get']
        tpart = tpart['parameters']

        recurse(tpart, mpart, 'part')

        recurse(total, magic, 'total')

    def test_combine_jobs(self):
        # This is a test that actually uses some keys.
        # The 'meta' is a list of objects, including a "name" member,
        # Index each row in the 'data' list of lists with these names:
        magic = DataHammer(self.JOBS_ORIG)
        names = ~magic.meta.columns.name
        normalized = DataHammer(dict(zip(names, row)) for row in magic.data)
        assert self.JOBS_DATA == ~normalized
        assert all(normalized[normalized.sid < 4].Jobs == ["2183", "733", "1838"])

    def test_selectors(self):
        magic = DataHammer(self.JOBS_DATA)

        forward = lrange(1, 15)
        backward = list(reversed(forward))

        assert forward == ~magic.sid
        assert backward == ~magic.position

        # Using 'and' calls __nonzero__ which is pointless, we override the bitwise
        # operators instead:
        low1 = magic.one < 350
        low3 = magic.three < 100
        either = low1 | low3
        differ = low1 ^ low3
        both1 = low1 & low3
        both2 = (~magic.one) & low1

        dump('low1', low1, 'low3', low3, 'both1', both1, 'both2', both2)
        dump('either', either, 'differ', differ)

        assert ~low1 == [i in (3, 10, 14) for i in forward]
        assert ~low3 == [i in (2, 3, 14) for i in forward]
        assert ~either == [i in (2, 3, 10, 14) for i in forward]
        assert ~differ == [i in (2, 10) for i in forward]
        assert ~both1 == [i in (3, 14) for i in forward]
        assert ~both2 == [i in (3, 10, 14) for i in forward]

        # Test boolean negation with -OBJ:
        nonce = object()

        def keep_if(a, b):
            assert b == nonce
            return a

        for md in (low1, low3, both1, both2, either, differ):
            neg = -md
            assert not any(neg & md)
            assert all(neg | md)
            assert ~neg == [not bit for bit in ~md]

    def test_strip(self):

        ns1 = Obj(a=100, b=[1, 2], c="foobar", d=dict(d1=100, d2="blah"))
        ns2 = Obj(a=100, b=[1, 2], c="foobar", d=dict(d1=100, d2="blah"))
        assert ns1 == ns2
        assert ns1 is not ns2

        source = [True, False, None, -1, 0, 1, [], [1], tuple(), (1,), True, False,
                  None, set(), {1, 2}, -1.1, 0.0, 1.1, "", "foo", "FOO", ns1, ns2]
        dd = list(source)
        md = DataHammer(dd)

        # Default filter for truthiness.
        ddt = [e for e in dd if e]
        res = dump('ddt', ddt, 'md._strip()', ~md._strip())
        assert ddt == res

        def without(item):
            dd = list(source)
            while item in dd:
                dd.remove(item)
            return dd

        # Strip all copies of a single item
        dd1 = without(1.1)
        res = md._strip(1.1)
        dump('dd1', dd1, 'md._strip(1.1)', ~res)
        assert dd1 == ~res

        # Strip items in a tuple/list/set:
        dd2 = without({1, 2})
        res = md._strip([{1, 2}])
        dump('dd2', dd2, 'md._strip([{1, 2}])', ~res)
        assert dd2 == ~res

        # Strip a set of items.
        dd3 = without({1, 2})
        res = md._strip([{1, 2}])
        dump('dd3', dd3, 'md._strip([{1, 2}])', ~res)
        assert dd3 == ~res

        # Callable
        dd = lrange(-6, 7)
        md = DataHammer(dd)
        res = md._strip(lambda x: 0 == (x % 3))
        assert lrange(-6, 7, 3) == ~res

        # And a DataHammer.
        dd = [e for e in range(-6, 7) if e % 3]
        kill = DataHammer(lrange(-6, 7, 3))
        res = md._strip(kill)
        res = md._strip(lambda x: 0 == (x % 3))
        assert lrange(-6, 7, 3) == ~res

    def test_apply(self):
        magic = DataHammer(self.JOBS_DATA)
        mod100 = [(78, 85), (95, 6), (83, 22), (10, 61), (53, 10),
                  (56, 21), (99, 71), (91, 59), (80, 60), (14, 14),
                  (69, 6), (44, 97), (6, 40), (8, 54)]

        def func100(ele, key1, key2):
            return ((ele[key1] % 100), (ele[key2] % 100))

        modapp1 = magic._apply(lambda d: (d['one'] % 100, d['three'] % 100))
        modapp2 = magic._apply(func100, 'one', key2='three')
        dump('modapp1', modapp1, 'modapp2', modapp2)

        assert ~modapp1 == mod100
        assert ~modapp2 == mod100
        assert all(modapp1 == modapp2)

    def test_each(self):
        magic = DataHammer(self.JOBS_DATA)
        mod100 = [(78, 85), (95, 6), (83, 22), (10, 61), (53, 10), (56, 21), (99, 71),
                  (91, 59), (80, 60), (14, 14), (69, 6), (44, 97), (6, 40), (8, 54)]

        def func100(ele, key1, key2):
            return ((ele[key1] % 100), (ele[key2] % 100))

        modapp1 = magic._apply(lambda d: (d['one'] % 100, d['three'] % 100))
        modapp2 = magic._apply(func100, 'one', key2='three')
        dump('modapp1', modapp1, 'modapp2', modapp2)

        assert ~modapp1 == mod100
        assert ~modapp2 == mod100
        assert all(modapp1 == modapp2)
        assert modapp1 == modapp1

    def test_contains_reversed(self):
        data = [(len(x), x) for x in "a bb c dd ee f ggg".split()]
        magic = DataHammer(data)
        for item in data:
            dump("Item", item)
            assert item in magic
            assert magic._contains(item)
        #
        # Whenver ITEM is in OBJ.__data, then:
        # 1. We expect  (ITEM in OBJ) == True  -- and it is.
        # 2. We do NOT expect (OBJ in ITEM) == True  -- but it is,
        #    because this equates to:  any(OBJ == ITEM) which will
        #    be true for the ITEM.
        #
        for item in data + [False, None]:
            logging.info("magic in item....")
            assert magic in [item]
            logging.info("magic in item ^^^^")

        data.reverse()
        rmagic = DataHammer(data)

        assert ~reversed(rmagic) == ~magic
        assert ~reversed(magic) == ~rmagic
        assert list(reversed(data)) == ~magic
        assert data == ~reversed(magic)

        dump("reversed(DataHammer(125))", reversed(DataHammer(125)))
        item = dict(a=200, b="foobar")
        assert DataHammer(item) == reversed(DataHammer(item))

    def test_math(self):
        amagic = DataHammer(self.ADATA)
        bmagic = DataHammer(self.BDATA)

        def handle(func, name):
            xdata = list(map(func, self.ADATA))
            result = getattr(amagic, name)()
            dump(name + '(amagic)', result)
            assert ~result == xdata
            xdata = list(map(func, self.BDATA))
            result = getattr(bmagic, name)()
            dump(name + '(bmagic)', result)
            assert ~result == xdata
        handle(int, '_int')
        handle(float, '_float')
        if six.PY2:
            handle(long, '_long')

        xdata = [a * b for a, b in self.ZIPPED]
        result = amagic * bmagic
        dump('amagic * bmagic', result)
        assert ~result == xdata
        result = amagic * self.BDATA
        dump('amagic * self.BDATA', result)
        assert ~result == xdata

        xdata = [a * 3 for a in self.ADATA]
        result = amagic * 3
        dump('amagic * 3', result)
        assert ~result == xdata

        xdata = [3 * a for a in self.ADATA]
        result = 3 * amagic
        dump('3 * amagic', result)
        assert ~result == xdata

        xdata = [a / b for a, b in self.ZIPPED]
        result = amagic / bmagic
        dump('amagic / bmagic', result)
        assert ~result == xdata
        result = amagic / self.BDATA
        dump('amagic / self.BDATA', result)
        assert ~result == xdata

        xdata = [a / 3 for a in self.ADATA]
        result = amagic / 3
        dump('amagic / 3', result)
        assert ~result == xdata

        xdata = [3 / a for a in self.ADATA]
        result = 3 / amagic
        dump('3 / amagic', result)
        assert ~result == xdata

        xdata = [a + b for a, b in self.ZIPPED]
        result = amagic + bmagic
        dump('amagic + bmagic', result)
        assert ~result == xdata
        result = amagic + self.BDATA
        dump('amagic + self.BDATA', result)
        assert ~result == xdata

        xdata = [a + 3 for a in self.ADATA]
        result = amagic + 3
        dump('amagic + 3', result)
        assert ~result == xdata

        xdata = [3 + a for a in self.ADATA]
        result = 3 + amagic
        dump('3 + amagic', result)
        assert ~result == xdata

        xdata = [a % 3 for a in self.ADATA]
        result = amagic % 3
        dump('amagic % 3', result)
        assert ~result == xdata

        xdata = [3 % a for a in self.ADATA]
        result = 3 % amagic
        dump('3 % amagic', result)
        assert ~result == xdata

        xdata = [a - b for a, b in self.ZIPPED]
        result = amagic - bmagic
        dump('amagic - bmagic', result)
        assert ~result == xdata
        result = amagic - self.BDATA
        dump('amagic - self.BDATA', result)
        assert ~result == xdata

        xdata = [a - 3 for a in self.ADATA]
        result = amagic - 3
        dump('amagic - 3', result)
        assert ~result == xdata

        xdata = [3 - a for a in self.ADATA]
        result = 3 - amagic
        dump('3 - amagic', result)
        assert ~result == xdata

        xdata = [a // b for a, b in self.ZIPPED]
        result = amagic // bmagic
        dump('amagic // bmagic', result)
        assert ~result == xdata
        result = amagic // self.BDATA
        dump('amagic // self.BDATA', result)
        assert ~result == xdata

        xdata = [a // 3 for a in self.ADATA]
        result = amagic // 3
        dump('amagic // 3', result)
        assert ~result == xdata

        xdata = [3 // a for a in self.ADATA]
        result = 3 // amagic
        dump('3 // amagic', result)
        assert ~result == xdata

        xdata = [a ** b for a, b in self.ZIPPED]
        result = amagic ** bmagic
        dump('amagic ** bmagic', result)
        assert ~result == xdata
        result = amagic ** self.BDATA
        dump('amagic ** self.BDATA', result)
        assert ~result == xdata

        xdata = [a ** 2 for a in self.ADATA]
        result = amagic ** 2
        dump('amagic ** 2', result)
        assert ~result == xdata

        xdata = [2 ** a for a in self.ADATA]
        result = 2 ** amagic
        dump('2 ** amagic', result)
        assert ~result == xdata

    def test_math_compare(self):
        amagic = DataHammer(self.ADATA)
        bmagic = DataHammer(self.BDATA)
        dump('amagic', amagic, 'bmagic', bmagic)

        xdata = [a > b for a, b in self.ZIPPED]
        result = amagic > bmagic
        dump('amagic > bmagic', result)
        assert ~result == xdata
        result = amagic > self.BDATA
        dump('amagic > self.BDATA', result)
        assert ~result == xdata

        xdata = [a > 3 for a in self.ADATA]
        result = amagic > 3
        dump('amagic > 3', result)
        assert ~result == xdata

        xdata = [3 > a for a in self.ADATA]
        result = 3 > amagic
        dump('3 > amagic', result)
        assert ~result == xdata

        xdata = [a >= b for a, b in self.ZIPPED]
        result = amagic >= bmagic
        dump('amagic >= bmagic', result)
        assert ~result == xdata
        result = amagic >= self.BDATA
        dump('amagic >= self.BDATA', result)
        assert ~result == xdata

        xdata = [a >= 3 for a in self.ADATA]
        result = amagic >= 3
        dump('amagic >= 3', result)
        assert ~result >= xdata

        xdata = [3 >= a for a in self.ADATA]
        result = 3 >= amagic
        dump('3 >= amagic', result)
        assert ~result >= xdata

        xdata = [a == b for a, b in self.ZIPPED]
        result = amagic == bmagic
        dump('amagic == bmagic', result)
        assert ~result == xdata
        result = amagic == self.BDATA
        dump('amagic == self.BDATA', result)
        assert ~result == xdata

        xdata = [a == 3 for a in self.ADATA]
        result = amagic == 3
        dump('amagic == 3', result)
        assert ~result == xdata

        xdata = [3 == a for a in self.ADATA]
        result = 3 == amagic
        dump('3 == amagic', result)
        assert ~result == xdata

        xdata = [a != b for a, b in self.ZIPPED]
        result = amagic != bmagic
        dump('amagic != bmagic', result)
        assert ~result == xdata
        result = amagic != self.BDATA
        dump('amagic != self.BDATA', result)
        assert ~result == xdata

        xdata = [a == 3 for a in self.ADATA]
        result = amagic == 3
        dump('amagic == 3', result)
        assert ~result == xdata

        xdata = [3 == a for a in self.ADATA]
        result = 3 == amagic
        dump('3 == amagic', result)
        assert ~result == xdata

        xdata = [a <= b for a, b in self.ZIPPED]
        result = amagic <= bmagic
        dump('amagic <= bmagic', result)
        assert ~result == xdata
        result = amagic <= self.BDATA
        dump('amagic <= self.BDATA', result)
        assert ~result == xdata

        xdata = [a <= 3 for a in self.ADATA]
        result = amagic <= 3
        dump('amagic <= 3', result)
        assert ~result == xdata

        xdata = [3 <= a for a in self.ADATA]
        result = 3 <= amagic
        dump('3 <= amagic', result)
        assert ~result == xdata

        xdata = [a < b for a, b in self.ZIPPED]
        result = amagic < bmagic
        dump('amagic < bmagic', result)
        assert ~result == xdata
        result = amagic < self.BDATA
        dump('amagic < self.BDATA', result)
        assert ~result == xdata

        xdata = [a < 3 for a in self.ADATA]
        result = amagic < 3
        dump('amagic < 3', result)
        assert ~result == xdata

        xdata = [3 < a for a in self.ADATA]
        result = 3 < amagic
        dump('3 < amagic', result)
        assert ~result == xdata

    def test_hash(self):
        amagic = DataHammer(self.ADATA)
        bmagic = DataHammer(self.BDATA)
        assert hash(tuple(self.ADATA)) == hash(amagic)
        assert hash(tuple(self.BDATA)) == hash(bmagic)

        for tag, data in (('list', [[1, 2], [3, 4]]), ('dict', dict(a=100)),
                          ('set', {1, 2, 3})):
            with pytest.raises(TypeError) as raised:
                magic = DataHammer(data)
                hash(magic)
            errmsg = "unhashable type: '%s'" % tag
            assert errmsg in str(raised.value).lower()

    def test_format(self):

        def fmt(data, **kwds):
            kwds.update(dict(sort_keys=True, separators=(',', ':')))
            if isinstance(data, list):
                nl = ',' + kwds.pop('nl', '')
                return "[%s]" % nl.join(json.dumps(e, **kwds) for e in data)
            return json.dumps(data, **kwds)

        # Test for no "[]" around a nested item:
        data = dict(bar='FOO', ack=True, foo='BAR', ary=[10, 20, 30])
        magic = DataHammer(data)
        dump('magic', magic)

        def handle(fmtstr, expect):
            result = fmtstr.format(magic)
            if result == expect:
                return
            logging.info("=== FORMAT '%s' of %s", fmtstr, data)
            logging.info("=== Expect<%s>(%s): >>\n%s\n<<=========",
                         tname(expect), hash(expect), expect.replace('\n', '\\n'))
            logging.info("=== Result<%s>(%s): >>\n%s\n<<=========",
                         tname(result), hash(result), result.replace('\n', '\\n'))
            assert result == expect

        handle("{}", fmt(data))
        handle("{:j}", fmt(data))
        handle("{:2j}", fmt(data, indent=2))
        handle("{:-2j}", fmt(data, indent=2))

        data = [1.25, dict(b='foo', a=1), dict(foo='bar', bar=[1, 2, 3]), -42]
        magic = DataHammer(data)
        dump('magic', magic)

        formats = {
            '{:-3j}': fmt(data, indent=3, nl='\n'),
            '{:-0j}': fmt(data, indent=0, nl='\n'),
            '{:3j}': fmt(data, indent=3),
            '{:0j}': fmt(data, indent=0),
            '{:j}': fmt(data),
            '{}': fmt(data),
        }
        for fmtstr, expect in formats.items():
            handle(fmtstr, expect)

        # Ensure we can dump *SOME* 'non serializable' types.
        data = Obj(a=1, b=[[[1, 2]]], c=lrange(5), d=Dictless(a=10, b=[1, 2]),
                   e=datetime.datetime(2017, 12, 26, 12, 30, 0))
        magic = DataHammer(data)
        text = ('{"a": 1, "b": [[[1, 2]]], "c": [0, 1, 2, 3, 4], "d": ' +
                '[10, [1, 2]], "e": "datetime.datetime(2017, 12, 26, 12, 30)"}')
        print(magic)
        assert text == str(magic)

    def test_empty_list(self):
        # Make sure that we don't throw when there is no data.
        empty = DataHammer([])

        assert 0 == len(empty)
        assert 0 == sum(empty)

        assert [] == ~empty
        assert [] == ~reversed(empty)
        assert [] == ~(empty.foo.bar)
        assert [] == ~-empty
        assert [] == ~(empty | True)
        assert [] == ~(empty | False)
        assert [] == ~(empty + 42)
        assert [] == ~(empty - 10)
        assert [] == ~(empty / 200)
        assert [] == ~(empty * 15)

        def boing(a, b):
            raise Exception("Should not be called")
        assert [] == ~(empty._apply(boing, 'foo', bar='FOO'))

        assert (None in empty) is False
        assert [] == ~(empty._contains(None))

        assert [] == ~empty._int()
        assert [] == ~empty._float()
        if six.PY2:
            assert [] == ~empty._long()

        bmagic = DataHammer(self.BDATA)
        assert [] == ~(empty * bmagic)
        assert [] == ~(empty * self.BDATA)
        assert [] == ~(empty * 3)
        assert [] == ~(3 * empty)
        assert [] == ~(empty / bmagic)
        assert [] == ~(empty / self.BDATA)
        assert [] == ~(empty / 3)
        assert [] == ~(3 / empty)
        assert [] == ~(empty + bmagic)
        assert [] == ~(empty + self.BDATA)
        assert [] == ~(empty + 3)
        assert [] == ~(3 + empty)
        assert [] == ~(empty - bmagic)
        assert [] == ~(empty - self.BDATA)
        assert [] == ~(empty - 3)
        assert [] == ~(3 - empty)
        assert [] == ~(empty // bmagic)
        assert [] == ~(empty // self.BDATA)
        assert [] == ~(empty // 3)
        assert [] == ~(3 // empty)
        assert [] == ~(empty ** bmagic)
        assert [] == ~(empty ** self.BDATA)
        assert [] == ~(empty ** 2)
        assert [] == ~(2 ** empty)
        assert [] == ~(empty > bmagic)
        assert [] == ~(empty > self.BDATA)
        assert [] == ~(empty > 3)
        assert [] == ~(3 > empty)
        assert [] == ~(empty >= bmagic)
        assert [] == ~(empty >= self.BDATA)
        assert [] == ~(empty >= 3)
        assert [] == ~(3 >= empty)
        assert [] == ~(empty == bmagic)
        assert [] == ~(empty == self.BDATA)
        assert [] == ~(empty == 3)
        assert [] == ~(3 == empty)
        assert [] == ~(empty != bmagic)
        assert [] == ~(empty != self.BDATA)
        assert [] == ~(empty == 3)
        assert [] == ~(3 == empty)
        assert [] == ~(empty <= bmagic)
        assert [] == ~(empty <= self.BDATA)
        assert [] == ~(empty <= 3)
        assert [] == ~(3 <= empty)
        assert [] == ~(empty < bmagic)
        assert [] == ~(empty < self.BDATA)
        assert [] == ~(empty < 3)
        assert [] == ~(3 < empty)

        assert hash(tuple()) == hash(empty)

    def test_indexing(self):
        data = lrange(10, 20)
        magic = DataHammer(data)

        for index, expect in (((1, 10, 4, 20, 2), [11, 14, 12]),
                              ((False, True, False, False, True), [11, 14]),
                              (([True] * 20), data),
                              (1, data[1]),
                              (slice(None, 4), data[:4]),
                              (slice(3), data[:3]),
                              (slice(1, 5), data[1:5]),
                              (slice(1, 7, 2), data[1:7:2])):
            deref = not isinstance(index, (slice, int))
            result = magic[index]
            dump('Expect', expect, 'Result1', result, 'Sliced', deref)
            assert expect == (~result if deref else result)

            if deref:
                other = DataHammer(index)
                result = magic[other]
                dump('Result2', result)
                assert expect == ~result

        for index in ("FOO", ["foo"], {1, 3}, (1, False), object()):
            with pytest.raises(TypeError) as raised:
                magic[index]
            dump('Raised', raised.value)
            assert 'Invalid index type' in str(raised.value)

    def test_single_item(self):
        # Make sure that we don't throw when there is no data.
        data = 12345
        magic = DataHammer(data)

        assert data == ~(magic | True)
        assert data == ~(magic | False)
        assert True == ~(True | magic)
        assert data == ~(False | magic)
        assert 1 == len(magic)

        assert data == ~magic
        assert data == ~reversed(magic)
        assert False == ~-magic
        assert data + 42 == ~(magic + 42)
        assert data - 10 == ~(magic - 10)
        assert data / 17 == ~(magic / 17)
        assert data * 15 == ~(magic * 15)

        def boing(*a, **k):
            raise Exception("Should not be called")

        with pytest.raises(Exception):
            magic._apply(boing, 'foo', bar='FOO')

        assert (None in magic) is False
        assert True == (data in magic)

        classes = {'_int': int, '_float': float, '_bool': bool}
        if six.PY2:
            classes['_long'] = long

        for name, cls in classes.items():
            expect = cls(data)
            result = eval('magic.%s()' % name)
            dump(name, result)
            assert expect == ~result

        dump('foobar', magic.foo.bar)
        assert ~magic.foo.bar is None

        first = 13
        ldata = [first, 20, 99]
        longer = DataHammer(ldata)
        assert (first * data) == ~(magic * longer)
        assert (first * data) == ~(magic * ldata)
        assert (data * 3) == ~(magic * 3)
        assert (data * 3) == ~(3 * magic)
        assert (data / first) == ~(magic / longer)
        assert (data / first) == ~(magic / ldata)
        assert (data / 3) == ~(magic / 3)
        assert (3 / data) == ~(3 / magic)
        assert (data + first) == ~(magic + longer)
        assert (data + first) == ~(magic + ldata)
        assert (data + 3) == ~(magic + 3)
        assert (3 + data) == ~(3 + magic)
        assert (data - first) == ~(magic - longer)
        assert (data - first) == ~(magic - ldata)
        assert (data - 3) == ~(magic - 3)
        assert (3 - data) == ~(3 - magic)
        assert (data // first) == ~(magic // longer)
        assert (data // first) == ~(magic // ldata)
        assert (data // 3) == ~(magic // 3)
        assert (3 // data) == ~(3 // magic)
        assert (data ** first) == ~(magic ** longer)
        assert (data ** first) == ~(magic ** ldata)
        assert (data ** 2) == ~(magic ** 2)
        assert (2 ** data) == ~(2 ** magic)
        assert (data > first) == ~(magic > longer)
        assert (data > first) == ~(magic > ldata)
        assert (data > 3) == ~(magic > 3)
        assert (3 > data) == ~(3 > magic)
        assert (data >= first) == ~(magic >= longer)
        assert (data >= first) == ~(magic >= ldata)
        assert (data >= 3) == ~(magic >= 3)
        assert (3 >= data) == ~(3 >= magic)
        assert (data == first) == ~(magic == longer)
        assert (data == first) == ~(magic == ldata)
        assert (data == 3) == ~(magic == 3)
        assert (3 == data) == ~(3 == magic)
        assert (data != first) == ~(magic != longer)
        assert (data != first) == ~(magic != ldata)
        assert (data == 3) == ~(magic == 3)
        assert (3 == data) == ~(3 == magic)
        assert (data <= first) == ~(magic <= longer)
        assert (data <= first) == ~(magic <= ldata)
        assert (data <= 3) == ~(magic <= 3)
        assert (3 <= data) == ~(3 <= magic)
        assert (data < first) == ~(magic < longer)
        assert (data < first) == ~(magic < ldata)
        assert (data < 3) == ~(magic < 3)
        assert (3 < data) == ~(3 < magic)

        assert hash((data, )) == hash(magic)

    def test_pick1(self):
        dd = lrange(-3, 8)
        dh = DataHammer(dd)
        knils = [dict(k1=None, k2=None, k3=None) for i in dd]
        assert knils == ~dh._pick('k1', 'x.y.k2', k3='foo.bar')

    def test_pick2(self):
        # Only take the 'meta'...
        dh = DataHammer(open_file('jobsdata.json'), json=True).meta
        exp = {
            "Contact Email": "opendata@its.ny.gov", "Publisher": "State of New York",
            "Contact Name": "Open Data NY"
        }
        res = dh.metadata.custom_fields._ind('Common Core')
        assert ~res == exp

        exp = dict(id='pxa9-czw8', tags=['job trends'], viewCount=44813,
                   screenName='NY Open Data', col=276163358, foo=None, bar=None)
        res = dh._pick('id', 'tags', 'viewCount', 'tableAuthor.screenName',
                       col='query.orderBys.0.expression.columnId',
                       foo='query.orderBys.200.foo', bar='query.bar.200.bar')
        assert [exp] == ~res

        # Validate that index integers used as keys are str.
        res = dh._pick('query.orderBys.0')
        print("Res: %s" % ~res)
        print("Res: %s" % ~dh)
        assert ["0"] == list(res[0].keys())

    def test_toCSV(self):
        dh = DataHammer(self.PEEP_DATA)
        expect = (
            "\"last\",\"first\",\"nick\",\"age\",\"where\"",
            "\"O'herlihan\",\"Rex\",\"The Singing Cowboy\",28,\"The Range\"",
            "\"Frog\",\"Kermit \\\"the\\\"\",,75,\"The Swamp\"",
            "\"Scully\",\"Dana\",\"Starbuck\",25,\"Parts unknown\""
        )

        # Is there a guarantee that the order is preserved?
        csv = dh._toCSV('name.last', 'name.first', nick='name.common',
                        age='age', where='office.location')
        print("CSV = " + csv[2])
        print("expect = " + expect[2])
        for nth, row in enumerate(csv):
            print("%d: %s" % (nth, row))
            print("   " + expect[nth])
        for n in range(len(expect)):
            print("Row %d:\n  <<<%s>>>\n  <<<%s>>>" % (n, expect[n], csv[n]))
        assert expect == csv

    def test_tuples(self):
        names = ('name.last', 'name.first', 'name.common', 'age', 'office.location')
        dh = DataHammer(self.PEEP_DATA)
        expect = tuple(
            (e['name']['last'], e['name']['first'], e['name']['common'],
             e['age'], e['office']['location'])
            for e in self.PEEP_DATA)
        out = dh._tuples(*names)
        assert expect == out

    def test_flatten1(self):
        # Start with deterministic data...
        inputs = ["text", 5, True, False, None, -123.456, object(), Obj(a=123, b="bee")]
        expect = list(inputs)

        def add(data, flat):
            inputs.append(data)
            expect.extend(flat)

        for group in ("aa bb cc".split(), ("other", 12, False, None, True, 0.0)):
            add(group, group)

        dh = DataHammer(inputs)
        result = dh._flatten()
        assert expect == ~result

        # Append non-deterministic types (set, dict).
        l0 = len(expect)

        dd1 = {"dog", "elk", "fox", "gopher"}
        expect.extend(dd1)
        l1 = len(expect)

        dd2 = {"a": "apple", "b": "bug", "c": "crayon"}
        expect.extend(dd2.values())
        l2 = len(expect)

        inputs.extend((dd1, dd2))
        dh = DataHammer(inputs)
        result = ~dh._flatten()

        # Compare by sections, including order
        sl0 = slice(l0)
        sl1 = slice(l0, l1)
        sl2 = slice(l0 + l1, l2)

        assert expect[sl0] == result[sl0]
        assert sorted(expect[sl1]) == sorted(result[sl1])
        assert sorted(expect[sl2]) == sorted(result[sl2])

    def test_flatten2(self):
        rng = random.Random()

        def num():
            return rng.randint(0, 5000)

        def flatten(obj):
            return [item for row in obj for item in (row if isinstance(row, list) else [row])]

        # 2 lists of 3 lists of 4 lists of 5 numbers
        data = [[[list(reversed([num() for a in range(5)]))
                  for b in range(4)] for c in range(3)] for d in range(2)]

        # Loop through, even past the depth (hence a no-op).
        dh = DataHammer(data)
        expect = data
        for loop in range(1, 6):
            print("Loop #%d: %s" % (loop, expect))
            expect = flatten(expect)
            dh = dh._flatten()
            assert expect == ~dh

    def test_groupby1(self):
        with open_file('people.json.gz', gz=True) as fd:
            data = json.load(fd)

        dh = DataHammer(data)
        ag = dh._groupby(('age', 'name.last'),
                         ('salary', 'location.state'))
        print("groupby 1: {:-0j}\n".format(ag))

        with open_file('people-ag1.json.gz', gz=True) as fd:
            expect = json.load(fd)
        assert expect == ~ag

    def test_groupby2(self):
        with open_file('people.json.gz', gz=True) as fd:
            data = json.load(fd)
        dh = DataHammer(data)

        # Argument order matches that specifed to _groupby() as the 'value' names.
        def reductor(salary, state):
            return mean(salary), dict(collections.Counter(state))

        ag = dh._groupby(('age', 'name.last'),
                         ('salary', 'location.state'),
                         combine=reductor)
        print("groupby 2: {:-0j}\n".format(ag))

        with open_file('people-ag2.json.gz', gz=True) as fd:
            expect = json.load(fd)
        assert expect == ~ag

    def test_array_mods(self):
        dd = lrange(-3, 8)
        mm = DataHammer(dd)

        dd.insert(1, 5)
        mm = mm._insert(1, 5)
        assert dd == ~mm

        dd.insert(5, 8)
        mm = mm._insert(5, 8)
        assert dd == ~mm

        dd = dd[:4] + [12, 13] + dd[6:]
        mm = mm._splice(4, 2, 12, 13)
        assert dd == ~mm

        dd = dd[:4] + dd[5:]
        mm = mm._splice(4, 1)
        assert dd == ~mm

        dd = dd[:4] + dd[5:]
        mm = mm._splice(4, 1)
        assert dd == ~mm

        dd.extend([30, 1, 5, 2])
        mm = mm._extend([30, 1, 5, 2])
        assert dd == ~mm

        def check(dd, ind, *params):
            d1 = eval('dd[%s]' % ind)
            m1 = mm._slice(*params)
            assert d1 == ~m1

        check(dd, '::2', None, None, 2)
        check(dd, '1:', 1)
        check(dd, '3:99', 3, 99)
        check(dd, '3:12:1', 3, 12, 1)

        # Cannot use nested items:
        with pytest.raises(AttributeError):
            DataHammer(dict(a=5, b=12))._slice(0)
        with pytest.raises(AttributeError):
            DataHammer(dict(a=5, b=12))._insert(0, {})

    def test_mutator_dict(self):
        magic = DataHammer(self.JOBS_DATA)

        mut = magic._mutate()
        assert isinstance(mut, DataHammer.Mutator)
        mut = magic._mutate().three
        assert isinstance(mut, DataHammer.Mutator)

        def check(tag, base, left, right):
            dump('base', base, tag + '.left', left, tag + '.right', right)
            assert (~left) == (~right)

        magic = DataHammer(self.JOBS_DATA)
        mod = magic.three + 30
        magic._mutate().three += 30
        check('iadd', magic, magic.three, mod)

        magic = DataHammer(self.JOBS_DATA)
        mod = magic.three - 7.5
        magic._mutate().three -= 7.5
        check('isub', magic, magic.three, mod)

        magic = DataHammer(self.JOBS_DATA)
        mod = magic.three * 1.5
        magic._mutate().three *= 1.5
        check('imul', magic, magic.three, mod)

        magic = DataHammer(self.JOBS_DATA)
        mod = magic.three / 1.25
        magic._mutate().three /= 1.25
        check('idiv', magic, magic.three, mod)

        magic = DataHammer(self.JOBS_DATA)
        mod = magic.three ** 3.5
        magic._mutate().three **= 3.5
        check('ipow', magic, magic.three, mod)

        magic = DataHammer(self.JOBS_DATA)
        mod = magic.three // 12.25
        magic._mutate().three //= 12.25
        check('ifloor', magic, magic.three, mod)

        magic = DataHammer(self.JOBS_DATA)
        mod = magic.three % 100
        magic._mutate().three %= 100
        check('imod', magic, magic.three, mod)

    def test_mutator_index(self):
        index = (3, 5, 7)
        data = [dict(a=i + 5, b=lrange(i*3, i*5), c=[dict(x=j) for j in (2, 4, 6)])
                for i in index]
        nada = [None for e in index]
        dump('data', data)
        magic = DataHammer(data)

        for e in data:
            e['b'][2] += 3
        magic._mutate().b._ind(2)._ += 3
        assert data == ~magic

        for e in data:
            e['c'][1]['x'] *= 1.5

        magic._mutate().c._ind(1).x *= 1.5
        assert data == ~magic

        # Suppress dereferencing errors:
        xout = magic._no_such_attr
        assert ~xout == nada

        mtwo = DataHammer([lrange(1, i) for i in index])
        xout = mtwo._ind(200)
        assert ~xout == nada

        xout = mtwo._foo
        assert ~xout == nada

    def test_mutator_set(self):
        orig = [dict(c=[Obj(x=i), Obj(y=i * 2)], k=Obj(a=i, b=i * 2), num=i)
                for i in range(11, 19)]
        data = copy.deepcopy(orig)

        magic = DataHammer(data)
        dump('1>>data', data, '1>>orig', orig, '1>>magic', ~magic)
        for e in data:
            e['c'][0].x = 1.25
            e['num'] = 50
        magic._mutate().c[0].x._set(1.25)
        mod = magic._mutate().num._set(50)
        dump('2>>data', data, '2>>orig', orig, '2>>magic', ~magic)
        assert ~mod == ~magic
        assert data == ~magic

        # Iterators
        values = [1, 3, 5]
        for e, val in zip(data, values * 3):
            e['num'] = val
        magic._mutate().num._set(values)
        dump('2>>data', data, '2>>orig', orig, '2>>magic', ~magic)
        assert data == ~magic

        # With '_set()' the object attribute/member does not need to already exist.
        keys = lrange(11, 19)
        data = [dict(k=Obj(a=i, b=i * 2, z=dict(i=i, x2=(i * 2), sqr=(i * i))),
                     c=[Obj(x=i), Obj(y=i * 2)]) for i in keys]
        magic = DataHammer(copy.deepcopy(data))

        # Set a 'new' attribute to a short list
        values = lrange(1, 6)
        for n, value in enumerate(values):
            data[n]['c'][0].new = value
        for item in data:
            item['k'].z['extra'] = 1234
        magic._mutate().c[0].new._set(values)
        magic._mutate().k.z.extra._set(1234)
        assert data == ~magic

        # Using "_set(list)" iterates over the list, but "_setall(list)" does not.
        val1 = [1, None, "text"]
        val2 = [2, "other"]
        for item in data:
            item['k'].new1 = list(val1)
        for nth, item in enumerate(val2):
            data[nth]['k'].new2 = item

        magic._mutate().k.new1._setall(val1)
        magic._mutate().k.new2._set(val2)
        for num, item in enumerate(~magic):
            dump(('item.%d' % num), item, ('data.%d' % num), data[num])
        assert data == ~magic

    def test_mutator_attr(self):
        orig = [dict(c=[Obj(x=i), Obj(y=i * 2)], k=Obj(a=i, b=lrange(i*3)))
                for i in (3, 5, 7)]

        data = copy.deepcopy(orig)

        magic = DataHammer(orig)
        dump('data', data, 'magic', ~magic)

        for e in data:
            e['c'][0].x /= 1.25
        magic._mutate().c[0].x /= 1.25
        assert data == ~magic
        dump('orig', orig, 'data', data, 'magic', ~magic)

        # Use class directly, too:
        DataHammer.Mutator(magic).k.a *= 1.5
        for e in data:
            e['k'].a *= 1.5
            e['c'][0].x += 8

        mod = DataHammer.Mutator(magic).c[0]._attr('x')
        assert str(mod) == "[Mutator([(0, 'c'), (1, 0), (0, 'x')])]"
        assert ~mod == ~magic
        mod += 8
        assert data == ~magic
        assert magic == mod
        dump('orig', orig, 'data', data, 'magic', ~magic)

        # index/key/attr off of an attr.
        for e in data:
            e['k'].b[0] += 8
        magic._mutate().k.b[0]._ += 8
        assert data == ~magic
        dump('orig', orig, 'data', data, 'magic', ~magic)

        # Lots of quiet failures, none of which mutate the data.
        magic._mutate().c[12]._ += 5
        magic._mutate().foo /= 5
        magic._mutate().c['12']._ -= 12
        magic._mutate().c._ind('foo')._ *= 5
        magic._mutate()._ind('foo')._ *= 5
        magic._mutate()['foo']._ *= 5
        magic._mutate()._ind(0)._ *= 5

        assert data == ~magic

    def test_mutator_reuse(self):
        data = [dict(c=[Obj(x=i), Obj(y=i * 2)],
                     k=Obj(a=i, b=i * 2)) for i in (3, 5, 7)]
        dump('data', data)
        magic = DataHammer(data)

        mod = magic._mutate()
        assert str(mod) == "[Mutator([])]"
        mod = mod.c
        assert str(mod) == "[Mutator([(0, 'c')])]"
        mod = mod.x
        assert str(mod) == "[Mutator([(0, 'c'), (0, 'x')])]"

        mod2 = mod._ind(100)
        # This fails currently, known bug...
        assert str(mod2) == "[Mutator([(0, 'c'), (0, 'x'), (1, 100)])]"
        assert str(mod) == "[Mutator([(0, 'c'), (0, 'x')])]"

    def test_mutator_apply(self):
        data = [dict(c=[Obj(x=i), Obj(y=i * 2)],
                     k=Obj(a=i, b=i * 2)) for i in (3, 5, 7)]
        dump('data', data)
        magic = DataHammer(data)

        def incr(obj, name, num=1):
            dump('OBJ', obj, 'num', num)
            setattr(obj, name, getattr(obj, name) + num)
            return obj

        magic._mutate().c[0]._apply(incr, 'x', num=2)
        magic._mutate().c[1]._apply(incr, 'y', num=5)
        dump('magic', magic, 'data', data)

        for item in data:
            item['c'][0].x += 2
            item['c'][1].y += 5

        assert data == ~magic
