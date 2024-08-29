#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
opo: optparse options
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           3,   # add_trace_option, DEBUG
           7,   # add_doctest_option/cb_doctest_testmod
           'rev-%s' % '$Rev: 1102 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

__all__ = ['add_date_options',
           'add_glob_options',
           'add_help_option',
           'add_verbosity_options',
           'add_version_option',
           'add_optval_option',
           'add_backup_options', # some tests still necessary
           'add_doctest_option',
           # to be used together:
           'add_trace_option', 'DEBUG',
           # callback functions:
           'cb_decrease',
           'cb_simplefunc',
           'cb_counting_sidekick',
           'cb_flags',
           'cb_list',
           'cb_fill_dict',
           'cb_doctest_testmod',
           # factory functions:
           'make_simple_callback',
           'make_splitter',
           'gimme',
           'make_inttuple_factory',
           'make_int_and_const_factory',
           # other helpers:
           'get_the_parser',
           # TODO:
           # 'cb_negations', # siehe wget.py, negations; auch für wobinich.py
           ]

try:
    from optparse import OptionConflictError, OptionValueError
except ImportError:
    from thebops.optparse import OptionConflictError, OptionValueError

from time import mktime, localtime
from os import environ
from sys import argv
try:
    # available as of Python 2.7+
    from collections import OrderedDict
except ImportError:
    OrderedDict = dict
pdb = None  # see DEBUG, cb_counting_sidekick, dbg_... functions

from thebops.shtools import DateCalculator
from thebops.anyos import isunix
from thebops.misc1 import extract_dict

try:
    _
except NameError:
    def _(s):
        return s

def cb_simplefunc(option, opt_str, value, parser, func, *args):
    """
    Simple callback function: apply the given function

    If the calling option takes a value, it is inserted
    as the 1st argument to the given function.
    """
    liz = list(args)
    if value is not None:
        liz.insert(0, value)
    setattr(parser.values, option.dest, func(*tuple(liz)))

def cb_decrease(option, opt_str, value, parser, floor=0, *args):
    """
    Simple callback function: decrease the given value by 1
    """
    val = getattr(parser.values, option.dest, 0)
    if value is None:
        val -= 1
    else:
        # can only happen if requested by calling option:
        val -= value
    assert None < -100
    if val < floor:
        val = floor
    setattr(parser.values, option.dest, val)

def cb_flags(option, opt_str, value, parser, f):
    """
    option -- ein Optionsobjekt
    opt_str -- z. B. '--search'
    value -- ein String, z. B. 'revs,msg'
    parser -- der Parser
    f -- eine Funktion, die Zeichenketten auf Zahlen (2**n) mappt
    """
    val = value.strip().lower()
    val = getattr(parser.values, option.dest, 0)
    if val is None:
        val = 0
    try:
        for s in value.split(','):
            if s:
                val |= f(s)
    except KeyError, e:
        raise OptionValueError(e.args[0])
    setattr(parser.values, option.dest, val)

def cb_list(option, opt_str, value, parser, f):
    """
    option -- ein Optionsobjekt
    opt_str -- z. B. '--search'
    value -- ein String, z. B. 'revs,msg'
    parser -- der Parser
    f -- eine Funktion, die Zeichenketten auf einen Normalwert mappt
    """
    val = value.strip().lower()
    liz = getattr(parser.values, option.dest, None)
    new = liz is None
    if new:
        liz = []
    try:
        for s in value.split(','):
            if s:
                liz.append(f(s))
    except KeyError, e:
        raise OptionValueError(e.args[0])
    if new:
        setattr(parser.values, option.dest, liz)

def cb_doctest_testmod(option, opt_str, value, parser,
                       module, quit=True,
                       break_silence=True,
                       verbose_optname='verbose',
                       verbose_add=None):
    """
    call doctest.testmod.

    module -- the module to test (required)
    quit -- quit after doctests, default: True
    break_silence -- when executing doctests without errors and
                     non-verbosely, doctest.testmod won't output
                     anything. If this option is True, and testmod
                     didn't output anything, tell about the successful
                     test.
    verbose_optname -- 'verbose', by default.
    verbose_add -- your default verbosity might be != 0. You will e.g.
                   want to specify -2 to adjust a default of 2
    """
    import doctest
    verbose = getattr(parser.values, verbose_optname)
    if verbose_add is not None and verbose is not None:
        v = verbose + verbose_add
    else:
        v = verbose
    res = doctest.testmod(module, v)
    if quit:
        if break_silence:
            if not v and res[0] == 0:
                modname = module.__name__
                print 'Doctests for %(modname)s successful.' % locals()
        raise SystemExit(0)

