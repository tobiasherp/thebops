#!/usr/bin/python
"""
thebops.plustr2 - plural strings module 2
(not yet usable)

For simple cases, where it is sufficient to have
a singular form (for num == 1) and a plural form for all other numbers,
you can use the thebops.plustr1 module already.

This module is intended to be more universally usable, since the above logic
is not sufficient for all languages.
"""

VERSION = (0,
           0, # forked from thebops.plustr1 0.5.1
           1, #
           'rev-%s' % '$Rev: 972 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))
__all__ = ['freezeText',
	   'applyNumber',
           ]
__author__ = 'Tobias Herp <tobias.herp@gmx.de>'

class PluralStringsHub(dict):
    """
    Hold a function for every string thrown at it, which contains markers for
    singular/plural forms, which are a superset from those understood by the
    thebops.plustr1 module:

    '[one|0:no|%(num)d] file[s] or director[y|ies]'

    This string is first split like this:
    '[one|0:no|%(num)d]' contains versions for the numbers 1, 0, and all others
    ' file'              always used
    '[s]'                '' for 1, and 's' for all other numbers
    ' or director'       always used
    '[y|ies]'            without further specs, the 1st string is for 1, and
                         the 2nd one for all other numbers

    To make this efficient - for repeated usage, at least - this class
    implements a map of functions.  If the function which interprets the given
    string is not yet present, it is automatically created by a factory
    function; this way, each template must be interpreted only once.


    """

thehub = PluralStringsHub()

def make_gimme3(sing, plu, zero):
    """
    >>> func = make_gimme3('one', '%(num)d', 'no')
    >>> func(1)
    'one'
    >>> func(42)
    '%(num)d'
    >>> func(0)
    'no'
    """
    def gimme3(num):
	if num == 1:
	    return sing
	elif num == 0:
	    return zero
	else:
	    return plu
    return gimme3

def serve_three(s):
    """
    for simple cases: [sing|]plu[|zero]
    Return a 3-tuple of strings, representing the singular, plural and zero
    forms.

    >>> serve_three('[one|%(num)d|no]')
    ('one', '%(num)d', 'no')
    >>> serve_three('[s]')
    ('', 's', 's')
    >>> serve_three('[y|ies]')
    ('y', 'ies', 'ies')

    Currently, no escaping of | characters is supported.
    """
    assert s[0] == '['
    assert s[-1] == ']'
    stem = s[1:-1]
    assert '[' not in stem
    assert ']' not in stem
    assert ':' not in stem
    liz = stem.split('|')
    ll = len(liz)
    assert ll <= 3
    if ll == 1:	# plural only
	return ('', liz[0], liz[0])
    elif ll == 2:
	return (liz[0], liz[1], liz[1])
    else:
	return tuple(liz)


ESCAPE_CHAR = intern('\\')
SWITCH = tuple('[]')
def _gen_chunktuples(s):
    """
    generate tuples:

    >>> list(_gen_chunktuples('file[s]'))
    [(0, 'file'), (1, '[s]')]
    >>> list(_gen_chunktuples('file[s] or director[y|ies]'))
    [(0, 'file'), (1, '[s]'), (0, ' or director'), (1, '[y|ies]')]

    Escape character is the backslash
    """
    flag = 0
    escaped = False
    chunk = []
    for ch in s:
	if ch == SWITCH[flag] and not escaped:
	    if flag:
		chunk.append(ch)
		yield (flag, ''.join(chunk))
		del chunk[:]
		flag = 0
	    else:
		if chunk:
		    yield (flag, ''.join(chunk))
		    del chunk[:]
		chunk.append(ch)
		flag = 1
	elif escaped:
	    chunk.append(ch)
	    escaped = False
	elif ch == ESCAPE_CHAR:
	    escaped = True
	else:
	    chunk.append(ch)
    if flag:
	raise ValueError('Open ended plural forms string: %s (%s)'
		         % (''.join(chunk), s))
    if chunk:
	yield (flag, ''.join(chunk))

OPNAME = {
	'>':  'gt',
	'>=': 'ge',
	'=':  'eq',
	'<':  'lt',
	'<=': 'le',
	'!=': 'ne',
	}
OPCHARS = set()
# reverse mapping (e.g. 'eq' -> '='):
OPNAME_REVERSE = {}
for key, val in OPNAME.items():
    OPCHARS.update(set(key))
    OPNAME_REVERSE[val] = key
# 'eq' -> 'eq':
for val in OPNAME.values():
    OPNAME[val] = val
# alternate operators:
OPNAME.update({
	'<>': 'ne',
	'==': 'eq',
	})


def make_comparator(opname, reference):
    if opname == 'gt':
	def func(num):
	    return num > reference
    elif opname == 'ge':
	def func(num):
	    return num >= reference
    elif opname == 'lt':
	def func(num):
	    return num < reference
    elif opname == 'le':
	def func(num):
	    return num <= reference
    elif opname == 'eq':
	def func(num):
	    return num == reference
    elif opname == 'ne':
	def func(num):
	    return num != reference
    else:
	raise ValueError('Unsupported operator name: %r'
		         % (opname))
    func.__name__ = '%(opname)s_%(reference)d' % locals()
    return func


class ComparatorHub(dict):
    """
    Stores comparator functions, which are very likely used for more than one
    string; this way, each needed comparator is created only once.

    >>> hub = ComparatorHub()
    >>> func = hub[('eq', 1)]
    >>> func(1)
    True
    >>> func(2)
    False
    >>> func.__name__
    'eq_1'

    For operators and their names, only one function is created:

    >>> hub[('=', 1)] is hub[('eq', 1)]
    True
    """
    def __getitem__(self, key):
	assert isinstance(key, tuple)
	try:
	    return dict.__getitem__(self, key)
	except KeyError:
	    op, arg = key
	    opname = OPNAME[op]
	    opnames = [op]
	    if opname != op:
		if (opname, arg) in self:
		    func = self[(opname, arg)]
		    self.__setitem__(key, func)
		    return func
		opnames.append(opname)
	    func = make_comparator(opname, arg)
	    for op in opnames:
		self.__setitem__((op, arg), func)
	    return func

def freezeText(text, number):
    """
    In contrast to thebops.plustr1.freezeText, the 2nd argument is used as a
    number, not only a boolean; the recognized text patterns are a superset of
    those used by the former.

    Examples:

    >-> freezeText('file[s] or director[y|ies]', 1)
    'file or directory'
    >-> freezeText('file[s] or director[y|ies]', 2)
    'files or directories'
    >-> freezeText('[0:no ]file[s] or director[y|ies]', 0)
    'no files or directories'
    """
    return thehub[text](number)

def applyNumber(text, **kwargs):
    """
    >-> applyNumber('[one|%(num)d] file[s] or director[y|ies]', num=1)
    'one file or directory'
    >-> applyNumber('[one|%(num)d] file[s] or director[y|ies]', num=2)
    '2 files or directories'
    """
    assert len(kwargs) == 1
    return thehub[text](**kwargs)

DIGITS = frozenset('0123456789')
NEW_CHUNK = 0
MODE_OPERATOR = 1
MODE_NUMBER = 2
MODE_TEXT = 3

def string_and_None(s):
    """
    Little utility for parsers: Generate the characters of a string, and None.

    >>> list(string_and_None('abc'))
    ['a', 'b', 'c', None]
    """
    for ch in s:
	yield ch
    yield None


def _raw_pluralspecs(s):
    """
    >>> p = _raw_pluralspecs
    >>> list(p(''))
    []
    >>> list(p('y|ies'))
    [(((),), 'y'), (((),), 'ies')]
    >>> list(p('1:y|ies'))
    [((('=', 1),), 'y'), (((),), 'ies')]
    >>> list(p('=1:y|ies'))
    [((('=', 1),), 'y'), (((),), 'ies')]
    >>> list(p('0:Keine|%(num)d'))
    [((('=', 0),), 'Keine'), (((),), '%(num)d')]

    """
    chunk = []
    oplist = []
    digits = []
    mode = NEW_CHUNK
    if s == '=1:y|ies' and 0:
	import pdb
	pdb.set_trace()
    for ch in string_and_None(s):
	if mode == NEW_CHUNK:
	    assert not oplist
	    if ch in DIGITS:
		oplist = ['=']
		digits.append(ch)
		mode = MODE_NUMBER
	    elif ch in OPCHARS:
		oplist.append(ch)
		mode = MODE_OPERATOR
	    else:
		mode = MODE_TEXT
		if ch != ':':
		    chunk.append(ch)
	elif mode == MODE_OPERATOR:
	    assert oplist
	    if ch in OPCHARS:
		oplist.append(ch)
	    elif ch in DIGITS:
		digits.append(ch)
		mode = MODE_NUMBER
	    else:
		op = ''.join(oplist)
		raise ValueError('Number after operator %(op)r expected;'
		                 ' got %(ch)r (%s)' % locals())
	elif mode == MODE_NUMBER:
	    if ch in DIGITS:
		digits.append(ch)
	    elif ch == ':':
		mode = MODE_TEXT
	    elif ch == ',':
		raise ValueError('Sorry: multiple comparisons not yet '
			         'supported (%s)' % locals())
	    else:
		op = ''.join(oplist)
		num = ''.join(digits)
		raise ValueError('":" after operator %(op)s and number %(num)s'
			         'expected; got %(ch)r (%(s)s)'
				 % locals())
	else:
	    assert mode == MODE_TEXT
	    if ch in ('|', None):
		if digits:
		    assert oplist
		    op = ''.join(oplist)
		    if op not in OPNAME:
			raise ValueError('Operator %(op)r not supported (%(s)r'
					 % locals())
		    yield ((op, int(''.join(digits))
			    ),
			   ), ''.join(chunk)
		else:
		    assert not oplist
		    yield ((),
			   ), ''.join(chunk)
		if ch is None:
		    return
		mode = NEW_CHUNK
		del oplist[:]
		del digits[:]
		del chunk[:]
	    else:
		chunk.append(ch)
    return
    assert 0, 'The flow doesn\'t reach this point'
    if mode == NEW_CHUNK:
	assert not oplist
	assert not digits
	assert not chunk


SINGLE_FALLBACK_TEXT = ('If comparisons given at all, only one '
			'is allowed without one; found %(fallback_text)r '
			'and %(text)r (%(s)r)'
			)
def parse_pluralspecs(s):
    """
    >>> list(parse_pluralspecs('s'))
    [(None, 's')]
    >>> list(parse_pluralspecs('=1:y|ies'))
    [(('eq', 1), 'y'), (None, 'ies')]
    """
    raw = list(_raw_pluralspecs(s))
    res = []
    fallback_text = None
    rule2txt = {}
    for tup in raw:
	rules, text = tup
	if not rules:
	    if fallback_text is not None:
		raise ValueError(SINGLE_FALLBACK_TEXT % locals())
	    fallback_text = text
	    continue
	for tup in rules:
	    try:
		(rawop, num) = tup
	    except ValueError:
		if fallback_text is not None:
		    raise ValueError(SINGLE_FALLBACK_TEXT % locals())
		fallback_text = text
		continue
	    op = OPNAME[rawop]
	    key = (op, num)
	    if key in rule2txt:
		text1 = rule2txt[key]
		if text1 != text:
		    raise ValueError('Two diffent texts found for '
			    '%(rawop)s%(num)d: %(text)r != %(text1)r'
			    ' (%(s)s)'
			    % locals())
		continue
	    res.append((key, text))
    if fallback_text is not None:
	res.append((None, fallback_text))
    else:
	res.append((None, ''))
    return res


if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=VERSION)
