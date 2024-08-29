#!/usr/bin/python
# -*- coding: utf-8 -*- vim: sw=4 ts=4 et si sts=4
u"""
Scan the PATH for the given file(s), or list it/check it for errors

see scanpath.txt (German) for TODO, ideas, remarks
"""
__version__ = (0,
               5, # --tail; Autoswitches
               1, # grouping of abbr. options
               'rev-%s' % '$Rev: 681 $'[6:-2],
               )
import sys, os
from thebops.errors import err, check_errors, progname, errline, fatal, warn, info
try:
    from thebops.enhopa import OptionParser, OptionGroup
except:
    from optparse import OptionParser, OptionGroup

_PN = progname()
WHICH = 0
if 'list' in _PN:
    LISTMODE = 1
elif 'scan' in _PN:
    LISTMODE = 0
elif 'which' in _PN:
    LISTMODE = 0
    WHICH = 1
elif 'l' in _PN:
    LISTMODE = 1
elif 's' in _PN:
    LISTMODE = 0
else:
    LISTMODE = None

COMMAND = None

import pdb
if 0:pdb.set_trace()
def isUnix():
    import os
    return 'x' in os.name
def pack2var(seq):
    """
    z. B. ['exe', 'com'] -> '.exe;.com'
    """
    from os.path import extsep, pathsep
    return pathsep.join([extsep+s for s in seq])

if isUnix():
    _os_dependent = {
                 'pathext': 'none by default',
                 'ext_var': None,
                 'extensions': (),
                 'def_curdir': False,
                 'def_curdir_0': ' (default on this platform)',
                 'def_curdir_1': '',
                 'pathsep': os.path.pathsep,
                 'extsep': os.path.extsep,
              }
else:
    extensions = ('.COM', '.EXE', '.CMD', '.BAT')
    ext_list = os.path.pathsep.join(extensions)
    _os_dependent = {
                 'pathext': _('tries the PATHEXT variable first; '
                              '%(ext_list)s by default'
                              ) % locals(),
                 'ext_var': 'PATHEXT',
                 'extensions': extensions,
                 'def_curdir': True,
                 'def_curdir_0': '',
                 'def_curdir_1': _(' (default on this platform)'),
                 'pathsep': os.path.pathsep,
                 'extsep': os.path.extsep,
              }
_os_dependent['ls'] = LISTMODE and 'list' or 'search'
if LISTMODE:
    _os_dependent['listmodetxt'] = _(' (activated via program name;'
                                     ' see scanpath and which as well)')
else:
    _os_dependent['listmodetxt'] = _(' (default, if program name contains'
                                     ' list or l, but not scan or s)')
try_pathext = not isUnix()

parser = OptionParser(usage=_('%prog [options]')
                            + (not LISTMODE and _(' file[s]') or ''),
                      version='%prog '+'.'.join(map(str, __version__)))
# print dir(parser)
parser.set_description(LISTMODE
                       and _('Lists the entries of the PATH variable'
                       ' (or another environment variable given by --varname)')
                       or _('Scans the/a PATH for the given file, finding ') +
                       (WHICH and _('the first matching entry by default')
                              or  _('*all* matching entries (not the first '
                                    'one only, which is the default beha'
                                    'viour of "which")')
                        ) + _(', and appending extensions as needed'
                              ' (according to system defaults)'))

group_ = OptionGroup(parser, _('Scan target options'))
group_.add_option('--varname',
                  default='PATH',
                  metavar=_('PATH'),
                  help=_('environment variable to use, default: %default'))
group_.add_option('--include-curdir', action='store_true',
                  default=_os_dependent['def_curdir'],
                  help='%(ls)s the current working directory first'
                  '%(def_curdir_1)s' % _os_dependent)
group_.add_option('--dont-include-curdir', action='store_false',
                  dest='include_curdir',
                  help='ignore the current working directory unless '
                  'explicitely included in PATH'
                  '%(def_curdir_0)s' % _os_dependent)
if not LISTMODE:\
group_.add_option('--extensions',
                  metavar=pack2var(('e1', 'e2')).upper(),
                  # default=_os_dependent['extensions'],
                  help='extensions to be appended when none is given '
                  '(%(pathext)s). Separate the items with %(pathsep)r, '
                  'and don\'t forget the leading %(extsep)rs' % _os_dependent)
