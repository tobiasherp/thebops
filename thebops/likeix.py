#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
thebops.likeix: find POSIX-conforming tools, even on Windows(TM) systems

This module serves two purposes:
- when calling a program without using the shell, the PATH is not searched.
  The functions in this module yield absolute paths.

  The find_progs function (anyos module) tries to ferret out all occurrences
  on the system, using a smart strategy:
  0. (for configuration files; typically not used for executables)
     searches a directory and all of its *parents* (not: children!)
  1. searches a specified set of directories.
     Some tools install on Win* in some directory somewhere below
     %ProgramFiles% which are not available in the PATH.
     find_progs optionally takes a sequence of directory specs which
     may contain environment variable names in Python's dict comprehension
     syntax; if the variable is unknown, the entry is ignored.
     (Of course, this is way faster than searching an entire harddisk.)
  2. Searches the PATH.
     When doing this, some directories can be excluded (the xroots argument)
     which contain very likely programs which don't behave like the desired
     POSIX tool at all, e.g. %(SystemRoot)%.

- for some often needed programs, there are certain useful strategies,
  and some well- (or not-so-well-) known environment variables.

  This module contains some special functions which salt the anyos.find_progs
  function with appropriate defaults.
  When seeking a certain program in various scripts, just update (or add!) the
  respective function in this module, rather than updating every single script.

Of course, you are welcome to tell the author about your additions :-)

As long as the strategies of the functions in this module are sufficient to
you, all you need to do is something like

    from thebops.likeix import ToolsHub
    hub = ToolsHub()
    print hub['sed']

... which will give you the complete path to the 'sed' program which was found
for you on your system, or None.

You can throw the name of any tool to your ToolsHub object.  If it knows a
special find_<toolname> function, it will use it; otherwise, it will try its
fallback function (find_PosixTool, by default).
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           3,   # ToolsHub (no demo so far)
           9,   # tuple_and_dict (not yet used); doctests
           'rev-%s' % '$Rev: 1100 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))
__all__ = ['ToolsHub',      # smart wrapper for find_progs
           'find_progs',    # from anyos.py
           # wrappers for find_progs:
           'find_diff',
           'find_find',
           'find_grep',
           'find_ln',
           'find_python',
           'find_sed',
           'find_sort',
           'find_tar',
           'find_uniq',
           'find_vim',
           'find_gvim',
           # ... for the PuTTY suite:
           'find_putty',
           'find_pscp',
           'find_psftp',
           'find_plink',
           'find_pageant',
           # ... SCM tools:
           'find_cvs',
           'find_svn',
           'find_tsvn',
           # ... cryptographic tools:
           'find_gpg',
           # ... other specific tools:
           'find_xmllint',
           # ... or any generic POSIX tool:
           'find_PosixTool',
           # for demo:
           'dedicated_finders',
           # wrap them all and take the 1st/best:
           'get_1st',
           'get_best',
           # indirs generation:
           'ProgramDirs',
           'PosixToolsDirs',
           'CygwinDirs',
           # ... there are more, but you won't need to use them directory
           # data:
           'WINDOWS_ROOTS',
           # exceptions, from anyos.py:
           'ProgramNotFound',
           'VersionsUnknown',
           'VersionConstrained',
           ]

from os import environ
from os.path import abspath, join
from thebops.anyos import find_progs, ProgramNotFound, vdir_digits, \
        VersionsUnknown, VersionConstrained

try:    # i18n-Dummy
    _
except NameError:
    _ = lambda s: s

def get_1st(f, **kwargs):
    """
    call the given find_... function and return the 1st hit

    f -- the name of the program as a non-unicode string (the wrapper function
         being find_<f>), or a generator function.

    The function will yield a KeyError if a string is given, and the
    respective find_<f> function doesn't exist in this module.

    Additional keyword arguments can be specified and are passed on to the
    function
    """
    if isinstance(f, str):
        f = globals()['find_%s' % f]
    for item in f(**kwargs):
        return item
    if 'progname' in kwargs:
        raise ProgramNotFound('%(progname)s not found' % kwargs)
    elif f.__name__.startswith('find_'):
        progname = f.__name__[5:] or '<unknown program>'
        raise ProgramNotFound('%(progname)s not found' % locals())
    else:
        raise ProgramNotFound('%r not successful' % f)

