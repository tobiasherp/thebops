#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Shell tools

Utility functions for shell programs.
See as well -> anyos.py
for functions etc. which handle operating system differences
(but are not necessarily related to the shell),
and shtools_demo.py
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           6,	# FilenameGenerator, GlobFileGenerator, defaults_summary
           4,   # Rotors need sequences above 1 of length
           'rev-%s' % '$Rev: 1042 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))
# für Module:
__all__ = ['sleep', 'slept',
           'ask',
           'one_of',
           # filename generators:
           'FilenameGenerator',
           'GlobFileGenerator',
           # exception classes:
           'Error',
           'ToolsValueError',
           'ExplainedValueError',
           'InvalidRotorError',
           'InvalidCharacterPoolError',
           'NothingToReturn',   # -> FilenameGenerator(nospecs)
           'ToolsUsageError',
           'UnsupportedKeywordArguments', # also a TypeError
           # exceptions for one_of:
           'OptionCheckError',
           'OptionConflictError',
           'OptionMissingError',
           # e.g. for svn-style commandline interfaces:
           'CommandError',
           'CommandUnknownError',
           'CommandNotImplementedError',
           'NoCommandError',
           # raise only if enabled:
           'NotFound', # -> GlobFileGenerator(notfound=ERROR_IF_NOT_FOUND)
           'NothingFound', # -> ...(notfound=ERROR_IF_NOTHING_FOUND)
           # callable instances:
           'TempWriter',
           'Rotor',
           # GlobFileGenerator(notfound, ...):
           'SILENT',
           'RAISE_EXCEPTION',
           'YIELD_PATTERNS',
           'YIELD_PATTERN',
           'ERROR_IF_NOTHING_FOUND',
           'ERROR_IF_NOT_FOUND',
           # integer values -> names:
           'CONSTANTS_INFO',
           # other data:
           'DEFAULT_ROTOR',
           # default values handling 
           # (DEFAULT_... variables omitted intentionally):
           'defaults_summary',
           'set_default',
           #
           'mapfunc',
           'value_and_strings',
           'replaced_switches',
           'mapfunc_dict',
           # date calculations:
           'DateCalculator',
           'noon',
           'daystart',
           ]

from ConfigParser import ConfigParser
from time import time, sleep as _sleep, \
        localtime, mktime, struct_time
from sys import stderr
try:
    _
except NameError:
    def _(s): return s
import string
try:
    string
except NameError:
    raise Exception('string module must be imported as such '
            '(because of possible modifications of character classes '
            'by the locale module)')

class Error(Exception):
    """base exception class for this module"""

class OptionCheckError(Error):
    """
    an error while checking (mostly: commandline) options

    (well, this is the intended usage of the one_of function)
    """
    def __init__(self, names=None):
        if names is not None:
            assert isinstance(names, (list, tuple))
        self.names = names

    def __str__(self):
        cn = self.__class__.__name__
        info = self.names and ', '.join(self.names) or ''
        return (cn == 'OptionCheckError'
                and '%(cn)s(%(info)s) (please use a specialized class)'
                or  '%(cn)s(%(info)s) (__str__ method missing)'
                ) % locals()

class OptionConflictError(OptionCheckError):
    def __str__(self):
        return (self.names is None
                and 'Conflicting options'
                or  'Conflicting options: %s'
                    % ', '.join(self.names)
                )

class OptionMissingError(OptionCheckError):
    def __str__(self):
        return (self.names is None
                and 'None of required options chosen'
                or  'Choose one of: %s'
                    % ', '.join(self.names)
                )

class CommandError(Error):
    def __init__(self, cmd):
        self.cmd = cmd

class NoCommandError(CommandError):
    def __init__(self):
        pass

    def __str__(self):
        return _('no command given')

class CommandUnknownError(CommandError):
    def __str__(self):
        return _('command %r miss-spelled or unknown'
                 ) % self.cmd

class CommandNotImplementedError(CommandError):
    def __init__(self, cmd, alt=[]):
        CommandError.__init__(self, cmd)
        self.alt = alt

    def __str__(self):
        if self.alt:
            return _('command %s (%s) not implemented'
                     ) % (self.cmd,
                          ', '.join(self.alt))
        else:
            return _('command %r not implemented'
                     ) % self.cmd