if not LISTMODE:\
group_.add_option('--ext-varname',
                  default=_os_dependent['ext_var'],
                  metavar=_('PATHEXT'),
                  help=_('name of the extensions variable to use, default:'
                  ' %default'))
parser.add_option_group(group_)

if not WHICH:
    group_=OptionGroup(parser, _('Execution options'))
    group_.add_option('--list-path-only', '-L',
                      action='store_true',
                      default=LISTMODE,
                      dest='listpathonly',
                      help='don\'t seek particular files, list the path'
                      ' variable only%(listmodetxt)s' % _os_dependent)
    group_.add_option('--check-dirs', '-C', '-c',
                      action='store_true',
                      help=_('check directories in PATH for existence'
                      ))
    parser.add_option_group(group_)

def add_all_option(g):
    g.add_option('--all', '-a',
                 action='store_false',
                 dest='which',
                 help=_('Print all matches in PATH, not just the first'
                 ) + (not WHICH and _(' (default)')
                                or  ''))

if not LISTMODE:
    def list_full_path(fn):
        """
        simply display the fully qualified name
        """
        from os.path import abspath, isdir, sep
        if isdir(fn):
            if option.verbose:
                print abspath(fn)+sep
            return 0
        print abspath(fn)
        return 1

    def list_with_md5sum(fn):
        """
        show the md5 checksum and filename
        """
        from hashlib import md5
        from os.path import abspath, isdir
        if isdir(fn):
            return 0
        thisfile = open(fn, 'rb')
        dig = md5(thisfile.read()).hexdigest()
        thisfile.close()
        print '%s  %s' % (dig, abspath(fn))
        return 1

    def _edit_settings():
        global COMMAND, FILES, DUPES
        if option.editor:
            COMMAND = option.editor
        else:
            COMMAND = None
            for vn in ('VISUAL', 'EDITOR'):
                try:
                    COMMAND = os.environ[vn]
                    if COMMAND.strip():
                        break
                except KeyError:
                    pass
            if COMMAND is None or not COMMAND.strip():
                fatal(_('no editor specified; use --editor or '
                        'the VISUAL or EDITOR environment variable'))
        FILES = []
        DUPES = {}

    def gen_lines(fo):
        n = 0
        buf = None
        prev = None
        # import pdb; pdb.set_trace()
        for z in fo:
            if n is 1:
                yield buf.rstrip()
            prev, buf = buf, z
            if prev is not None:
                yield buf.rstrip()
            n += 1
        if n == 1 and not isinstance(fo, (tuple, list)):
            for z in buf.split('\n'):
                yield z.rstrip()

    def edit_files(fn):
        """
        edit, using the environment vars VISUAL and EDITOR
        """
        global COMMAND, FILES, DUPES
        from os.path import isdir, normpath, abspath, normcase
        if isdir(fn):
            return 0
        try:
            COMMAND, FILES
        except NameError:
            _edit_settings()
        if option.verbose:
            list_full_path(fn)
        name = normcase(normpath(abspath(fn)))
        try:
            DUPES[name]
        except KeyError:
            FILES.append(fn)
        return 1

    def _show_settings():
        global DUPES, TEXTUAL
        from os.path import normcase
        DUPES = dict()
        TEXTUAL = set(['.'+e
                       for e in normcase('txt TXT py BAT CMD bat cmd '
                           'rex REX pl '
                           'php php4 php5 '
                           'html xhtml xml'
                           'phtml xsl xslt'
                           ).split()])

    def show_files(fn):
        """
        show textual files
        """
        global DUPES, TEXTUAL
        from os.path import isdir, normpath, abspath, normcase, splitext
        if isdir(fn):
            return 0
        try:
            DUPES, TEXTUAL
        except NameError:
            _show_settings()
        name = normcase(normpath(abspath(fn)))
        try:
            DUPES[name]
        except KeyError:
            DUPES[name] = 1
            ext = splitext(name)[1]
            if ext in TEXTUAL:
                try:
                    fo = open(fn, 'r')
                    print '**', fn+':'
                    for z in gen_lines(fo):
                        print z
                    fo.close()
                except OSError, e:
                    print '!! %s: nicht lesbar (%s)' % (fn, e)
            else:
                print '?? %s: keine (bekannte) Textdatei-Erweiterung (%s)' \
                        % (fn, ext)
        return 1

    def file_heads(fn):
        """
        show textual files (like head commandline utility)
        """
        global DUPES, TEXTUAL
        from os.path import isdir, normpath, abspath, normcase, splitext
        if isdir(fn):
            return 0
        try:
            DUPES, TEXTUAL
        except NameError:
            _show_settings()
        name = normcase(normpath(abspath(fn)))
        try:
            DUPES[name]
        except KeyError:
            DUPES[name] = 1
            ext = splitext(name)[1]
            if ext in TEXTUAL:
                try:
                    fo = open(fn, 'r')
                    print '**', fn+':'
                    n = 1
                    for z in gen_lines(fo):
                        if n > option.lines:
                            break
                        print z
                        n += 1
                    fo.close()
                except OSError, e:
                    print '!! %s: nicht lesbar (%s)' % (fn, e)
            else:
                print '?? %s: keine (bekannte) Textdatei-Erweiterung (%s)' \
                        % (fn, ext)
        return 1

    def file_tails(fn):
        """
        show textual files (like tail commandline utility)
        """
        global DUPES, TEXTUAL
        from os.path import isdir, normpath, abspath, normcase, splitext
        if isdir(fn):
            return 0
        try:
            DUPES, TEXTUAL
        except NameError:
            _show_settings()
        name = normcase(normpath(abspath(fn)))
        try:
            DUPES[name]
        except KeyError:
            DUPES[name] = 1
            ext = splitext(name)[1]
            if ext in TEXTUAL:
                try:
                    fo = open(fn, 'r')
                    from collections import deque
                    deq = deque([None] * option.lines)
                    print '**', fn+':'
                    for z in gen_lines(fo):
                        deq.append(z)
                        deq.popleft()
                    fo.close()
                    for z in deq:
                        if z is not None:
                            print z
                except OSError, e:
                    print '!! %s: nicht lesbar (%s)' % (fn, e)
            else:
                print '?? %s: keine (bekannte) Textdatei-Erweiterung (%s)' \
                        % (fn, ext)
        return 1

    FILEFUNC = {}
    FILEFUNC['list'] = list_full_path
    FILEFUNC['md5'] = list_with_md5sum
    FILEFUNC['edit'] = edit_files
    FILEFUNC['show'] = show_files
    FILEFUNC['head'] = file_heads
    FILEFUNC['tail'] = file_tails
    action_keys = FILEFUNC.keys()
    action_keys.sort()

    group_ = OptionGroup(parser,
                         WHICH and _('Operation details')
                               or  _('For scan mode only (default; seek files)'
                                     ))
    group_.add_option('--action',
                      metavar='(%s)' % '|'.join(action_keys),
                      choices=action_keys,
                      help=_('an action to perform for each found file'
                      ' (see below); default: list (unless --editor'
                      ' specified)'))
    del action_keys
    if 0:\
    group_.add_option('--order',
                      metavar='file',
                      choices=('file','dir'), default='file',
                      help=_('results order (in case of more than one file to '
                      'seek): "file" (default; go through the files and seek '
                      'each one in the PATH) or "dir" (go through the PATH on'
                      'ce and look for every given file). Currently only the '
                      'default is implemented.'))
    group_.add_option('--which', '-1',
                      action='store_true',
                      default=WHICH,
                      help=_("'which' mode: stop after 1st match found"
                      '%s; negated by --all' % (WHICH and ' (default)' or '')))
    if WHICH:
        add_all_option(group_)
    group_.add_option('--editor',
                      action='store',
                      help=_('specify the editor to use (--action=edit, implied)'
                      '; by default, the VISUAL and EDITOR environment vari'
                      'ables are checked'))
    group_.add_option('--dry-run',
                      action='store_false',
                      default=True,
                      dest='doit',
                      help=_('don\'t execute (edit) command, just print it'))
    if 0:\
    group_.add_option('--regex',
                      action='store_true',
                      help=_('allow regular expressions for the file names specifi'
                      'cations'
                      ' (NOT YET IMPLEMENTED)'
                      '.'))
    group_.add_option('-n', '--lines',
                      action='store',
                      type='int',
                      # default=10,     # -> nachgelagert
                      help=_('number of lines (for --head and --tail), '
                      'default: 10. Negative Numbers '
                      'are allowed for --head (implying --tail), '
                      'and 0 auto-switches head, tail and show to list.'
                      ))
    parser.add_option_group(group_)