def make_simple_callback(func, optional=None, optval=None):
    """
    return a callback function which throws the value at the given
    function and stores it.

    func -- the function; will be given:
            - the value
            - the *callback_args
            - the **callback_kwargs
    optional -- if True, the <value> will be used only if not None
                (useful for options with optional value) 
    optval -- if not None, switches <optional> to True
    """
    if optional is None:
        optional = optval is not None

    def simple_cb(option, opt_str, value, parser,
                  *args, **kwargs):
        """
        feed the value into function <func>
        (given to make_simple_callback)
        """
        val = func(value, *args, **kwargs)
        setattr(parser.values, option.dest, val)

    def simple_cb_opt(option, opt_str, value, parser,
                      *args, **kwargs):
        """
        If the option value is not None, it is used.
        If it is None, a non-None optval is inserted.
        """
        liz = args
        if value is not None:
            liz.insert(0, value)
        elif optval is not None:
            liz.insert(0, optval)
        setattr(parser.values, option.dest,
                func(*tuple(liz), **kwargs))

    if optional:
        return simple_cb_opt
    else:
        return simple_cb

def splitdate_european(s, div='.', order='dmy',
                       dictclass=OrderedDict,
                       factory=None):
    """
    split a european-style date specification and return a dict.

    s -- the string to split
    div -- the dividing character
    order -- 'dmy' or 'ymd' (note: no 'mdy' here!)
    dictclass -- if Python provides it (and this module could find it
                 at creation time of this function!),
                 the OrderedDict class is used, which keeps the given order.
    factory -- a function which is given the following arguments:
               - the dictionary
               - the keys
               - the order argument ('dmy' or 'ymd')
               By default, the dictionary is returned.

    The doctests require the availability of the OrderedDict class
    (Python 2.7+) to succeed completely; a useful factory might be one which turns the result
    into a namedtuple (Python 2.6+).

    >>> od = splitdate_european('1.10.')
    >>> od == {'day': 1, 'month': 10, 'year': None}
    True
    >>> od
    OrderedDict([('day', 1), ('month', 10), ('year', None)])
    >>> od = splitdate_european('2014-09', '-', 'ymd')
    >>> od == {'year': 2014, 'month': 9, 'day': None}
    True
    >>> od
    OrderedDict([('year', 2014), ('month', 9), ('day', None)])
    """
    keys = ['day', 'month', 'year']
    assert order in ('dmy', 'ymd')
    if order == 'ymd':
        keys.reverse()
    if dictclass is None:
        dictclass = dict
    res = dictclass()
    for k in keys:
        res[k] = None
    for (k, v) in zip(keys, s.split(div, 2)):
        if v:
            res[k] = int(v)
    if factory is not None:
        return factory(res, keys, order)
    return res

