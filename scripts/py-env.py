#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Python environment variables info
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           2,   # REMatcher; py26 -> py26+; some (but not all) bugs fixed
           1,   # small bugfix (blank lines); --trace option hidden
           'rev-%s' % '$Rev: 938 $'[6:-2],
           # TODO: info about variable meanings
           # TODO: checking functions (enabled/disabled, isdir ...)
           # TODO: check directories/files for existence
           # TODO: for sys.path entries, tell about reasons (PYTHONPATH ...)
           # TODO: suffixes for directories
           # TODO: "emulate" Zope (..._HOME)
           )
__version__ = '.'.join(map(str, VERSION))
from sys import version_info, path
from os import environ
try:
    from thebops.enhopa import OptionParser, OptionGroup
except ImportError:
    from optparse import OptionParser, OptionGroup
try:
    set
except NameError:
    from sets import Set as set
from pprint import pprint	# DEBUG

from thebops.errors import error, info, check_errors
from thebops.opo import add_version_option, add_verbosity_options

from pprint import pprint	# DEBUG
# pprint(environ.keys())
	# vim: tabstop=35 cursorcolumn tw=72
pyvars = [                         # ---- noexpandtab      textwidth=80 ----- #
    ('py',
     'all Python versions', {
        'PYTHONHOME':	"Location of standard libraries",
        'PYTHONPATH':	"Additions to standard search path for modules",
        'PYTHONSTARTUP':	"Interactive mode; commands run before"
                        	" first input is prompted for",
        'PYTHONY2K':	"set nonempty to require 4 year date formats",
        'PYTHONOPTIMIZE':	"set nonempty causes basic optimisation."
                         	" Set to 2 also discards docstrings",
        'PYTHONDEBUG':	"set nonempty to turn on python debugging",
        'PYTHONINSPECT':	"force interactive mode on end of"
                        	" normal program termination",
        'PYTHONUNBUFFERED':	"turn OFF buffering of stdin, stdout and stderr",
        'PYTHONVERBOSE':	"provide verbose information about module"
                        	" loading (set to 2 for very verbose!)",
        'PYTHONWARNINGS':	"one or more (comma separated) warning"
                         	" handling specs (like for -W)",
        'PYTHONCASEOK':	"Ignore case in importing modules",
     }),
    ('py25-',
     'debug mode (up to Python 2.5)', {
        'THREADDEBUG':	"If set, Python 2.5- will print threading debug info"
                      	' (renamed to PYTHONTHREADDEBUG as of Python 2.6)',
     }),
    ('py26+',    # official documentation
     'Added at Python 2.6', {
        'PYTHONIOENCODING':	"change unicode handling"
                           	" for stdin / stdout / stderr",
        'PYTHONNOUSERSITE':	"don't add user's directory to sys.path",
        'PYTHONUSERBASE':	"change the user's directory",
        'PYTHONEXECUTABLE':	"Mac OS X Only."
                           	" Override the program name in argv[0]",
     }),
    ('py26+',    # source: see URL below
     'http://docs.python.org/library/sys.html#sys.dont_write_bytecode', {
        'PYTHONDONTWRITEBYTECODE':	"don't write bytecode"
                                  	" (-B, Python 2.6+)",
     }),
    ('pydoc',
     'pydoc', {
        'PYTHONDOCS':	"URL or local directory for Library Reference Manual"
                     	" pages, instead of http://docs.python.org/library/",
     }),
    ('debug',
     'debug mode', {
        'PYTHONTHREADDEBUG':	"If set, Python will print threading debug info.",
    # Changed in version 2.6: Previously, this variable was called THREADDEBUG.
        'PYTHONDUMPREFS':	"If set, Python will dump objects and reference"
                         	" counts still alive after shutting down the"
                         	" interpreter.",
        'PYTHONMALLOCSTATS':	"If set, Python will print memory allocation"
                            	" statistics every time a new object arena is"
                            	" created, and on shutdown.",
     }),
    ]
zope_startup = [
    ('zope',
     'Zope startup files', {
        'ZOPE_HOME':	"location of Zope installation",
        'PYTHON_HOME':	"location of used Python interpreter",
        'INSTANCE_HOME':	"location of Zope instance",
        }),
    ]
roundup = [
    ('roundup',
     'Roundup (issue tracker)', {
        'TRACKER_HOME':	"location of a single Roundup instance",
        }),
    ]
django = [
    ('django',  # https://docs.djangoproject.com/en/dev/topics/settings/
     'Django Web framework', {
        'DJANGO_SETTINGS_MODULE':	"settings module in Python path syntax,"
                                 	" e.g. mysite.settings; 'settings' should be"
                                 	" on the Python import search path. ",
     }),
    ]
pyvars.extend(zope_startup)
pyvars.extend(roundup)
pyvars.extend(django)
if 0:\
pprint(pyvars)	# DEBUG

# allowed (non-generic) group specs:
groups = []
for tup in pyvars:
    if not tup[0] in groups:
        groups.append(tup[0])
assert 'other' not in groups

prefixes = [
        ('PYTHON', 	# the prefix
         'debug',	# the predecessor group
         ),
        ('ZOPE', 'zope'),
        ('ROUNDUP', 'roundup'),
        ('DJANGO', 'django'),
        ]
other_generic = {}
for tup in prefixes:
    prefix, after_group = tup
    other_generic[prefix] = groups.index(after_group) + 0.1

defaultgroups = ['py']
if version_info >= (2, 6):
    defaultgroups.append('py26+')