def _check_version(v, min_version=None, version_below=None,
                   onerror='return'):
    """
    check the given version tuple <v> against the reference values.

    Note: This function is currently meant for the callpy function only
    (py2/py3) and not considered public; the signature might change
    significantly!

    >>> _check_version((2, 5), min_version=(2, 5), version_below=(3, 0))
    True
    >>> _check_version((2, 4, 4), min_version=(2, 5), version_below=(3, 0))
    False
    >>> _check_version((3, 0), min_version=(2, 5), version_below=(3, 0))
    False
    """
    assert onerror in ('return', 'error')
    if v < min_version:
        if onerror == 'error':
            raise VersionConstrained()
        return False
    if version_below is not None:
        if v >= version_below:
            if onerror == 'error':
                raise VersionConstrained()
            return False
    return True

def get_best(f,
             version_func=vdir_digits,
             version_below=None,
             min_version=None,
             **kwargs):
    """
    call the given find_... function and return the best hit

    f -- the name of the program as a non-unicode string (the wrapper function
         being find_<f>), or a generator function.

    version_func -- a function which extracts version info from each hit.
                    The default, <vdir_digits>, simply inspects the directory
                    for version information and returns e.g. (7, 2) for
                    .../vim72 directories, which is fine e.g. for vim and
                    python installations on Windows systems.

    version_below -- a version to stay below; e.g. to avoid python 3
                     interpreters, specify (3, 0)

    The function will yield a KeyError if a string is given for <f>, and the
    respective find_<f> function doesn't exist in this module.
    If seeked, but w/o success, a ProgramNotFound exception or one of its
    descendants is raised.

    Additional keyword arguments can be specified and are passed on to the
    function
    """
    if isinstance(f, str):
        f = globals()['find_%s' % f]
    found = []
    unversioned = []
    mismatch = 0
    for item in f(**kwargs):
        ver = version_func(item)
        if ver is None:
            unversioned.append(item)
        elif _check_version(ver, min_version, version_below):
            found.append((ver, item))
        else:
            mismatch += 1
    if found:
        found.sort()
        return found[-1][1]
    progname = None
    if 'progname' in kwargs:
        progname = kwargs['progname']
    elif f.__name__.startswith('find_'):
        progname = f.__name__[5:] or None
    if progname is None:
        progname = '<unknown>'
    if mismatch:
        raise VersionConstrained(progname)
    elif unversioned:
        raise VersionsUnknown(progname)
    else:
        raise ProgramNotFound(progname)

## -------------------------------------------------------[ data ... [

WINDOWS_ROOTS = ['%(windir)s',
                 '%(SystemRoot)s',
                 ]

## -------------------------------------------------------] ... data ]

## ----------------------------------------[ find_progs wrappers ... [

def find_PosixTool(progname,
                   indirs=0,
                   scanpath=1,
                   xroots=WINDOWS_ROOTS,
                   **kwargs):
    """
    use find_progs with appropriate defaults to find
    a generic Posix-compatible executable
    """
    if indirs == 0:
        indirs = PosixToolsDirs()
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      xroots=xroots,
                      **kwargs)

def find_svn(progname='svn',
             indirs=0,
             scanpath=1,
             **kwargs):
    """
    use find_progs with appropriate defaults to find an 'svn' executable
    """
    if indirs == 0:
        indirs = SubversionDirs()
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      **kwargs)

def find_tsvn(progname='TortoiseProc.exe',
              indirs=0,
              scanpath=1,
              **kwargs):
    """
    use find_progs with appropriate defaults to find a
    TortoiseSVN executable, by default: TortoiseProc.exe
    (will very likely succeed under Windows(tm) only)
    """
    if indirs == 0:
        indirs = ProgramDirs('TortoiseSVN/bin')
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      **kwargs)