if not WHICH:
    group_ = OptionGroup(parser, _('For list mode only (-L)'))
    group_.add_option('--prefix',
                      action='store',
                      metavar=_('"%(no)2d "'),
                      default='',
                      help=_("string to prefix each line. Unless in '%(no)d' "
                      "or similar (pythonic dict comprehension of 'no'),"
                      " no '%' characters are allowed; default: empty."
                      ' To use blanks, you can enclose the whole option in quotes'))
    group_.add_option('--number', '-N',
                      action='store_const',
                      const='%(no)2d) ',
                      dest='prefix',
                      help=_("Set --prefix to '%(no)2d) ', which causes the output"
                      " lines to be prefixed by ' 1) ', ' 2) ' and so on"
                      '. NOTE: When used with -c, invalid entries are '
                      'numbered, too; specify -cv to see them'))
    parser.add_option_group(group_)

if not WHICH:
    group_ = OptionGroup(parser, _('Options from GNU which'))
    if 0:
        group_.add_option('--skip-dot',
                          action='store_true',
                          help=_('Skip directories in PATH that start with a dot'
                          ' (NOT YET IMPLEMENTED)'))
        group_.add_option('--skip-tilde',
                          action='store_true',
                          help=_('Skip directories in PATH that start with a tilde'
                          ' (NOT YET IMPLEMENTED)'))
        group_.add_option('--show-dot',
                          action='store_true',
                          help=_('Don\'t expand a dot to current directory in output'
                          ' (NOT YET IMPLEMENTED)'))
        group_.add_option('--show-tilde',
                          action='store_true',
                          help=_('Output a tilde for HOME directory for non-root'
                          ' (NOT YET IMPLEMENTED)'))
        group_.add_option('--tty-only',
                          action='store_true',
                          help=_('Stop processing options on the right if not on tty'
                          ' (NOT YET IMPLEMENTED)'))
    if not LISTMODE:
        add_all_option(group_)
        parser.add_option_group(group_)