else:
    defaultgroups.append('py25-')

p = OptionParser(usage='%%prog [-mo] [-g %s,...]' % ','.join(defaultgroups),
                 description=_('Tell about environment variables recognised'
                 ' by the Python interpreter and/or certain Python software,'
                 ' and optionally about their '
                 'impact on the module search path'))
g = OptionGroup(p, _("Python variables information"))
g.add_option('--group', '-g',
             action='append',
             dest='groups',
             metavar='|'.join(groups),
             help=_('specify the groups of variables you are interested in; '
             'you may use this option more than once, or separate values with'
             ' commas (",")'))
g.add_option('--missing', '-m',
             action='store_true',
             help=_('tell about the "missing" variables of the given group(s)'
             ))
g.add_option('--others', '-o',
             action='count',
             help=_('tell about existing variables of non-given group(s)'
             '; -oo: include any variable beginning with "PYTHON"'
             ))
g.add_option('--path', '-p',
             action='store_true',
             help=_('show sys.path'))
add_version_option(p, version=VERSION)
add_verbosity_options(p)
p.add_option_group(g)
g = OptionGroup(p, _("Debugging"))
g.add_option('-T', '--trace',
             action='count',
             help=_('load pdb and set_trace'))
if 0:\
p.add_option_group(g)
try:
    p.set_collecting_group()
except AttributeError:
    pass
option, args = p.parse_args()
if option.trace:
    import pdb
    pdb.set_trace()

class REMatcher:
    """
    A class for RE matching functions.
    Arguments to the __init__ method:

    expr -- a regular expression. Unless starting with "^"
            or ending with "$", these are amended

    groupname -- the name of the match group of interest ("(?P<name>...)").
                 If given, the found value (or None) will be returned;
                 otherwise True or False only.
    """
    def __get_re_module(self):
        cls = self.__class__
        try:
            return cls.__re_module is not None
        except AttributeError:
            try:
                import re
                cls.__re_module = re
                return 1
            except ImportError:
                cls.__re_module = None
                return 0

    def __init__(self, expr, groupname=None, compileflags=0):
        self.__get_re_module()
        if self.__re_module is None:
            self.__enabled = 0
            return
        if groupname is not None:
            assert isinstance(groupname, str)
            assert groupname
        self.__groupname = groupname
        self.__enabled = 1
        self.__expr = expr
        self.__ro = self.__class__.__re_module.compile(expr, compileflags)

    def __call__(self, s):
        if self.__class__.__re_module is None:
            return None
        mo = self.__ro.match(s)
        if mo:
            if self.__groupname is None:
                return True
            return mo.group(self.__groupname)
            # return mo.groupdict()[self.__groupname]
        elif self.__groupname is None:
            return False
        else:
            return None     # implicit, but anyway

used_groups = set()
if option.groups:
    specsPythonVersion = REMatcher('^py(?P<version>2[0-9])$', 'version')
    for gr in option.groups:
        for g in gr.split(','):
            if g in groups:
                used_groups.add(g)
            else:
                # generic support for 'py24' etc. specs: 
                tst = specsPythonVersion(g)
                if tst is None:
                    error(_('unknown variables group %(g)r'
                            ) % locals())
                else:
                    vtup = tuple(map(int, tst[2:]))
                    used_groups.add(vtup >= (2, 6)
                                    and 'py26+'
                                    or  'py25-')
elif not option.path:	# the only other option
    for g in defaultgroups:
        used_groups.add(g)
if not used_groups and not option.path: # won't happen ...
    error(_('nothing to do (no variables groups specified)'))
check_errors()
if 0: print used_groups

interesting_vars = list()
other_vars = list()
for tup in pyvars:
    if tup[0] in used_groups:
        i = groups.index(tup[0])
        interesting_vars.extend([(i, k)
                                 for k in tup[2].keys()])
    else:
        if option.others:
            other_vars.extend([k
                               for k in tup[2].keys()])
interesting_names = [n[1] for n in interesting_vars]
interesting_vars.sort()
interesting_vars.append((None, None))
if 0:\
pprint(interesting_vars)

found_as = dict()
found_other = list()
for k in environ.keys():
    ku = k.upper()
    if ku in interesting_names:
        found_as[ku] = (k, environ[k])
    elif ku in other_vars:
        found_as[ku] = (k, environ[k])
        found_other.append(ku)
    elif option.others >= 2 and ku.startswith('PYTHON'):
        found_as[ku] = (k, environ[k])
        found_other.append(ku)

# pprint(found_as)
complained_about = set()
group_index = None
missing = list()

dirty = 0
def divide():
    global dirty
    if dirty:
        print
    else:
        dirty = 1

for gi, varname in interesting_vars:
    # print (gi, varname)	# DEBUG
    if gi != group_index:
        if missing and option.missing:
            for varname in missing:
                if not varname in complained_about:
                    info(_('not defined: %(varname)s') % locals())
                    complained_about.add(varname)
            del missing[:]
        group_index = gi
    if varname is None:
        break
    tup = found_as.get(varname, None)
    if tup is None:
        missing.append(varname)
        continue
    found_var, val = tup
    print '%(found_var)s=%(val)s' % locals()

if found_other:
    divide()
    found_other.sort()
    for varname in found_other:
        found_var, val = found_as.get(varname)
        print '%(found_var)s=%(val)s' % locals()

if option.path:
    divide()
    print _('Python module search path:')
    for p in path:
        print '  %(p)s' % locals()