def find_find(progname='find',
              **kwargs):
    """
    use find_progs with appropriate defaults to find a 'find' executable
    which does what a *x find is supposed to do
    """
    return find_PosixTool(progname=progname,
                          **kwargs)

def find_grep(progname='grep',
              indirs=0,
              scanpath=1,
              **kwargs):
    """
    use find_progs with appropriate defaults to find a 'grep' executable
    """
    if indirs == 0:
        indirs = PosixToolsDirs()
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      **kwargs)

def find_sed(progname='sed',
             **kwargs):
    """
    use find_progs with appropriate defaults to find a 'sed' executable
    """
    return find_PosixTool(progname=progname,
                          **kwargs)

def find_sort(progname='sort',
              **kwargs):
    """
    use find_progs with appropriate defaults to find a 'sort' executable
    which does what a *x sort is supposed to do
    """
    return find_PosixTool(progname=progname,
                          **kwargs)

def find_tar(progname='tar',
              **kwargs):
    """
    use find_progs with appropriate defaults to find a 'tar' executable

    NOTE: some tar implementations on Windows don't support filtering
          the output through gzip, bzip2, compress and the like; thus,
          it might be necessary to seek a bsdtar.exe as well.
          You can do this explicitly, of course, but there is no convenient
          automatic way do it automatically (yet).
    """
    return find_PosixTool(progname=progname,
                          **kwargs)

def find_uniq(progname='uniq',
              **kwargs):
    """
    use find_progs with appropriate defaults to find a 'uniq' executable
    """
    return find_PosixTool(progname=progname,
                          **kwargs)

def find_vim(progname='vim',
             indirs=0,
             scanpath=1,
             vdirs=0,
             **kwargs):
    """
    use find_progs with appropriate defaults to find a 'vim' executable
    """
    if indirs == 0:
        indirs = VimDirs()
    if vdirs == 0:
        vdirs = VimVDirs()
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      vdirs=vdirs,
                      **kwargs)

def find_gvim(progname='gvim',
              **kwargs):
    """
    look for gvim in the same places like (the console version) vim
    """
    return find_vim(progname=progname,
                    **kwargs)

def find_diff(progname='diff',
              indirs=0,
              scanpath=1,
              **kwargs):
    """
    use find_progs with appropriate defaults to find a 'diff' executable
    """
    if indirs == 0:
        indirs = DiffDirs()
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      **kwargs)

def find_ln(progname='ln',
            indirs=0,
            scanpath=1,
            **kwargs):
    """
    use find_progs with appropriate defaults to find an 'ln' executable
    which hopefully supports the important switches (-f, -s, ...)
    """
    if indirs == 0:
        indirs = PosixToolsDirs()
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      **kwargs)

def find_python(progname='python',
                indirs=0,
                scanpath=1,
                vdirs=0,
                **kwargs):
    """
    use find_progs with appropriate defaults to find a 'python' executable
    """
    if indirs == 0:
        indirs = PythonDirs()
    if vdirs == 0:
        vdirs = PythonVDirs()
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      vdirs=vdirs,
                      **kwargs)

def find_cvs(progname='cvs',
             indirs=0,
             scanpath=1,
             **kwargs):
    """
    use find_progs with appropriate defaults to find a 'cvs' executable
    """
    if indirs == 0:
        indirs = ProgramDirs('TortoiseCVS')
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      **kwargs)

# PuTTY suite (http://www.chiark.greenend.org.uk/~sgtatham/putty/):

def find_putty(progname='putty',
               indirs=0,
               scanpath=1,
               **kwargs):
    """
    use find_progs to find a PuTTY executable
    (an ssh client for Windows operating systems)
    """
    if indirs == 0:
        indirs = ProgramDirs('PuTTY')
    return find_progs(progname=progname,
                      indirs=indirs,
                      scanpath=scanpath,
                      **kwargs)

def find_pscp(progname='pscp',
              **kwargs):
    """
    use find_putty to find pscp (PuTTY's scp client)
    """
    return find_putty(progname=progname,
                      **kwargs)