class ToolsValueError(Error, ValueError):
    """
    Exceptions for single bogus values
    """
    msg_tmpl = 'Invalid value (%(value)r)'
    def __init__(self, value):
        self.value = value
    def _dict(self):
        """
        return a dictionary which contains all attributes whose names don't
        start with an underscore character
        """
        dic = dict()
        for n in dir(self):
            if not n.startswith('_'):
                dic[n] = getattr(self, n)
        return dic

    def __str__(self):
        return self.msg_tmpl % self._dict()

class ExplainedValueError(Error, ValueError):
    """
    ValueError with message template
    """
    def __init__(self, value, tmpl):
        self.value = value
        self.tmpl = tmpl

    def __str__(self):
        return self.tmpl % (self.value,)

class InvalidRotorError(ToolsValueError):
    msg_tmpl = 'Invalid rotor string (%(value)r)'
class InvalidCharacterPoolError(ToolsValueError):
    msg_tmpl = 'Invalid characters in pool (%(value)r)'

class NothingToReturn(ToolsValueError):
    msg_tmpl = 'No ham in the arguments to %(value)s()'
    def __init__(self, other):
        try:
            value = other.__class__.__name__
        except AttributeError:
            value = '<unknown>'
        self.value = value

class NotFound(ToolsValueError):
    """
    something was given but not found
    """
    msg_tmpl = 'Nothing found for pattern %(pattern)s%(ignored_info)s'
    def __init__(self, pattern, ignored=0):
        self.pattern = pattern
        self.ignored = ignored
        self.ignored_info = (ignored
                             and ' (%d entries ignored)' % locals()
                             or '')
class NothingFound(NotFound):
    """
    nothing was found, for none of the given specs
    """
    msg_tmpl = 'Nothing found for patterns %(pattern)s%(ignored_info)s'

class ToolsUsageError(Error):
    pass
class UnsupportedKeywordArguments(ToolsUsageError, TypeError):
    def __init__(self, dic):
        self.invalid_args = dic
        # hopefully TypeError compatible (untested):
        self.args = dic.keys()
        self.message = ('unsupported keyword args %r'
                        ) % ((dic,),
                             )
    def __str__(self):
        return self.message

def one_of(seq, accept_allfalse=False, use_exceptions=True):
    """
    check the given arguments; at most one of them must be true.
    The arguments may be given as either value singletons or (value,
    description) tuples.

    seq -- a sequence, e.g. [(0, '--first-choice'), (1, '--2nd-choice')]

    accept_allfalse -- specify a True value if false-only values are
                       acceptable; in this case, 0 (all false) or 1 (exactly
                       one True value) is returned

    use_exceptions -- this function raises OptionCheckError exceptions when the
                      check fails; otherwise a return value would be needed
                      (not implemented yet)

    """
    res = []
    descriptions = []
    without = 0
    for a in seq:
        if isinstance(a, (tuple, list)):
            val, descr = a
            descriptions.append(descr)
        else:
            val, descr = a, None
            without += 1
        if val:
            res.append(descr or '*')
    if len(res) == 1:
        return 1    # OK
    elif not res and accept_allfalse:
        return 0
    elif use_exceptions:
        if res:
            raise OptionConflictError(descriptions
                                      and res
                                      or None)
        else:
            raise OptionMissingError(descriptions or None)
    else:
        raise NotImplementedError