group_ = OptionGroup(parser, _('Abbreviations for path variables'))
group_.add_option('--path',
                  action='store_const',
                  dest='varname',
                  const='PATH',
                  help=_('abbr. for --varname=PATH'))
group_.add_option('--pypath',
                  action='store_const',
                  dest='varname',
                  const='PYTHONPATH',
                  help=_('abbr. for --varname=PYTHONPATH'))
group_.add_option('--classpath',
                  action='store_const',
                  dest='varname',
                  const='CLASSPATH',
                  help=_('abbr. for --varname=CLASSPATH')
                  + (not LISTMODE
                      and _(' (sorry, no searching of .jar archives [yet])')
                      or  ''))
group_.add_option('--ldlib',
                  action='store_const',
                  dest='varname',
                  const='LD_LIBRARY_PATH',
                  help=_('abbr. for --varname=LD_LIBRARY_PATH'))
if not LISTMODE:
    parser.add_option_group(group_)
    group_ = OptionGroup(parser, _('Abbreviations for commands'))
    group_.add_option('--list',
                      action='store_const',
                      dest='action',
                      const='list',
                      help=_('abbr. for --action=list'
                      ' (show filenames only)'))
    group_.add_option('--show',
                      action='store_const',
                      dest='action',
                      const='show',
                      help=_('abbr. for --action=show'
                      ' (Dateinamen und, sofern textuell, den Inhalt zur Stan'
                      'dardausgabe ausgeben)'))
    group_.add_option('--head',
                      action='store_const',
                      dest='action',
                      const='head',
                      help=_('abbr. for --action=head'
                      ' (wie Shell-Tool "head": nur erste --lines Zeilen, Stan'
                      'dardwert: 10; negative Werte schalten auf --tail um)'
                      ))
    group_.add_option('--tail',
                      action='store_const',
                      dest='action',
                      const='tail',
                      help=_('abbr. for --action=tail'
                      ' (wie Shell-Tool "tail": nur letzte --lines Zeilen)'
                      ))
    group_.add_option('--md5',
                      action='store_const',
                      dest='action',
                      const='md5',
                      help=_('abbr. for --action=md5'
                      ' (show md5 checksums and filenames)'))
    group_.add_option('--edit',
                      action='store_const',
                      dest='action',
                      const='edit',
                      help=_('abbr. for --action=edit'
                      '; see --editor'))
    group_.add_option('--self',
                      action='store_true',
                      help=_('tell the program to seek itself'))