def find_psftp(progname='psftp',
              **kwargs):
    """
    use find_putty to find psftp (PuTTY's secure FTP client)
    """
    return find_putty(progname=progname,
                      **kwargs)

def find_plink(progname='plink',
              **kwargs):
    """
    use find_putty to find plink (PuTTY's commandline connection utility)
    """
    return find_putty(progname=progname,
                      **kwargs)

def find_pageant(progname='pageant',
                 **kwargs):
    """
    use find_putty to find pageant (PuTTY's authentication agent)
    """
    return find_putty(progname=progname,
                      **kwargs)

def find_gpg(progname='gpg',
             indirs=0,
             **kwargs):
    """
    use find_progs to find gpg, the GNU Privacy Guard (tm)
    """
    if indirs == 0:
        indirs = ProgramDirs('Gnu/GnuPG/pub')
    return find_progs(progname=progname,
                      indirs=indirs,
                      **kwargs)

def find_xmllint(progname='xmllint',
                 indirs=0,
                 **kwargs):
    """
    use find_progs to find xmllint
    """
    if indirs == 0:
        indirs = ProgramDirs('Gnu/GnuPG')
    return find_progs(progname=progname,
                      indirs=indirs,
                      **kwargs)

## ----------------------------------------] ... find_progs wrappers ]

def dedicated_finders():
    """
    for demo: return the dedicated find_... functions
    """
    from string import lowercase
    blacklist = ('progs',)
    return sorted([s for s in [funcname[5:]
                               for funcname in globals().keys()
                               if funcname.startswith('find_')
                               ]
                   if s and s[0] in lowercase
                        and s not in blacklist])

def tuple_and_dict(name, arg):
    """
    Little helper for ToolsHub: Take a keyword argument to the constructor and
    return a 2-tuple of args tuple and kwargs dict.

    >>> def myfindfunc(): pass

    Sorry, the doctests involving myfindfunc don't work yet ...

    >X> tuple_and_dict('sed', (myfindfunc, {'indirs': '/my/tools/source'}))
    (('sed', myfindfunc), {'indirs': '/my/tools/source'})
    >X> tuple_and_dict('sed', (myfindfunc,))
    (('sed', myfindfunc), {})

    ... but these work:
    >>> tuple_and_dict('sed', ('alias', {'indirs': '/my/tools/source'}))
    (('sed', 'alias'), {'indirs': '/my/tools/source'})
    >>> tuple_and_dict('sed', {'indirs': '/my/tools/source'})
    (('sed',), {'indirs': '/my/tools/source'})

    Bogus input:
    >X> tuple_and_dict(1, {})
    """
    assert isinstance(name, basestring), \
            ('A keyword part of an argument will always be some string'
             ' (%(name)r)'
             ) % locals()
    args = [name]
    if isinstance(arg, dict):
        return (tuple(args), arg)
    kwargs = {}
    hasdict = False
    if isinstance(arg, basestring):
        raise ValueError('Currently no string values are supported'
                         ' (%(name)s=%(arg)r)'
                         % locals())
    for a in arg:
        if hasdict:
            raise ValueError('Surplus argument: %(a)r'
                         ' (%(name)s=%(arg)r)'
                         % locals())
        if isinstance(a, dict):
            kwargs = a
            hasdict = True
        else:
            args.append(a)
    return (tuple(args), kwargs)


## ---------------------------------------------[ ToolsHub class ... [