_SLEPT = 0
def sleep(secs, compact=True, step=1):
    """
    sleep the given amount of seconds, counting up visibly on the console.

    secs -- number of seconds [int]
    compact -- compact output (don't let the sleep information occupy
               the screen line permanently) [bool:True]
    step -- amount of seconds to sleep between screen output actions
            ([int:1])
    """
    # TODO: argument [function] for erasing to eol (Esc[K or similar)
    # TODO: argument [function] for output, avoiding stdout when possible
    # TODO: time.sleep supports float arguments as well
    global _SLEPT
    assert isinstance(step, int)
    assert isinstance(secs, int)
    assert step >= 1
    if secs <= 0:
        return
    stop = int(secs)
    SLEEPSTART = time()
    slept = 0
    msg = _('sleeping %%s/%s seconds ...\r') % stop
    if compact:
        eraser = ' ' * len(msg)+'\r'
    try:
        try:
            while slept < stop:
                minitim = max(int(min(step, stop-slept)), 1)
                disp = int(slept+minitim)
                print msg % disp,
                _sleep(minitim)
                slept = time() - SLEEPSTART
        except KeyboardInterrupt:
            slept = time() - SLEEPSTART
            raise
    finally:
        if compact:
            print eraser,
        else:
            print
        _SLEPT += slept

def slept():
    """
    return the amount of seconds slept using the sleep function
    (float; non-threadsafe)
    """
    # Thread-safety consideration: the _SLEPT variable will contain one
    # single sum of sleeptimes for all threads which share the module
    return _SLEPT

def parse_choices(txt):
    """
    parse the choices string for the ask function

    >>> parse_choices('ja:1;nein,njet:0;vielleicht')
    [(['ja'], 1), (['nein', 'njet'], 0), (['vielleicht'], 2)]
    """
    tmp = []
    idx = 0
    for s in txt.split(';'):
        split1 = s.split(':', 1)
        if split1[1:]:
            mapsto = int(split1[1])
        else:
            mapsto = idx
        tmp.append((split1[0].split(','),
                    mapsto,
                    ))
        idx += 1
    return tmp

def choices_maps(liz):
    reply = dict()
    text = dict()
    primaries = []
    for (words, code) in liz:
        word = words[0]
        assert code not in text
        text[code] = word
        assert word not in reply
        reply[word] = code
        primaries.append(word)
    tmp_keys = dict()
    def abbrevs(wo, co, di):
        for i in range(len(wo), 0, -1):
            a = wo[:i]
            if not di.has_key(a):
                di[a] = set([co])
            else:
                di[a].add(co)
    for (words, code) in liz:
        for w in words:
            abbrevs(w, code, tmp_keys)
    for word, codes in tmp_keys.items():
        if len(codes) == 1:
            reply[word] = codes.pop()
        else:
            assert word not in primaries
    return (reply,      # maps strings to codes
            text,       # maps codes to text
            primaries)  # in-order list of words

def get_readfunc():
    """
    return a function which reads the answer
    """
    return raw_input

def format_choices(reply, text, prim):
    return ' (%s) ' % '/'.join(prim)

def explain_choices(reply, text, prim):
    if len(prim) > 2:
        return _('Please answer %s, or %s! '
                 ) % (', '.join(prim[:-1]),
                      prim[-1])
    else:
        return _('Please answer %s! '
                 ) % _(' or ').join(prim)

def ask(txt, choices=None, default=None, onbreak=None, onescape=None,
        onerror=None,
        read_func=None, choices_formatter=None, choices_explainer=None,
        console=None):
    """
    txt -- the question to ask; should *not* contain choices information
    choices -- a string, e.g. 'yes:1;no,nein:0;all;quit'

    values (integer) for special cases:
    default -- only return was pressed
    onbreak -- KeyboardInterrupt (if no value given, is re-raised)
    onescape -- Esc was pressed (not yet supported)

    functions:
    read_func -- a function to read characters
    choices_formatter -- creates something like ' (y/n) '
    choices_explainer -- creates the message for wrong answers

    misc.:
    console -- a device to write to (hopefully not redirected)

    """
    # TODO: lap time spent waiting for answers
    # TODO: timeout (optional)
    # TODO: default for CR, space
    # TODO: default for timeout
    # TODO: get rid of raw_input (printing ASCII only)
    # TODO: function for output
    # TODO: function for input
    if choices is None:
        choices = _('yes:1;no:0')
    reply, text, primaries = choices_maps(parse_choices(choices))
    if read_func is None:
        read_func = get_readfunc()
    choices = (choices_formatter or format_choices
               )(reply, text, primaries)
    txt += choices
    explain = (choices_explainer or explain_choices
               )(reply, text, primaries)
    if console is None:
        console = get_console()
    idx = 0
    try:
        code = None
        while True:
            try:
                console.write(idx and explain or txt)
                answer = read_func()
                code = reply[answer]
                return code
            except KeyboardInterrupt:
                if onbreak is None:
                    raise
                return onbreak
            except KeyError:
                idx = (idx + 1) % 5
            except EOFError:
                warn(_('stdin is redirected'))
                if onerror is None:
                    raise
                return onerror
    finally:
        if code is not None:
            print text[code]