parser.add_option_group(group_)

parser.add_option('--verbose', '-v',
                  action='count',
                  help=_('be verbose (-vv: even more verbose)'))
try:
    parser.set_collecting_group()
except AttributeError:
    pass
option, args = parser.parse_args()
option.order = 'file'
if WHICH:
    option.listpathonly = 0

errors = 0
if option.self:
    args.append(_PN)
if option.listpathonly:
    if option.action is not None:
        warn('--list-path-only: action ("%s") is ignored' % option.action)
    if args:
        err('--list-path-only supports no further arguments')
elif not args:
    err('nothing given to be seeked')
if option.lines is None:
    if option.action in ('head', 'tail'):
        option.lines = 10
    elif option.action in ('show',):
        warn('--action=%s: --lines value is ignored (%r); use --head or --tail'
             % (option.action, option.lines))
elif option.listpathonly:
    if option.verbose:
        warn('--list-path-only: --lines=%d are ignored' % option.lines)
elif option.lines == 0:
    if option.action in ('head', 'tail', 'show'):
        if option.verbose:
            info('--%s: --lines=%d, auto-switching to --list'
                 % (option.action, option.lines))
        option.action = 'list'
    elif option.verbose > (option.action == 'list'):
        warn('--action=%s: --lines=%d are ignored' % option.lines)
if option.lines < 0:
    if option.action == 'head':
        option.action = 'tail'
        if option.verbose:
            info('--head: negative --lines value (%r), auto-switching to --tail'
                 % option.lines)
        option.lines *= -1
    elif option.action == 'tail':
        (option.listpathonly and warn or err
         )('--tail: lines value < 0 (given: %r) not supported'
           % option.lines)

check_errors()

if 0:pdb.set_trace()
try:
    if option.extensions is None:
        if try_pathext and option.ext_varname \
                       and os.environ.has_key(option.ext_varname):
            option.extensions = os.environ[option.ext_varname].lower().split(os.path.pathsep)
        else:
            option.extensions = ()
    elif not option.extensions:
        option.extensions = ()
    elif isinstance(option.extensions, str):
        option.extensions = option.extensions.split(os.path.pathsep)
except AttributeError:
    option.extensions = ()

try:
    if option.action is None:
        if option.editor:
            option.action = 'edit'
        else:
            option.action = 'list'
    elif option.action == 'edit':
        pass
    elif option.editor:
        warn('other action specified; --editor ignored')
except AttributeError:
    pass

def ext_info():
    if option.verbose:
        if option.extensions:
            errline('Extensions: '+ os.path.pathsep.join(option.extensions))
        else:
            errline('No extensions!')

def seek_single_file(f):
    """
    seek the given file in the PATH
    """
    if option.verbose:
        errline('Seeking %s...' % f)
    if 0:
        import pdb
        pdb.set_trace()
    if option.extensions:
        fext = os.path.split(f)[1]
        if not fext:
            a_ext = 1
        elif fext in option.extensions:
            a_ext = 0
        else:
            a_ext = 1
    else:
        a_ext = 0
    dirs = os.environ[option.varname].split(os.path.pathsep)
    if option.include_curdir:
        dirs.insert(0, os.path.curdir)
    lfound = 0
    for d in dirs:
        if 0:
            import pdb
            pdb.set_trace()
        if a_ext:
            for e in option.extensions:
                fi = os.path.join(d, f+e)
                if os.path.exists(fi):
                    if FILEFUNC[option.action](fi):
                        lfound = 1
                        if option.which:
                            return lfound
        fi = os.path.join(d, f)
        if os.path.exists(fi):
            if FILEFUNC[option.action](fi):
                lfound = 1
                if option.which:
                    return lfound
    return lfound

