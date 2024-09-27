#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
rexxbi - selected functions like those built-in in the REXX language

As far as possible, these functions behave the same as their REXX antetypes.
This includes characters (and words) in strings being *numbered* (starting with
1) rather than *indexed* (starting with 0).  The gain of this in a Python
context is the False boolean value of 0 (while -1 is True).

The following differences between Python and REXX make it impossible to have
perfectly identical function signatures:

* Rexx allows to omit certain arguments;
  Python supports keyword arguments instead
* Rexx ignores case when it comes to variables and (almost all) function names,
  which Python does not

As for this module, the functions expect real numbers where REXX would allow
strings which *look like* numbers, since everything is a string.  This aspect
could of course be handled differently by another module;  here no automagic
conversions are implemented for reasons of performance and simplicity.

Thus, don't expect this to suffice to build a Rexx interpreter;
however, some Rexx functions might be of some use:

>>> translate('ij.fg.abcd', '2012-12-31', 'abcdefghij')
'31.12.2012'

(look for the doctests, and try the commandline demo rexxbi_demo.py)
"""
# examples: <http://www.kyla.co.uk/other/rexx2.htm>,
#   <http://www.scoug.com/OPENHOUSE/REXXINTRO/RXBISTTR1.4.HTML>,
#   <http://www.kilowattsoftware.com/tutorial/rexx/bitranslate.htm>

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           4,	# integrated demo moved to -> rexxbi_demo.py
           8,	# d2x;  x2d, x2b incomplete (no width argument yet)
           'rev-%s' % '$Rev: 1102 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))
__all__ = [# general-use utilities:
           'left',
           'right',
           'center', 'centre',
           'pos',
           'substr', 'delstr',
           'translate',
           'verify',
           'compare',
           'copies',
           'overlay',
           # word functions:
           'word', 'words', 'wordpos',
           'wordindex',
           'wordlength',
           'subword', 'delword',
           # conversion functions:
           # (not complete yet)
           'd2x',
           # 'x2d',
           # 'x2b',
           # no part of Rexx, but needed e.g. for demo:
           'even', 'odd',
           # exceptions:
           'RexxError',
           'RexxArgumentError',
           ]

from thebops.misc1 import fillingzip
import string

try:
    _
except NameError:
    def _(s):
        return s

DEBUG = 0

# --------------------------------------------------[ exceptions ... [
class RexxError(Exception):
    def __str__(self):
        return self.msg

class RexxArgumentError(RexxError):
    def __init__(self, arg, fname):
        self.arg = arg
        self.fname = fname
        self.msg = None

    def _make_message(self):
	if self.msg is None:
            self.msg = ('invalid argument %(arg)r'
                        'to function %(fname)r'
                        ) % locals()

    def __str__(self):
	self._make_message()
	return self.msg

class RexxArgumentValueError(RexxArgumentError, ValueError):
    def __init__(self, fname, *args):
        self.args = args
        self.fname = fname
        self.msg = None

    def _make_message(self):
	if self.msg is None:
            self.msg = ('invalid argument %(arg)r'
                        'to function %(fname)r'
                        ) % locals()

class NegativeNumberRequiresWidth(RexxArgumentValueError):
    def __init__(self, fname, num):
	self.fname = fname
	self.num = num
	self.msg = None

    def _make_message(self):
	if self.msg is None:
	    self.msg = _('%s(%r) requires a width argument'
		         ) % (self.fname, self.num)

    def __str__(self):
	self._make_message()
	return self.msg

class WidthMustNotBeNegative(RexxArgumentValueError):
    def __init__(self, fname, width, *args):
	self.fname = fname
        self.width = width
        self.args = args
	self.msg = None

    def _make_message(self):
	if self.msg is None:
            self.msg = _('%s(%s): width must not be negative (%r)'
                         ) % (self.fname,
                              ', '.join(map(repr, self.args)),
                              self.width)


# --------------------------------------------------] ... exceptions ]

# ---------------------------------------[ general-use utilities ... [
def left(s, width, fillchar=' '):
    """
    like the Rexx built-in function LEFT:
    return the first <width> characters of the given string,
    filled up with <fillchar>

    >>> left('foo', 5)
    'foo  '
    >>> left('foo', 5, '*')
    'foo**'
    >>> left('foo', 1)
    'f'
    """
    assert width >= 0
    length = len(s)
    if length > width:
        return s[:width]
    else:
        return s.ljust(width, fillchar)

def right(s, width, fillchar=' '):
    """
    like the Rexx built-in function RIGHT:
    return the last <width> characters of the given string,
    filled up with <fillchar>

    >>> right('foo', 5)
    '  foo'
    >>> right('foo', 5, '*')
    '**foo'
    >>> right('foo', 2)
    'oo'
    """
    assert width >= 0
    if width == 0:
        return ''
    length = len(s)
    if length > width:
        return s[-width:]
    else:
        return s.rjust(width, fillchar)

def center(s, width, fillchar=' '):
    """
    like the Rexx built-in function CENTER (or CENTRE):
    return the middle <width> characters of the given string,
    filled up with <fillchar>.

    NOTE that for odd widths greater than the odd length of the
    given string, Rexx doesn't behave like Python's center method!

    >>> center('ham', 5, '-')
    '-ham-'
    >>> center('ham', 6, ' ')
    ' ham  '
    >>> center('abcde', 2)
    'bc'
    >>> centre('spam', 7)
    ' spam  '
    """
    assert width >= 0
    assert len(fillchar) == 1
    length = len(s)
    if length > width:
        head, rest = divmod(length-width, 2)
        return s[head:-(head+rest)]
    elif odd(width) and even(length):
        return s.center(width-1, fillchar) + fillchar
    else:
        return s.center(width, fillchar)
centre = center

def pos(s1, s2, startpos=1):
    """
    like the Rexx built-in function POS:

    find the string s1 in s2, starting at position <startpos> (default:
    1, i.e. search the whole string)

    >>> pos('a', 'abc')
    1
    >>> pos('a', 'abc', 2)
    0
    >>> pos('a', 'abca', 2)
    4
    """
    if startpos == 1:
        return s2.find(s1) + 1
    p = s2[startpos-1:].find(s1)
    if p == -1:
        return 0
    return p + startpos

def substr(s, start, width=None, fillchar=' '):
    """
    like the Rexx built-in function SUBSTR:

    >>> substr('abcde', 3)
    'cde'
    >>> substr('abcde', 3, 5)
    'cde  '
    >>> substr('abcde', 3, 5, '*')
    'cde**'
    >>> substr('abcde', 3, 0)
    ''
    """
    assert start >= 1
    if width is None:
        return s[start-1:]
    elif width == 0:
        return ''
    assert width > 0
    return left(s[start-1:], width, fillchar)

def delstr(s, start, width=None):
    """
    like the Rexx built-in function DELSTR:

    >>> delstr('abcde', 3)
    'ab'
    >>> delstr('abcde', 3, 1)
    'abde'
    >>> delstr('abcde', 3, 0)
    'abcde'
    """
    assert start >= 1
    start -= 1
    if width is None:
        return s[:start]
    elif width == 0:
        return s
    tmp = list(s)
    del tmp[start:start+width]
    return ''.join(tmp)

def translate(s, new=None, old=None, fillchar=None):
    """
    s -- a string (required)

    new -- a string (or sequence of characters)

    old -- like new

    fillchar -- used if old is longer than new

    This function serves two purposes:

    1) if only a string is given, returns s.upper()

    2) the more interesting form allows to "reorder" strings:
       each character in s, if contained in old, is replaced by the respective
       character in new.

    >>> translate('abc')
    'ABC'
    >>> translate('abcdef', '1', 'abcd')
    '1   ef'
    >>> translate('ij.fg.abcd', '2012-12-31', 'abcdefghij')
    '31.12.2012'
    """
    if (new, old, fillchar) == (None, None, None):
        return s.upper()
    if fillchar is None:
        fillarg = ''
        fillchar = ' '
    else:
        assert len(fillchar) == 1
    themap = {}
    if old is None:
        for ch in s:
            themap[ch] = fillchar
    else:
        for (val, key) in fillingzip(new or '', old or '', fillchar):
            themap[key] = val
    res = []
    for ch in s:
        try:
            res.append(themap[ch])
        except KeyError:
            res.append(ch)
    return ''.join(res)

def verify(s, ref, mode=0):
    """
    return the 1-based position in s which is *not* present in ref (nomatch
    mode, default), or which *is* present in s (match mode)

    s -- the inspected string

    ref -- the reference set of characters; in Rexx also given as a string

    mode -- 'nomatch' or 0 (default), or 'match' or 1; case is ignored

    Currently, there the following calling syntax differences to the Rexx
    version:
    - Rexx supports (case-insensitive) abbreviations of 'match' and 'nomatch'
      as well; this is not implemented (yet?)
    - instead, this function allows to use selected boolean values,
      where False means 'NOMATCH'

    >>> verify('abc', 'a')
    2
    >>> verify('abc', 'a', 'nomatch')
    2
    >>> verify('abc', 'a', 0)
    2
    >>> verify('abc', 'a', 'match')
    1
    >>> verify('abc', 'c', 1)
    3
    >>> verify('follow the white rabbit', 'abcdefhilortwxyz')
    7
    """
    if mode not in (0, 1, False, True):
        mode = match_arg(mode)
    nr = 1
    refset = set(ref)
    if mode:
        for ch in s:
            if ch in refset:
                return nr
            nr += 1
    else:
        for ch in s:
            if ch not in refset:
                return nr
            nr += 1
    return 0

def compare(s1, s2, pad=None):
    """
    >>> compare('abc', 'abc ')
    4
    >>> compare('abc', 'abc ', ' ')
    0
    >>> compare('abc', 'xyz')
    1
    >>> compare('abc', 'abc  e', ' ')
    6
    """
    pos = 1
    for (a, b) in zip(s1, s2):
        if a != b:
            return pos
        pos += 1
    if len(s1) == len(s2):
        return 0
    if pad is None:
        return pos
    for ch in s1[pos-1:] or s2[pos-1:]:
        if ch != pad:
            return pos
        pos += 1
    return 0

def copies(s, count):
    """
    >>> copies('abc', 0)
    ''
    >>> copies('ga', 2)
    'gaga'
    """
    assert isinstance(s, basestring)
    assert count >= 0
    return s * count

def overlay(s, target, start=1, count=None, fillchar=' '):
    """
    >>> overlay('a', 'bbb', 1)
    'abb'
    >>> overlay('a', 'bbb', 5)
    'bbb a'
    >>> overlay('a', 'bbb', 5, 2)
    'bbb a '
    >>> overlay('a', 'bbb', 2, 5)
    'ba    '
    >>> overlay('a', 'bbb', 5, 2, '-')
    'bbb-a-'
    >>> overlay('a', 'bbb', 2, 5, '-')
    'ba----'
    >>> overlay('', 'bbb', 5, None, '-')
    'bbb-'
    >>> overlay('', 'bbb', 5, 0, '-')
    'bbb-'
    """
    if count is None:
        count = len(s)
    else:
        assert count >= 0
        if count != len(s):
            s = left(s, count, fillchar)
    if len(target) < start + count - 1:
        target = left(target, start + count - 1, fillchar)
    liz = list(target)
    si = start - 1
    for ch in s:
        liz[si] = ch
        si += 1
    return ''.join(liz)

# ---------------------------------------] ... general-use utilities ]

# ---------------------------------------------[ no part of Rexx ... [
def odd(n):
    """
    >>> odd(2)
    False
    >>> odd(1)
    True
    """
    assert isinstance(n, int)
    return bool(n % 2)

def even(n):
    """
    >>> even(2)
    True
    >>> even(1)
    False
    """
    return not odd(n)
# ---------------------------------------------] ... no part of Rexx ]

# ----------------------------------------------[ word functions ... [
def word(s, pos):
    """
    >>> word('  ', 1)
    ''
    >>> word('   eins zwei  ', 2)
    'zwei'
    >>> word('eins.zwei', 2)
    ''
    >>> word('eins\tzwei', 2)
    'zwei'
    """
    assert pos > 0
    try:
        return s.split()[pos-1]
    except IndexError:
        return ''

def words(s):
    """
    Return the number of whitespace-divided words

    >>> words('  ')
    0
    >>> words('   eins zwei  ')
    2
    >>> words('eins.zwei')
    1
    >>> words('eins\tzwei')
    2
    """
    return len(s.split())

def wordpos(w, s):
    """
    Return the number of the given word in the given string

    >>> wordpos('zwei', '  ')
    0
    >>> wordpos('zwei', '   eins zwei  ')
    2
    >>> wordpos('zwei', 'eins.zwei')
    0
    >>> wordpos('zwei', 'eins\tzwei')
    2
    >>> wordpos('  follow  ', '  follow the white rabbit')
    1
    """
    try:
        return s.split().index(w.strip()) + 1
    except ValueError:
        return 0

def wordindex(s, nr):
    """
    Return the 1-based position of the 1st character of the nth word

    >>> wordindex('  ', 1)
    0
    >>> wordindex('   eins zwei  ', 1)
    4
    >>> wordindex('eins\tzwei', 2)
    6
    """
    pos = 0
    sofar = 0
    inword = 0
    for ch in s:
        pos += 1
        if ch in string.whitespace:
            if inword:
                inword = 0
        else:
            if not inword:
                sofar += 1
                if sofar == nr:
                    return pos
                inword = 1
    return 0

def subword(s, first, count=None):
    r"""
    Return max. count (or all remaining) subwords of the given string,
    beginning with word #<first>.

    The returned string ends with the end of the last contained
    word, with trailing whitespace stripped.

    >>> subword('follow the white rabbit', 1)
    'follow the white rabbit'
    >>> subword('follow the white rabbit', 1, 1)
    'follow'
    >>> subword('  follow the white rabbit  ', 3, 2)
    'white rabbit'
    >>> subword('  follow the white  rabbit', 3, 2)
    'white  rabbit'
    >>> subword('  ', 1)
    ''
    >>> subword('   eins   zwei  drei  ', 1, 2)
    'eins   zwei'
    >>> subword('   eins   zwei  drei  ', 1)
    'eins   zwei  drei'
    >>> subword('eins\tzwei', 1, 2)
    'eins\tzwei'
    >>> subword('eins\tzwei', 2)
    'zwei'
    >>> subword('eins\tzwei', 2, 1)
    'zwei'
    >>> subword('eins\tzwei', 3, 1)
    ''
    >>> subword('follow the white rabbit', 2, 1)
    'the'
    """
    assert isinstance(first, int)
    assert first >= 1
    sidx = (first - 1) * 2
    if count is not None:
        assert isinstance(count, int)
        if count == 0:
            return ''
        assert count > 0
        eidx = (first + count - 2) * 2 + 1
    else:
        eidx = None
    ii = 0
    indexes = _wordborders(s)
    for spos in indexes:
        if ii == sidx:
            if count is None:
                return s.rstrip()[spos:]
            else:
                ii += 1
                break
        ii += 1
    # too few words:
    if ii == 0:
        return ''
    for epos in indexes:
        if ii == eidx:
            return s[spos:epos]
        elawo = epos
        ii += 1
    return s.rstrip()[spos:]

'''
TODO: change subword() to use _wordbordertups() as well
(like delword() does)
subword() is *not* the exact complement to delword()!

def subword2(s, first, count=None):
    r"""
    Return max. count (or all remaining) subwords of the given string,
    beginning with word #<first>.

    The returned string ends with the end of the last contained
    word, with trailing whitespace stripped.

    >>> subword2('follow the white rabbit', 1)
    'follow the white rabbit'
    >>> subword2('follow the white rabbit', 1, 1)
    'follow'
    >>> subword2('  follow the white rabbit  ', 3, 2)
    'white rabbit'
    >>> subword2('  follow the white  rabbit', 3, 2)
    'white  rabbit'
    >>> subword2('  ', 1)
    ''
    >>> subword2('   eins   zwei  drei  ', 1, 2)
    'eins   zwei'
    >>> subword2('   eins   zwei  drei  ', 1)
    'eins   zwei  drei'
    >>> subword2('eins\tzwei', 1, 2)
    'eins\tzwei'
    >>> subword2('eins\tzwei', 2)
    'zwei'
    >>> subword2('eins\tzwei', 2, 1)
    'zwei'
    >>> subword2('eins\tzwei', 3, 1)
    ''
    >>> subword2('follow the white rabbit', 2, 1)
    'the'
    """
    assert isinstance(first, int)
    assert first >= 1
    # sidx - index of the index of the 1st character
    #        of the 'first'st word
    sidx =  None
    if count is not None:
        assert isinstance(count, int)
        if count == 0:
            return s
        assert count > 0
        firstofrest = first + count
    else:
        firstofrest = None
    p('subword2(%r, %d, %s)' % (s, first, count))
    pvars(locals(), 'sidx', 'firstofrest')
    ii = 1
    indextups = _wordbordertups(s)
    for (spos, epos) in indextups:
        pvars(locals(), 'spos', 'ii')
        if ii == first:
            if count is None:
                return s[spos:]
            else:
                sidx = spos
        elif spos is None:
            if sidx is not None:
                return s[sidx:prevspos]
            else:
                return s
        elif ii == firstofrest:
            if sidx:
                return s[sidx:prevspos]
            else:
                return s[:spos]
        ii += 1
        prevspos = spos
    return s
'''

def wordlength(s, nr):
    """
    Return the length of the word #<nr>, or 0

    >>> wordlength('The quick brown fox jumps', 1)
    3
    >>> wordlength('', 1)
    0
    >>> wordlength('Ottos Mops', 3)
    0
    """
    try:
        i = 1
        for tup in _wordbordertups(s):
            if i == nr:
                return tup[1] - tup[0]
            i += 1
        return 0
    except (IndexError, TypeError):
        return 0

def delword(s, first, count=None):
    """
    Return the given string with max. <count> words removed
    (or all remaining), beginning with subword #<first>;

    trailing whitespace is removed if the last word is removed;
    the space before the first deleted word is preserved.

    >>> delword('follow the white rabbit', 1)
    ''
    >>> delword('  follow   the white rabbit ', 2, 2)
    '  follow   rabbit '
    >>> delword('  follow   the white rabbit ', 2, 10)
    '  follow   '
    >>> delword('follow the white rabbit', 1, 4)
    ''
    >>> delword('follow the white rabbit', 1, 5)
    ''
    >>> delword('follow the white rabbit', 2)
    'follow '
    >>> delword('follow the white rabbit', 2, 3)
    'follow '
    >>> delword('follow the white rabbit', 2, 5)
    'follow '
    >>> delword('follow the white rabbit', 3)
    'follow the '
    >>> delword('follow the white rabbit', 3, 2)
    'follow the '
    >>> delword('follow the white rabbit ', 3, 2)
    'follow the '
    >>> delword('follow the white rabbit', 3, 5)
    'follow the '
    >>> delword('follow the white rabbit', 4)
    'follow the white '
    >>> delword('follow the white rabbit', 4, 1)
    'follow the white '
    >>> delword('follow the white rabbit', 4, 5)
    'follow the white '
    >>> delword('follow the white rabbit', 5)
    'follow the white rabbit'
    >>> delword('follow the white rabbit ', 5, 1)
    'follow the white rabbit '
    >>> delword('follow the white rabbit', 5, 1)
    'follow the white rabbit'
    >>> delword('follow the white rabbit ', 5, 5)
    'follow the white rabbit '
    """
    assert isinstance(first, int)
    assert first >= 1
    # sidx - index of the index of the 1st character
    #        of the 'first'st word
    sidx =  None
    if count is not None:
        assert isinstance(count, int)
        if count == 0:
            return s
        assert count > 0
        firstofrest = first + count
    else:
        firstofrest = None
    p('delword(%r, %d, %s)' % (s, first, count))
    pvars(locals(), 'sidx', 'firstofrest')
    ii = 1
    indextups = _wordbordertups(s)
    for (spos, epos) in indextups:
        pvars(locals(), 'spos', 'ii')
        if ii == first:
            if count is None:
                return s[:spos]
            else:
                sidx = spos
        elif spos is None:
            if sidx is not None:
                return s[:sidx]
            else:
                return s
        elif ii == firstofrest:
            if sidx:
                return s[:sidx] + s[spos:]
            else:
                return s[spos:]
        ii += 1
    return s
# ----------------------------------------------] ... word functions ]

# ----------------------------------------[ conversion functions ... [

def x2d(s):
    """
    Konvertiert eine beliebige vorzeichenlose Sedezimalzahl (ein String)

    >>> x2d('A')
    10
    """
    return int(s, 16)

def d2x(num, width=None):
    """
    Convert a integer number to a hex string.

    >>> d2x(10)
    'A'
    >>> d2x(10, 2)
    '0A'
    >>> d2x(1234, 2)
    'D2'

    For negative input, a (non-negative) width must be given:

    >>> d2x(-1, 2)
    'FF'
    """
    i = int(num)
    if width is None:
	if i < 0:
            raise NegativeNumberRequiresWidth('d2x', num)
	return '%X' % i
    if width == 0:
        return ''
    if width < 0:
        raise WidthMustNotBeNegative('d2x', width, num, width)
    if i < 0:
        j = 16 ** width
        a = abs(i)
        while j < a:
            j *= 16
        x = '%X' % (j - a)
        return x[-width:]
    
    res = '%0*X' % (width, i)
    if len(res) > width:
	return res[-width:]
    return res

def x2b(s):
    """
    convert a hex string to binary

    >>> x2b('A')
    '1010'
    >>> x2b('11')
    '00010001'
    """
    d = x2d(s)
    tmp = []
    while d:
        d, b = divmod(d, 2)
        tmp.append(b)
    tmp.extend([0]*_missing(len(tmp)))
    tmp.reverse()
    ch = '01'
    return ''.join([ch[b]
                    for b in tmp
                    ])

def _missing(num):
    """
    >>> _missing(11)
    1
    >>> _missing(0)
    4
    >>> _missing(2)
    2
    """
    if not num:
        return 4
    a = num % 4
    if a:
        return 4 - a
    return 0

# ----------------------------------------] ... conversion functions ]

# -----------------------------------------------------[ helpers ... [
def match_arg(s):
    """
    interpret Rexx-conforming 3rd arguments to verify
    and return 0 or 1

    ObjectRexx interprets 'mismatch' like 'match', which
    is counter-intuitive; thus, this value is disallowed!

    >>> match_arg('match')
    1
    >>> match_arg('M')
    1
    >>> match_arg('n')
    0
    >>> match_arg('nOma')
    0
    >>> match_arg('nnnn')
    0
    """
    assert isinstance(s, str)
    assert s, 'empty strings are not allowed'
    la = s.lower()
    longstrings = ('nomatch', 'match')
    for i in range(2):
        if longstrings[i].startswith(la):
            return i
    # sic! Getestet mit ooRexx_4.0.1(MT):
    for i in range(2):
        if la.startswith(longstrings[i][0]):
            return i
    raise RexxArgumentError(s, 'verify')

def _wordbordertups(s):
    """
    helper for subword and delword:
    yield a 2-tuple for each found word, and finally (None, None).

    >>> list(_wordbordertups(''))
    [(None, None)]
    >>> list(_wordbordertups('single'))
    [(0, 6), (None, None)]
    >>> list(_wordbordertups(' two words '))
    [(1, 4), (5, 10), (None, None)]
    >>> list(_wordbordertups('eins drei'))
    [(0, 4), (5, 9), (None, None)]
    """
    idx = 0
    def isblanc(ch):
        return ch in string.whitespace
    def noblanc(ch):
        return ch not in string.whitespace
    funcs = (noblanc, isblanc)
    funcidx = 0 # 1st search for non-blanks
    prev = 0
    si = None
    for ch in s:
        this = funcs[funcidx](ch)
        if this != prev:
            funcidx = not funcidx
            if si is None:
                si = idx
            else:
                yield (si, idx)
                si = None
        idx += 1
    if si is not None:
        yield (si, idx)
    yield (None, None)

def _wordborders(s):
    """
    helper for subword and delword;
    the number of yielded indexes is always even

    >>> list(_wordborders('single'))
    [0, 6]
    >>> list(_wordborders(' two words '))
    [1, 4, 5, 10]
    >>> list(_wordborders('eins\tzwei'))
    [0, 4, 5, 9]
    """
    if not s:
        return
    idx = 0
    def isblanc(ch):
        return ch in string.whitespace
    def noblanc(ch):
        return ch not in string.whitespace
    funcs = (noblanc, isblanc)
    funcidx = 0 # 1st search for non-blanks
    prev = 0
    for ch in s:
        this = funcs[funcidx](ch)
        if this != prev:
            funcidx = not funcidx
            yield idx
        idx += 1
    if funcidx:
        yield idx

def pvars(ns, *args):
    """
    ns -- namespace (e.g. 'locals()')
    args -- variable names (from ns)
    """
    if not DEBUG:
        return
    assert isinstance(ns, dict)
    liz = ['%s=%%(%s)r' % (item, item)
           for item in args]
    print ('; '.join(liz)) % ns

def p(s):
    if DEBUG: print(s)
# -----------------------------------------------------] ... helpers ]

if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=__version__)