(SILENT,                    # simply yield nothing if nothing is found
 RAISE_EXCEPTION,           # for nospecs, notfound
 YIELD_PATTERNS,            # if nothing is found, yield the patterns
 YIELD_PATTERN,             # yield each pattern which yields no matches
 ERROR_IF_NOTHING_FOUND,    # raise an Exception if nothing is found
 ERROR_IF_NOT_FOUND,        # raise an Exception at the 1st non-matching pattern
) = range(2, 8)
DEFAULT_UNIQUESPECS = True
DEFAULT_NOSPECS = RAISE_EXCEPTION   # might change ...

class FilenameGenerator(object):
    """
    Functions to take a sequence of file specs (most likely a tuple of specs
    given as commandline arguments)
    """
    def __init__(self, *args, **kwargs):
        """
        The most basic FilenameGenerator simply yields the given patterns.
        The only option is whether to strip duplicates from the list:

        unique_specs -- a boolean value, defaulting to DEFAULT_UNIQUESPECS
                        (which is True by default)

        nospecs -- what to do if nothing was specified
        """
        try:
            unique = kwargs.pop('unique_specs')
        except KeyError:
            unique = DEFAULT_UNIQUESPECS
        try:
            nospecs = kwargs.pop('nospecs')
        except KeyError:
            nospecs = DEFAULT_NOSPECS
        assert nospecs in self.nospecs_acceptable()
        if nospecs == RAISE_EXCEPTION and not args:
            raise NothingToReturn(self)
        if unique:
            self.specs = tuple(self.unique_list(args))
        else:
            self.specs = args
        if kwargs:
            raise UnsupportedKeywordArguments(kwargs)

    def __iter__(self):
        for a in self.specs:
            yield a

    def unique_list(self, seq):
        res = []
        for item in seq:
            if item not in res:
                res.append(item)
        return res

    def nospecs_acceptable(self):
        """
        return the acceptable values for the nospecs option
        """
        return (SILENT,
                RAISE_EXCEPTION,
                )

DEFAULT_IGNORE = ['*~']
DEFAULT_NOTFOUND = YIELD_PATTERNS