class ToolsHub(dict):
    """
    Provide a dictionary of tools.

    Allows to seek tools only when needed, and seek them only once.
    """
    def __init__(self, fallback=find_PosixTool, **kwargs):
        """
        Initialization:

          hub = ToolsHub()

        You may specify special functions to find
        certain programs, e.g.

          hub = ToolsHub(tar=[my_tar_finder,
                              {'scanpath': 0}],
                         sed={'indirs': ...})

        The ToolsHub will look for a find_sed function and fallback to
        find_PosixTool by default.
        """
        def interesting_name(s):
            return (s.startswith('__') and
                    s.endswith('__')
                    ) or 'get' in s or 'set' in s

        hintsmap = {}
        self.fallback = fallback

        # old version:
        for k, v in kwargs.items():
            if isinstance(v, dict):
                func, adic = self.smartie(k)
                adic.update(v)
            else:
                if isinstance(v, tuple):
                    v = list(v)
                else:
                    assert isinstance(v, list), \
                            'Only lists, tuples and dicts are ' \
                            'accepted (%r)' % (v,)
                try:
                    func = v.pop(0)
                except IndexError:
                    func, adic = self.smartie(k)
                if v:
                    bdic = v.pop(0)
                    assert isinstance(bdic, dict), \
                            'dictionary of arguments to function ' \
                            'expected (%r)' % (bdic,)
                    adic.update(bdic)
                    assert not v
            hintsmap[k] = (func, adic)
        self.hintsmap = hintsmap
        self.sequences = {}
        return
        # new version:
        self.hintsmap = hintsmap
        self.sequences = {}
        for k, v in kwargs.items():
            miniargs, minikwargs = tuple_and_dict(k, v)
            self.register(*miniargs, **minikwargs)

    def __iter__(self):
        return self.__iter__.__dict__()

    def __getitem__(self, key):
        if key not in self.__dict__:
            try:
                f, kwargs = self.hintsmap[key]
            except KeyError:
                f, kwargs = self.smartie(key)
            seq = f(**kwargs)
            if seq:
                self.sequences[key] = seq.__iter__()
                val = seq.next()
                self.__dict__.__setitem__(key, val)
                return val
            else:
                self.__dict__.__setitem__(key, None)
        try:
            return self.__dict__.__getitem__(key)
        except KeyError:
            return None

    def smartie(self, progname):
        # TODO: find better name ...
        """
        Return a tuple (function, kwargs): a function and a dictionary of
        keyword arguments.  If the module contains a function
        "find_<progname>", it is returned; otherwise, the fallback is used
        (find_PosixTool by default), and <progname> is given as the keyword
        argument "progname".
        """
        try:
            return (globals()['find_'+progname],
                    {})
        except KeyError:
            return (self.fallback,
                    {'progname': progname,
                     })

    def __str__(self):
        return str(self.__dict__)

## ---------------------------------------------] ... ToolsHub class ]

## ---------------------------------------[ directory generators ... [

class WinProgramDirs(object):
    """
    Executable class as a helper for the ProgramFiles etc. environment
    variables of recent Windows (tm) operating systems
    """
    def __init__(self, env=None):
        self.used = 0
        if env is None:
            env = environ
        self.env = environ

    def __reinit(self):
        if not self.used:
            self.reinit()
            self.used = 1

    def __call__(self, *args):
        self.__reinit()
        if not args:
            for d in self.dirs():
                yield d
        for a in args:
            for d in self.dirs():
                da = abspath(join(d, a))
                yield da

    def reinit(self, dic=None):
        if dic is not None:
            self.env = dic
        vals = []
        for k, v in self.env.items():
            ku = k.upper()
            if (k.startswith('ProgramFiles')
                or k.startswith('ProgramW')
                or ku.startswith('PROGRAMFILES')
                or ku.startswith('PROGRAMW')
                ):
                v2 = abspath(v)
                if v2 not in vals:
                    vals.append(v2)
        self._dirs = vals

    def dirs(self):
        self.__reinit()
        for d in self._dirs:
            yield d

# yields generator functions:
ProgramDirs = WinProgramDirs()