def mkdate_simple(s, func=splitdate_european):
    """
    return the localtime(), with ...
    - ... time set to noon (12:00:00)
    - ... date components replaced by those specified
      in the given d.[m.[y]] string argument
    """
    dic = func(s)
    liz = _dd2list(dic)
    today_l = list(localtime())
    if liz[0] is not None and liz[0] < 100:
        liz[0] += (today_l[0] // 100) * 100
    today_l[3:6] = [12, 0, 0]
    for i in range(len(liz)):
        if liz[i] is not None:
            today_l[i] = liz[i]
    return localtime(mktime(today_l))

def _dd2list(dic):
    """
    date dictionary to list

    >>> d = dict(day=15, month=3, year=2014)
    >>> _dd2list(d)
    [2014, 3, 15]
    """
    return [dic['year'], dic['month'], dic['day']]

def add_date_options(pog,
                     dest='date',
                     today_args=None,
                     tomorrow_args=None,
                     yesterday_args=None,
                     parsedval_args=None,
                     parsedval_func=None,
                     metavar=None,
                     default=0):
    """
    pog -- parser or group

    Allowed regular keyword arguments for options:
    - dest
    - metavar
    - default

    Special keyword arguments:
      today_args -- long/short option strings to specify <today>
      tomorrow_args -- long/short option strings to specify <tomorrow>
      yesterday_args -- long/short option strings to specify <yesterday>
      parsedval_args -- long/short option strings for the option
                        which takes a value
      parsedval_func -- the function used to convert the given value
    """
    adddays = DateCalculator()
    cbargs = [adddays, None]
    kwargs = {'dest': dest,
              'action': 'callback',
              'callback': cb_simplefunc,
              'callback_args': None,    # replaced by tuple, see below
              }
    if default is not None:
        if isinstance(default, int) and default < 10000:
            default = adddays(default)
        elif isinstance(default, (int, float)):
            default = localtime(default)
        kwargs['default'] = default

    if today_args is None:
        today_args = ['--today',
                      '--heute',
                      ]
    if today_args:
        cbargs[1] = 0
        kwargs['callback_args'] = tuple(cbargs)
        pog.add_option(*tuple(today_args), **kwargs)
    if yesterday_args is None:
        yesterday_args = ['--yesterday',
                          '--gestern',
                          ]
    if yesterday_args:
        cbargs[1] = -1
        kwargs['callback_args'] = tuple(cbargs)
        pog.add_option(*tuple(yesterday_args), **kwargs)
    if tomorrow_args is None:
        tomorrow_args = ['--tomorrow',
                         '--morgen',
                         ]
    if tomorrow_args:
        cbargs[1] = 1
        kwargs['callback_args'] = tuple(cbargs)
        pog.add_option(*tuple(tomorrow_args), **kwargs)
    if parsedval_args is None:
        parsedval_args = ['--date',
                          '--datum',
                          ]
    if parsedval_args:
        if parsedval_func is None:
            parsedval_func = mkdate_simple
        del kwargs['callback_args']
        if metavar is None:
            metavar = getattr(parsedval_func, 'metavar', None)
        kwargs.update({'callback': cb_simplefunc,
                       'callback_args': (parsedval_func,),
                       'type': 'string',
                       'metavar': metavar,
                       })
        pog.add_option(*tuple(parsedval_args), **kwargs)

def add_help_option(pog, *args, **kwargs):
    """
    Add a --help option to the given OptionParser or OptionGroup object
    (possible only if not already done during creation of the OptionParser
    object; to suppress this, create it with 'add_help_option=0').

    All options but the "parser or group" are optional; by default, the only
    difference to the non-suppressed --help option is the additional '-?'
    option string (and your free choice to put it into an option group).
    """
    # TODO:
    # - autosplit to two options if an integer constant for --help is given
    # - ... perpaps introduce "add_..._options" for this purpose
    if not args:
        args = ('-h', '-?', '--help')
    keys = kwargs.keys()
    if 'action' not in keys:
        kwargs['action'] = 'help'
    if 'help' not in keys:
        kwargs['help'] = _('show this help message and exit')
    pog.add_option(*args, **kwargs)

def add_version_option(pog, *args, **kwargs):
    """
    Add a --version option to the given OptionParser or OptionGroup object
    (possible only if not already done during creation of the OptionParser
    object; to suppress this, create it without the 'version' argument
    and give this argument to this function instead).

    Important argument:

    version -- the program version, e.g. a string, or a tuple of integers. You
               *must* specify this, unless you change the default 'version'
               action to something else, e.g. 'count', and build your version
               information facility yourself.

    All arguments to add_option are supported; by default, the only difference
    to the non-default --version option is the additional '-V' option string
    (and your free choice to put it into an option group).
    """
    if not args:
        args = ('-V', '--version')
    keys = kwargs.keys()
    if 'version' in keys:
        version = kwargs.pop('version')
        if isinstance(version, (int, float)):
            version = '%%prog %s' % version
        elif isinstance(version, (list, tuple)):
            version = ' '.join(('%prog',
                                '.'.join(map(str, version))))
        elif isinstance(version, basestring):
            pass
        else:
            version = '%%prog %s' % (version,)
        pa = pog
        while hasattr(pa, 'parser'):
            pa = getattr(pa, 'parser')
        pa.version = version

    if 'action' not in keys:
        kwargs['action'] = 'version'
    if 'help' not in keys:
        kwargs['help'] = _("show program's version number and exit")
    pog.add_option(*args, **kwargs)

def add_verbosity_options(pog,
                          dest='verbose',
                          default=0,
                          action='count',
                          complement=None,
                          verbose_help=None,
                          q_help=None,
                          quiet_help=None,
                          q_args=None,
                          q_kwargs=None):
    """
    Add counting -v/--verbose option, under certain conditions
    accompanied with --quiet and a decreasing -q.

    This function is work in progress; please specify keyword arguments,
    since the exact signature might change!

    Options are:

    dest -- propagated to option constructors
    default -- dto., default: 0
    action -- 'count' (default) or 'store_true'
    complement -- whether to create the complementary options
                  -q and --quiet. Default is yes, if the default value
                  is != 0, else no.
    verbose_help -- your own help string for the -v/--verbose option;
                    specify a non-None false value to suppress the default help
    q_help -- your own help string for the -q option (dto.)
    quiet_help -- dto., for the --quiet option
    q_args -- unnamed arguments to complement function (currently used only
              if complement = 1)
    q_kwargs -- kwargs to the cb_decrease callback function which is used
                by '-q'. By default, this won't ever set the verbosity value to
                a number below zero; to change this, you might use {'floor':
                None}.
    """
    # help strings:
    if verbose_help is None:
        if action == 'count':
            verbose_help = _('be verbose (-vv: even more verbose)')
        else:
            verbose_help = _('be verbose')
    elif not verbose_help:
        verbose_help = None
    # processing:
    pog.add_option('-v', '--verbose',
                   dest=dest,
                   default=default,
                   action=action,
                   help=verbose_help)
    if complement is None:
        complement = int(default != 0)
        if default >= 2:
            complement = 2
    if not complement:
        return
    # more help strings:
    if quiet_help is None:
        quiet_help = _('switch extra output off')
    elif not quiet_help:
        quiet_help = None
    if complement < 2:
        kwargs = dict( dest=dest,
                       action='store_const',
                       const=0,
                       help=quiet_help)
        if q_args is None:
            q_args = ('--quiet', '-q')
        pog.add_option(*q_args, **kwargs)
        return
    if q_help is None:
        q_help = _('decrease verbosity')
    elif not q_help:
        q_help = None
    if quiet_help is None:
        quiet_help = _('switch extra output off')
    elif not quiet_help:
        quiet_help = None
    try:
        pog.add_option('-q',
                       dest=dest,
                       action='callback',
                       callback=cb_decrease,
                       callback_kwargs=q_kwargs,
                       help=q_help)
    except OptionConflictError:
        pass
    pog.add_option('--quiet',
                   dest=dest,
                   action='store_const',
                   const=0,
                   help=quiet_help)

def add_glob_options(pog,
                     dest=None,
                     default=None):
    """
    add --glob and --no-glob options to tell a program to evaluate
    or not shell-style regular expressions for commandline-given
    file (or directory..., whatever you need) arguments.

    On Linux operating systems and alike, usually the shell does the expansion;
    on DOS-descended operating systems (including Windows(tm) and OS/2(tm)),
    this is done by the programs themselves.

    dest - propagated to the option constructor, default: 'glob'
    default - give a non-None value to override the calculation from the
              anyos module
    """
    s = ('', _(' (default on this platform)'))
    if default is None:
        default = not isunix()
    else:
        default = bool(default)
    pog.add_option('--glob',
                   dest=dest or 'glob',
                   default=default,
                   action='store_true',
                   help=_('evaluate shell-style regular expressions%s'
                   ) % s[default])
    pog.add_option('--no-glob',
                   dest=dest or 'glob',
                   action='store_false',
                   help=_('leave regular expression expansion to the shell%s'
                   ) % s[not default])

def add_doctest_option(pog, *args, **kwargs):
    """
    Add an option which immediately executes the doctests of the calling
    module.

    Usage:
        import mod
        add_doctest_option(parser, module=mod)

    For more options, see the cb_doctest_testmod callback function.
    """
    if not args:
        args = ('--doctest',)
    callback_kwargs = extract_dict(kwargs,
               ('module', 'quit', 'break_silence',
                'verbose_optname', 'verbose_add'))
    quit = callback_kwargs.get('quit', 1)
    kwa = {'action': 'callback',
           'callback': cb_doctest_testmod,
           'help': quit
               and _('execute doctests and quit')
               or  _('execute doctests and continue'),
           'callback_kwargs': callback_kwargs,
           }
    if kwargs:
        kwa.update(kwargs)
    pog.add_option(*args, **kwa)

def cb_counting_sidekick(option, opt_str, value, parser,
                         *funcs):
    """
    combines counting to calling functions:
    at first call, the first function is called,
    at second call the second.

    Used for add_trace_option/DEBUG.
    """
    val = getattr(parser.values, option.dest, 0)
    if value is None:
        value = 1
    if val is None:
        val = 1
    else:
        # can only happen if requested by calling option:
        val += value
    setattr(parser.values, option.dest, val)
    if val <= len(funcs):
        funcs[val-1]()

_DEBUG_KEY = 'dummy'
def DEBUG(func=None, *args, **kwargs):
    """
    For development purposes, simplifies the usage of pdb.set_trace.
    No need for

      if 0:
          import pdb; pdb.set_trace()

    everywhere in the code anymore.

    To be used together with add_trace_option.

    If called with arguments, the first one is checked for callability;
    if it evaluates to a True value, the processing is continued.

    If the first argument is not callable, no **kwargs are allowed.
    Otherwise, all *args are checked for their boolean value.
    """
    global pdb, _DEBUG_KEY
    if _DEBUG_KEY == 'dummy':
        return
    else:
        if callable(func) and not func(*args, **kwargs):
            return
        elif kwargs:
            assert not kwargs, (
                    'keyword args require a callable first argument'
                    ' (DEBUG(%r, %s, %s)'
                    ) % (func, args, kwargs)
        check = func is not None or args
        if check:
            for item in (func,) + args:
                if item:
                    check = 0
                    break
            if check:
                return

        if _DEBUG_KEY == 'init':
            import pdb
            _DEBUG_KEY = 'trace'
        elif _DEBUG_KEY == 'trace':
            return pdb.set_trace()  # -TT

def _dbg_import():
    # DEBUG can be used anywhere in application code;
    # no need to import pdb
    global pdb, _DEBUG_KEY
    import pdb
    _DEBUG_KEY = 'init'

def _dbg_start():
    # DEBUG will pdb.set_trace() when called after options evaluation;
    # see add_trace_option, cb_counting_sidekick
    global pdb, _DEBUG_KEY
    import pdb
    _DEBUG_KEY = 'trace'

def _dbg_options():
    # allows to debug options evaluation;
    # see add_trace_option, cb_counting_sidekick
    return DEBUG()

def add_trace_option(pog, *args, **kwargs):
    """
    Usage:

      from thebops.opo import add_trace_option, DEBUG
      # ...
      p = OptionParser(...)
      add_trace_option(p)   # counting option, -T
      # ...
      o, a = p.parse_args()
      DEBUG()               # calls set_trace, if -TT

    If the trace option is not given, every call to the DEBUG function will
    simply do nothing.
    If it is given once (-T), pdb is imported, and the first call to DEBUG will do
    nothing (but "awake" it)
    If it is given twice (-TT), the first call will execute pdb.set_trace().
    If it is given three times (-TTT), pdb.set_trace() is executed immediately,
    thus allowing to debug options evaluation.

    """
    KEYS = {'dest': 'trace',
            'action': 'callback',
            'callback': cb_counting_sidekick,
            'callback_args': (_dbg_import,
                              _dbg_start,
                              _dbg_options,
                              ),
            }
    KEYS.update(kwargs)
    if 'help' in KEYS:
        if not KEYS['help'].strip():
            del KEYS['help']
    else:
        KEYS['help'] = _('increase debugging level: '
                'with -T, DEBUG anywhere in the code; '
                'with -TT, start debugging after options evaluation; '
                'with -TTT, debugging starts *immediately* during '
                'options evaluation.')
    if not args:
        args = ('-T',)
    pog.add_option(*args, **KEYS)

def default_backup_type():
    return environ.get('VERSION_CONTROL', 'existing')

def default_backup_suffix():
    return environ.get('SIMPLE_BACKUP_SUFFIX', '~')

BACKUP_TYPES = (
        ('none', 'off'),
        ('simple', 'never'),
        ('numbered', 't'),
        ('existing', 'nil'),
        )
def normal_backup_type(v, bogus='error'):
    assert bogus in ('warn', 'error')
    fromenv = None
    if v is None:
        v = default_backup_type()
    for tup in BACKUP_TYPES:
        if v in tup:
            return tup[0]
    if bogus == 'warn':
        warn(_('ignoring bogus backup type "%s"'
               ) % (v,))
        return 'existing'
    raise OptionValueError(v)

def cb_backup_args(option, opt_str, value, parser,
                   boolean_dest=None, bogus='error'):
    """
    callback funktion to evaluate backup args
    """
    val = normal_backup_type(value, bogus)
    setattr(parser.values, option.dest, val)
    if boolean_dest:
        setattr(parser.values, boolean_dest,
                val != 'none')

def cb_backup_trick17(option, opt_str, value, parser,
                      type_dest='backup_type', bogus='error'):
    """
    callback function to fix the problem described in the add_backup_options
    docstring
    """
    val = getattr(parser.values, type_dest)
    if val in (None, 'none'):
        val = normal_backup_type(None, bogus)
        setattr(parser.values, type_dest, val)
    setattr(parser.values, option.dest, val!='none')

def gimme(const):
    """
    A very simple factory: return a function which returns a constant value.
    Useful for defaultdicts.

    >>> f = gimme(4)
    >>> f()
    4
    >>> f.__name__
    'gimme_4'
    """
    def f():
        return const
    f.__name__ = 'gimme_%s' % const
    return f

def make_inttuple_factory(ch):
    """
    return a function which splits a string and returns a 2-tuple of integers.

    >>> func = make_inttuple_factory('=')
    >>> func('1=2')
    (1, 2)
    >>> make_inttuple_factory(':')('2:3')
    (2, 3)
    """
    def inttuple(s):
        liz = s.split(ch, 1)
        return tuple(map(int, liz))
    return inttuple

def make_int_and_const_factory(const):
    """
    return a function which returns a (num, const) tuple for any
    given 'num'.

    >>> func = make_int_and_const_factory(42)
    >>> func('1')
    (1, 42)
    """
    def consttuple(s):
        return (int(s), const)
    return consttuple

def make_splitter(factory, ch=',', skipempty=True):
    """
    Create a splitter function

    >>> factory = make_inttuple_factory(':')
    >>> splitter = make_splitter(factory)
    >>> tuple(splitter('1:2,2:3,'))
    ((1, 2), (2, 3))
    """
    def splitter(s):
        for chunk in s.split(ch):
            yield factory(chunk)
    def splitter_skipempty(s):
        for chunk in s.split(ch):
            if chunk:
                yield factory(chunk)
    if skipempty:
        return splitter_skipempty
    else:
        return splitter


def cb_fill_dict(option, opt_str, value, parser,
                 splitter):
    """
    callback function: fill a dictionary.
    The dictionary can be affected by more than one option; thus,
    the first option which shares the common dest(ination) - and
    uses this callback function - creates the dictionary.

    Non-standard arguments:

    splitter - generates (key, value) tuples from the
               string argument.
    """
    dic = getattr(parser.values, option.dest)
    if dic is None:
        dic = {}
        setattr(parser.values, option.dest, dic)
    for (key, val) in splitter(value):
        dic[key] = val


def add_backup_options(pog,
                       boolean_dest='backup',
                       bogus='error',
                       hidden_group=None,
                       hidden_option='-b'):
    """
    add the backup options like known from *X tools like tar, cp, msgmerge
    etc., including consideration of the environment vars SIMPLE_BACKUP_SUFFIX
    (for --suffix, destination: backup_suffix) and VERSION_CONTROL (--backup,
    destination: backup_type).

    The value to the --backup option is optional; thus, the only supported
    syntaxes are "--backup [other, non-related options or arguments]" or
    "--backup=value".

    boolean_dest -- the destination of a boolean value, which is written when
                    the --backup[=TYPE] is used; if 'none' (which can come from
                    the environment, if used without an argument), this would
                    be False.
                    Note: Unless you specify a <hidden_group> to take the
                    <hidden_option>, this value won't exist in the parsed
                    options object if the --backup option is not used
    bogus -- if 'error', an unsupported value (from the commandline, or from
             the environment) will raise an error; if 'warn', a fallback value
             is used (currently: 'existing')
    hidden_group -- a group to take the <hidden_option>, which will ensure the
                    existence of the <boolean_dest> option value in any case.
                    If not finally added, the option won't be visible in the
                    help output.
    hidden_option -- '-b', by default.
                     Since it is present, it must work...
                     Thus, a callback function is used, which overrides a
                     former --backup=none, if necessary
    """
    pog.add_option('--suffix',
                   dest='backup_suffix',
                   action='store',
                   metavar=_('CHAR'),
                   default=default_backup_suffix(),
                   help=_('backup suffix, default: \'~\', or the value of '
                   'the SIMPLE_BACKUP_SUFFIX environment variable'))
    add_optval_option(pog,
                   '--backup',
                   dest='backup_type',
                   action='callback',
                   type='string',
                   empty=None,
                   metavar='|'.join([tup[0] for tup in BACKUP_TYPES]),
                   callback=cb_backup_args,
                   callback_args=(boolean_dest, bogus),
                   # TODO: help formatter which aligns the tabs vertically
                   #       and preserves line breaks
                   help=_(('adjust the backup type, default: none, or the '
                   'value of the VERSION_CONTROL environment variable. '
                   'NOTE: With VERSION_CONTROL = none or off, '
                   'this option is ignored.  '
                   'Allowed values are:\n'
                   '  none, off\tnever make backups\n'
                   '  numbered, t\tmake numbered backups\n'
                   '  existing, nil\tnumbered if numbered backups exist,'
                                     ' simple otherwise\n'
                   '  simple, never\talways make simple backups'
                   ).replace('\t', ' -- ')
                    .replace('\n', ';')
                    .replace(':;', ':')
                    ))
    if hidden_group and hidden_option and boolean_dest:
        hidden_group.add_option(hidden_option,
                                dest=boolean_dest,
                                action='callback',
                                callback=cb_backup_trick17,
                                callback_args=('backup_type', bogus),
                                help=_('activate backup (unless the '
                                'VERSION_CONTROL environment variable '
                                'is "none" or "off")'
                                '; preserves the type adjusted by the '
                                '--backup=type option'))

def add_optval_option(pog, *args, **kwargs):
    """
    Add an option which can be specified without a value;
    in this case, the value (if given) must be contained
    in the same argument as seen by the shell,
    i.e.:

    --option=VALUE, --option will work;
    --option VALUE will *not* work

    Arguments:
    pog -- parser or group
    empty -- the value to use when used without a value

    Note:
      If you specify a short option string as well, the syntax given by the
      help will be wrong; -oVALUE will be supported, -o VALUE will not!
      Thus it might be wise to create a separate option for the short
      option strings (in a "hidden" group which isn't added to the parser after
      being populated) and just mention it in the help string.
    """
    if 'empty' in kwargs:
	empty_val = kwargs.pop('empty')
        # in this case it's a good idea to have a <default> value; this can be
        # given by another option with the same <dest>, though
        for i in range(1, len(argv)):
            a = argv[i]
            if a == '--':
                break
            if a in args:
                argv.insert(i+1, empty_val)
                break
    pog.add_option(*args, **kwargs)

def get_the_parser(pog):
    """
    take an OptionParser or OptionGroup object
    and return the (root) OptionParser object
    """
    use = pog    # don't change the given object!
    while 1:
        try:
            use = use.parser
        except AttributeError:
            return use


if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=__version__)