class GlobFileGenerator(FilenameGenerator):
    """
    Generate filenames from file specs, supporting shell-style regular
    expressions (glob.glob)
    """

    def __init__(self, *args, **kwargs):
        """
        Additional options:

        ignore -- a pattern (or a sequence of patterns) of files which are
                  typically found but aren't of any interest; if not given,
                  the DEFAULT_IGNORE value is used (which by default ignores
                  backup files, '*~').

                  NOTE: the presence in the <args> overrides <ignore>!

        notfound -- tells what to do if a pattern (or *all* pattern) yields no
                    hits;  default: YIELD_PATTERNS
                    (NOTE: this is different from YIELD_PATTERN; see the
                    comments in the source above)
        """
        try:
            ignore = kwargs.pop('ignore')   # OK with Python 2.3
            if ignore is None:
                ignore = []
            elif isinstance(ignore, (list, tuple)):
                ignore = list(ignore)
            else:
                ignore = [ignore]
        except KeyError:
            ignore = DEFAULT_IGNORE
        self._ignore = self.unique_list([pat
                                         for pat in ignore
                                         if not pat in args])
        try:
            notfound = kwargs.pop('notfound')
        except KeyError:
            notfound = DEFAULT_NOTFOUND
        assert notfound in self.notfound_acceptable()
        self.notfound = notfound
        FilenameGenerator.__init__(self, *args, **kwargs)

    def __iter__(self):
        from glob import glob
        self.init_ignore()
        notfound = self.notfound
        found_something = 0
        if notfound == YIELD_PATTERNS:
            bogus_patterns = []
        for pat in self.specs:
            found_this = 0
            ignored_here = 0
            for fn in glob(pat):
                if self.is_ignored(fn):
                    if notfound == ERROR_IF_NOT_FOUND:
                        ignored_here += 1
                    continue
                yield fn
                found_this = 1
            if found_this:
                found_something = 1
            elif notfound == YIELD_PATTERN:
                yield pat
            elif notfound == YIELD_PATTERNS:
                bogus_patterns.append(pat)
            elif notfound == ERROR_IF_NOT_FOUND:
                raise NotFound(pat, ignored_here)
        if found_something:
            return
        else:
            if notfound == YIELD_PATTERNS:
                for pat in bogus_patterns:
                    yield pat
            elif notfound == ERROR_IF_NOTHING_FOUND:
                raise NothingFound(tuple(self.specs), self.count_ignored)

    def is_ignored(self, fn):
        from fnmatch import fnmatch
        for pat in self._ignore:
            if fnmatch(fn, pat):
                self.count_ignored += 1
                return 1
        return 0

    def init_ignore(self):
        """
        preparations before the is_ignored method can be used
        """
        self.count_ignored = 0

    def notfound_acceptable(self):
        """
        return the acceptable values for the notfound option
        """
        return (SILENT,
                YIELD_PATTERNS,
                YIELD_PATTERN,
                ERROR_IF_NOTHING_FOUND,
                ERROR_IF_NOT_FOUND,
                )

class OptionCascade(object):
    """
    (NOT IMPLEMENTED YET)
    reads configuration options from a cascade of .ini files

    IDEAS:
    - try a local version first,
      then optionally go up the directory tree,
      then try the user's preferences,
      then try the system-wide preferences,
      then use the implemented default
    - for writing:
      - try local only
      - try the first existing file up the tree
      - try the system-wide preferences file
      - try the user's preferences
      - abort when first attempt / all possibilities failed?
    - optionally create a local file with all used settings
      (collected from commandline and cascade)

    (vielleicht nicht noetig; ConfigParser.read liest auch eine Liste!
    """

def get_console():
    """
    Return a target device for non-redirectable output.

    A quite rudimentary version which simply returns standard error.
    Should be replaced by something better (depending on the operating
    system); normally, you are not interested in the redirected output
    of a -> Rotor(), but you might be interested in error texts ...
    """
    return stderr

def eraser_list(length):
    r"""
    return a "raw" -> eraser (e.g. if building a list)

    >>> eraser_list(3)
    ['\x08\x08\x08', '   ', '\x08\x08\x08']
    """
    return [ch * length
            for ch in '\b \b']

def eraser(length):
    r"""
    return a string to "erase" a string of the given length from the console

    (yes, there are shells around which don't support Escape sequences like
    \e[K which deletes until the end of line; thus, the deleting is done by
    hand)

    >>> eraser(3)
    '\x08\x08\x08   \x08\x08\x08'
    """
    return ''.join(eraser_list(length))

class TempWriter:
    """
    A callable instance to print process information (which one would't want
    to get redirected) to the console, e.g. filenames.  Should work regardless
    of the width of the terminal window, on every console which supports the
    backspace character and (unlike physical printers) prints space characters
    instead of simply moving the cursor by one position to the right.

    Example usage:
      p = TempWriter()
      for root, dirs, files in os.walk(os.curdir):
          for file in files:
              p(os.path.join(root, filename))
              ...

    """
    def __init__(self, device=None):
        self.prevlength = 0
        if device is None:
            self.device = get_console()

    def __call__(self, txt, linebreak=0, optimistic=0):
        """
        Print the given string to the configured device.

        txt -- a one-line string.  Please avoid tabs and other non-space (x20)
               characters, as these won't be taken into account.
        linebreak -- boolean argument: whether to add a linebreak or not
                     (False, by default)
        optimistic -- assume the current given string to be at least as long as
                      the previous (False by default)
        """
        if self.prevlength:
            if optimistic:
                self.device.write('\b'*self.prevlength)
            else:
                self.device.write(eraser(self.prevlength))
        if linebreak:
            self.device.write(txt+'\n')
            self.prevlength = 0
        else:
            if txt:
                self.device.write(txt)
            self.prevlength = len(txt)

    def cleanup(self, linebreak=0):
        self('', linebreak)

