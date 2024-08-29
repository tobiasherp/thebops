#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
misc1: miscellaneous functions etc., collected here for lack of a better place.

Please don't rely on the functions and classes available here - not for too
long, at least.  The general policy is:
 
- New stuff might vanish without notice if part of an alpha or beta version
  of thebops *only*.
- New stuff will remain available here for at least two years (rounded to the
  next full year) or the next but one major version, whatever comes last:
  - something new as of thebops 0.1.16 won't be moved or deleted before
    thebops 0.3;
  - something new as of 2014-03-15 won't be moved or deleted before
    2017-01-01.

"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           2,   # make_valuesClass
           'rev-%s' % '$Revision: 1102 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

__all__ = ['extract_dict',      # thebops 0.1.16, 2014-03-15
           'make_valuesClass',  # thebops 0.1.16, 2014-03-15
           'fillingzip',        # thebops 0.1.16, 2014-03-15
           # 'named_date_tuple',
           ]

try:
    # available as of Python 2.6+
    from collections import namedtuple
except ImportError:
    namedtuple = None

try:
    # available as of Python 2.7+
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict

def fillingzip(s1, s2, fillchar):
    """
    assymmetrical zip function; if the 1st sequence is shorter than the 2nd, it
    is filled up with the fillchar.

    >>> list(fillingzip('abc', 'ABCDE', '*'))
    [('a', 'A'), ('b', 'B'), ('c', 'C'), ('*', 'D'), ('*', 'E')]
    >>> list(fillingzip('abcde', 'ABC', '*'))
    [('a', 'A'), ('b', 'B'), ('c', 'C')]
    """
    for tup in zip(s1, s2):
        yield tup
    if len(s1) < len(s2):
        for ch in s2[len(s1):]:
            yield (fillchar, ch)

def extract_dict(dic, keys, pop=True):
    """
    Return an excerpt of the given dict which contains the given keys

    dic -- the dictionary
    keys -- the sequence of keys
    pop -- if True (the default),
           the keys are removed from the original dictionary

    >>> dic = {'one': 1, 'two': 2}
    >>> extract_dict(dic, ('one', 'three'))
    {'one': 1}
    >>> dic
    {'two': 2}
    """
    if isinstance(keys, basestring):
        keys = (keys,)
    res = {}
    get = pop and dic.pop or dic.get
    for key in keys:
        if key in dic:
            res[key] = get(key)
    return res

def make_valuesClass(seq, default=None, classname=None):
    """
    Return a simple class which provides a limited set of named attributes
    which default to a given value (by default: None).

    >>> cls = make_valuesClass(('help', 'version'), classname='Mock')
    >>> o = cls()
    >>> str(o)
    'Mock(help=None, version=None)'
    >>> o.help = 1
    >>> str(o)
    'Mock(help=1, version=None)'
    >>> str(cls(version=1))
    'Mock(help=None, version=1)'
    """
    assert not isinstance(seq, basestring)
    # preserve the order, thus don't use a set: 
    nodupes = []
    for a in seq:
        if not a in nodupes:
            nodupes.append(a)

    SEQ = tuple(nodupes)
    class _Mock(object):
        """
        A simple Values class which supports a limited set of attributes
        """
        def __init__(self, **kwargs):
            """
            accept named arguments with names given
            when calling the factory method
            """
            for a in SEQ:
                setattr(self, a,
                        kwargs.pop(a, default))
            assert not kwargs

        def __str__(self):
            s = ['%s=%r' % (a, getattr(self, a))
                 for a in SEQ]
            return '%s(%s)' % (self.__class__.__name__, s)

    if classname:
        _Mock.__name__ = classname
    return _Mock

if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=VERSION)