def seek_files(liz):
    """
    seek the given files in the PATH by calling seek_single_file();
    for each file iterate the PATH anew
    """
    found = 0
    notfound = 0
    ext_info()
    for fn in liz:
        if seek_single_file(fn):
            found += 1
        else:
            notfound += 1
            err('%s not found in %s' % (fn, option.varname))

    if notfound and option.verbose > 1:
        errline('%s is:' % option.varname)
        for d in os.environ[option.varname].split(os.path.pathsep):
            errline(' - '+d)
    if not found:
        check_errors()
    else:
        if COMMAND:
            def mask(fn):
                import string
                from os.path import normpath
                for ch in '<|>"':
                    if ch in fn:
                        raise RuntimeError('invalid character in filename'
                                ' (%r, %r)' % (ch, fn))
                for ch in string.whitespace:
                    if ch in fn:
                        return '"%s"' % normpath(fn)
                return normpath(fn)
            cmd = ' '.join([COMMAND,]+
                           [mask(fn) for fn in FILES])
            from os import system
            if option.verbose or not option.doit:
                print cmd
            if option.doit:
                rc = system(cmd)
                if rc:
                    fatal('return code is %d' % rc)
        sys.exit(0)

def getpathdirs():
    u"""
    Gib die in option.varname verzeichneten Verzeichnisse zurueck
    """
    try:
        dirs = os.environ[option.varname].split(os.path.pathsep)
    except:
        err('%s is not defined!' % option.varname)
        dirs = []
    if option.include_curdir:
        dirs.insert(0, os.path.curdir)
    return dirs

def verbose_status():
    return option.verbose > 1

def getpathdirs_checking():
    """
    Verwendung:
    for isdir, status, dirname, suffix in getpathdirs_checking:
        print status, dirname+suffix
    """
    from os.path import isdir, exists, normpath, sep
    vinfo = (verbose_status()
             and ('\t(not found!)',
                  '\t(not a directory!)')
             or ('', ''))

    for d in getpathdirs():
        if isdir(d):
            yield 1, 'OK:  ', normpath(d), sep
        elif exists(d):
            yield 0, 'Err2:', normpath(d), vinfo[1]
        else:
            yield 0, 'Err1:', normpath(d), vinfo[0]


def listpath_checking():
    """
    Verzeichnisse ausgeben, sofern gefunden
    """
    from os.path import isdir, exists, normpath, sep
    for d in getpathdirs():
        if isdir(d):
            print 'OK:', normpath(d)+sep
        elif exists(d):
            print '(2)', normpath(d)+'\t(not a directory!)'
        else:
            print '(1)', normpath(d)+'\t(not found!)'

def listpath():
    """
    Verzeichnisse ausgeben
    """
    for d in getpathdirs():
        print d

check_errors()

if option.listpathonly:
    import pdb
    # pdb.set_trace()
    mask = None
    if option.check_dirs:
        if option.verbose:
            mask = '%(status)s %(dirname)s%(suffix)s'
        else:
            mask = '%(dirname)s%(suffix)s'
            if 0:
                from os.path import isdir
                for d in filter(isdir, getpathdirs()):
                    print d
    if option.prefix:
        mask = mask or '%(dirname)s'
        mask = option.prefix + mask
    if mask:
        no = 0
        skipped = 0
        invalid = 0
        try:
            if option.check_dirs:
                for isdir, status, dirname, suffix in getpathdirs_checking():
                    no += 1
                    if isdir:
                        print mask % locals()
                    elif option.verbose:
                        print mask % locals()
                        invalid += 1
                    else:
                        skipped += 1
                    # pdb.set_trace()
                if skipped:
                    warn('%d entr%s skipped'
                         % (skipped,
                            skipped > 1 and 'ies' or 'y'))
                if invalid:
                    info('%d invalid entr%s'
                         % (invalid,
                            invalid > 1 and 'ies' or 'y'))
            else:
                for dirname in getpathdirs():
                    no += 1
                    print mask % locals()
        except KeyError, e:
            fatal('--prefix %r: Variable %r unknown' % (option.prefix, e.args[0]))
    else:
        listpath()
elif option.order == 'file':
    seek_files(args)
elif option.order == 'dir':
    raise NotImplementedError('search_dirs')