DEFAULT_ROTOR = "/-\\|"
class Rotor(TempWriter):
    """
    creates a function which can be called repeatedly and will
    each time print a new character (or word) to the console,
    cycling through a given sequence.

    Example usage:
      rotate = Rotor('-+|+')
      while 1:
          ...
          rotate()

    You may rotate almost anything which the shell is willing to print;
    but avoid funny stuff like tab, backspace and newline characters, as
    those will not be taken into account
    """
    def __init__(self, s=None, start=0, device=None):
        if s:
            assert len(s) > 1
        self.chars = list(s or DEFAULT_ROTOR)
        self.num = start
        self.idx = None
        TempWriter.__init__(self, device)

    def __call__(self, count=0):
        out = []
        if self.idx is None:
            self.idx = -1
        else:
            out.extend(eraser_list(len(self.chars[self.idx])))
        self.idx = (self.idx + 1) % len(self.chars)
        out.append(self.chars[self.idx])
        self.device.write(''.join(out))

    def cleanup(self):
        if self.idx is not None:
            self.device.write(eraser(len(self.chars[self.idx])))
            self.idx = None

CONSTANTS_INFO = {}
def _make_reverse_map():
    global CONSTANTS_INFO
    ucc = set(string.ascii_uppercase)
    ucc.add('_')
    for (key, val) in globals().items():
        if key.startswith('_'):
            continue
        if set(key).difference(ucc):
            continue
        if key.startswith('DEFAULT'):
            continue
        if not isinstance(val, int):
            continue
        CONSTANTS_INFO[val] = key
_make_reverse_map()

def defaults_summary():
    """
    display a summary of the currently active default values
    """
    for (key, val) in globals().items():
        if key.startswith('DEFAULT'):
            if isinstance(val, int):
                try:
                    name = CONSTANTS_INFO[val]
                except KeyError:
                    if val in (0, 1):
                        name = bool(val)
                    else:
                        name = '%d (no name)' % val
                print '%(key)s=%(name)s' % locals()
            else:
                print '%(key)s=%(val)r' % locals()
    print CONSTANTS_INFO

def set_default(name, val):
    """
    set the given default value; allows to change module defaults
    without the need to import the module as such
    """
    converted = '_'.join(('DEFAULT',
                          name.replace('_', '').replace(' ', '').upper(),
                          ))
    assert converted in globals()
    # unterscheidet zw. int- und bool-Werten:
    assert type(val) == type(globals()[converted])
    globals()[converted] = val

class mapfunc(object):
    """
    create a function which maps a string to a value
    and can be used e.g. as an argument to a callback function
    when creating optparse options.

    >>> f = mapfunc(([0, ''], [1, 'eins', 'one'], [2, 'zwei']))
    >>> f('one')
    1
    >>> f.metavar()
    'eins,zwei'
    """
    def __init__(self, maplists, cls=int, func=None):
        assert cls is not None
        if func is None:
            func = value_and_strings
        themap = {}
        meta = []
        maplists = sorted(maplists)
        for liz in maplists:
            dic = func(liz)
            val = dic['value']
            met = dic['meta']
            assert isinstance(val, cls)
            assert liz
            if met is not None:
                meta.append(met)
            for s in dic['strings']:
                themap[s] = val
        self.__meta = meta
        self.__themap = themap

    def __call__(self, s):
        return self.__themap[s]

    def metavar(self, ch=','):
        return ch.join(self.__meta)

def mapfunc_dict():
    """
    Return a dictionary as a base to the return value of the
    value_and_strings function or their variants.

    The keys are:
    strings -- the allowed argument strings
    value   -- the resulting value
    meta    -- a component for a metavar argument
    """
    return dict(strings=[],
                value=None,
                meta=None)