def PosixToolsDirs():
    """
    Generate the directories to search for POSIX tools without a special
    generator function; used by find_PosixTool, if the indirs argument is
    0 (the default)
    """
    for d in ProgramDirs('GnuWin32/bin'):
        yield d
    # http://sourceforge.net/projects/unxutils/
    for p in [
            r'%(SystemDrive)s\Tools\UnxUtils',
            r'%(SystemDrive)s\UnxUtils',
            r'%(SystemDrive)s',
            ]:
        yield join(p, r'usr\local\wbin')

    for d in [
            # Tobias Herp's system:
            r'%(SystemDrive)s\Compiler\MinGW\msys\1.0\bin',
            # MinGW doesn't like to be installed in a path containing blanks ...
            r'%(SystemDrive)s\MinGW\msys\1.0\bin',
            r'%(HomeDrive)s\MinGW\msys\1.0\bin',
            ]:
        yield d
    # just to be sure:
    for d in ProgramDirs('MinGW/msys/1.0/bin'):
        yield d
    for d in CygwinDirs():
        yield d

def CygwinDirs():
    # Cygwin programs are best used in a Cygwin environment,
    # where they are found in the usual *x directories,
    # and expect *x filename conventions on Windows systems
    for d in [
            r'%(SystemDrive)s\Cygwin',
            r'%(HomeDrive)s\Cygwin',
            ]:
        yield d
    for d in ProgramDirs('Cygwin'):
        yield d

def SubversionServerDirs():
    """
    Generate the directories to search for a svnserve executable;
    might contain svn excutables as well, and thus included by the
    SubversionDirs function
    """
    yield '%(VISUALSVN_SERVER)s/bin'

def SubversionDirs():
    """
    Generate the directories to search for a svn executable;
    used by find_svn, if the indirs argument is 0 (the default)
    """
    for d in ProgramDirs('TortoiseSVN/bin'):
        yield d
    # server distributions:
    for d in SubversionServerDirs():
        yield d
    for d in PosixToolsDirs():
        yield d

def VimDirs():
    """
    Generate the directories to search for a vim executable;
    used by find_vim, if the indirs argument is 0 (the default);
    see VimVDirs()
    """
    yield '%(VIM_EXE_DIR)s'
    for d in PosixToolsDirs():
        yield d

def VimVDirs():
    """
    Generate the directories to search for a vim executable;
    used by find_vim, if the vdirs argument is 0 (the default)
    """
    for wpd in ProgramDirs():
        yield join(wpd, 'Vim', 'vim*')

def DiffDirs():
    """
    Generate the directories to search for a diff executable;
    used by find_diff, if the indirs argument is 0 (the default).
    """
    yield '%(VIM_EXE_DIR)s'
    for d in PosixToolsDirs():
        yield d

def PythonDirs():
    """
    Generate directories to search for a python executable;
    used by find_python, if the indirs argument is 0 (the default).
    Note: More important is the vdirs argument which is used first;
    see PythonVDirs!
    """
    yield '%(PYTHONHOME)s'
    for d in PosixToolsDirs():
        yield d

def PythonVDirs():
    """
    Generate directories to search for a python executable;
    used by find_python, if the vdirs argument is 0 (the default).
    """
    def gen_parents():
        for d in ['%(SystemDrive)s\\',    # default! :-(
                  # don't clutter the root directory:
                  r'%(SystemDrive)s\Interpreter',
                  r'%(SystemDrive)s\Interpreters',
                  r'%(SystemDrive)s\Interpreter\Python',
                  r'%(SystemDrive)s\Interpreters\Python',
                  ]:
            yield d
        for d in ProgramDirs():
            yield d
    for wpd in gen_parents():
        yield join(wpd, 'python*')

## ---------------------------------------] ... directory generators ]

def _ffunc(topic, verbose=0, **kwargs):
    """
    demo:
    call the function for the given topic
    """
    from thebops.errors import err
    if topic == 'progs':
        err('use the --find-progs option instead')
        return
    elif topic == 'PosixTool':
        return
    try:
        f = globals()['find_'+topic]
        if verbose:
            print 'find_%s(%s):' \
                  % (topic, ('\n'+(6+len(topic))* ' '
                             ).join(['%s=%r' % tup
                                     for tup in fargs.items()]))
        else:
            print 'find_%s():' % topic
        for p in f(**kwargs):
            print '-', p
    except KeyError:
        err('sorry, no function find_%s'
            % topic)

if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=__version__)