def value_and_strings(seq):
    """
    Take a sequence and return a dictionary (see -> mapfunc_dict)

    The given sequence is part of a sequence which is given
    during creation of a mapfunc function.

    >>> value_and_strings(1, 'eins', 'zwei')
    {'value': 1, 'meta': 'eins', 'strings': ['eins', 'zwei']}
    >>> value_and_strings(1, None, 'eins', 'zwei')
    {'value': 1, 'meta': None, 'strings': ['eins', 'zwei']}
    """
    res = mapfunc_dict()
    liz = list(seq)
    res['value'] = liz.pop(0)
    strings = res['strings']
    first = 1
    for s in liz:
        if first:
            res['meta'] = s
            first = 0
        if s is not None:
            strings.append(s)
    return res

def replaced_switches(seq):
    """
    Take a sequence and return a dictionary (see -> mapfunc_dict)

    >>> replaced_switches('space', 'all-spaces', '--ignore-all-space')
    {'value': 'space', 'meta': 'space', 'strings': ['space', 'all-spaces'],
     'replaced': ['--ignore-all-spaces']}
    """
    res = mapfunc_dict()
    val = None
    liz = list(seq)
    repl = []
    strings = res['strings']
    for s in liz:
        if s.startswith('-'):
            repl.append(s)
            continue
        elif val is None:
            val = s
            res['value'] = val
            res['meta'] = s
        strings.append(s)
    res['replaced'] = repl
    return res

def words_to_option(seq):
    """
    >>> words_to_option(('/ignorespaces', 'spaces', 'space-change'))
    {'value': '/ignorespaces', 'meta': 'spaces',
     'strings': ['spaces', 'space-change']}
    """

def noon(date=None, as_secs=None):
    """
    take a date and return it, the time being set to 12:00 (noon)

    Arguments (optional):

    date -- defaults to now
    as_secs - defaults to False, unless date given as seconds value
    """
    if date is None:
        date = localtime()
    elif isinstance(date, (int, float)):
        date = localtime(date)
        if as_secs is None:
            as_secs = 1
    liz = list(date)
    liz[3:6] = [12, 0, 0]
    tim = struct_time(liz)
    if as_secs:
        return mktime(tim)
    return tim

def daystart(date=None, as_secs=None):
    """
    take a date and return it, the time being set to 0:00

    Arguments (optional):

    date -- defaults to now
    as_secs - defaults to False, unless date given as seconds value
    """
    if date is None:
        date = localtime()
    elif isinstance(date, (int, float)):
        date = localtime(date)
        if as_secs is None:
            as_secs = 1
    liz = list(date)
    liz[3:6] = [0, 0, 0]
    tim = struct_time(liz)
    if as_secs:
        return mktime(tim)
    return tim

class DateCalculator(object):
    """
    A function class for simple date calculations (regardless of the time)

    >>> adddays = DateCalculator(1349260000)
    >>> adddays(0)[:3]
    (2012, 10, 3)
    >>> adddays(30)[:3]
    (2012, 11, 2)
    """
    def __init__(self, ref=None, freeze=None):
        """
        ref -- reference date (default: today)
        freeze -- if true, store the date when the function is created.
                  Default: true (must not be false if reference date given)
        """
        if ref is not None:
            refdate = noon(ref)
            if freeze is not None:
                assert freeze
        else:
            if freeze is None:
                freeze = 1
            if freeze:
                refdate = noon()
            else:
                refdate = None
        if refdate is not None:
            self._refsecs = mktime(refdate)
        else:
            self._refsecs = None
        self.secs_per_day = 24 * 60 ** 2

    def __call__(self, delta):
        """
        delta - an integer (1 to get 'tomorrow', -1 for 'yesterday')
        """
        assert isinstance(delta, int)
        if self._refsecs is None:
            return localtime(time()+self.secs_per_day*delta)
        else:
            return localtime(self._refsecs+self.secs_per_day*delta)

try:
    if __name__ != '__main__':
        pass
    elif 0:
        'something to try during development'
except KeyboardInterrupt:
    raise SystemExit

if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version='%prog '+__version__)
