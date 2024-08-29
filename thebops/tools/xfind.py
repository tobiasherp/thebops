"""
use *x find on Windows(tm) systems where an incompatible program is part of the system
"""

VERSION = (0,
           1,   # first version
           'rev-%s' % '$Rev: 959 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

from sys import argv
from getopt import gnu_getopt, GetoptError
from thebops.likeix import ToolsHub
from thebops.base import progname, RC_ABORT
from thebops.errors import error, warn, info
from thebops.misc1 import make_valuesClass
from textwrap import wrap

try:
    _
except NameError:
    def _(s, *args):
        return s
hub = ToolsHub()
Values = make_valuesClass(('help', 'version',
                           'nothing',
                           ),
                          classname='Values')
try:
    from subprocess import Popen
except ImportError:
    # TODO: use old module instead 
    raise


HELP_ARGS = ('-help', '--help', '-h')
VERSION_ARGS = ('-version', '--version', '-V')

# print help when no commandline args are given at all?
HELP_WHEN_EMPTY = True
SKIP_INTRO = {'-exec': ';',
              }

def parse_for_help_or_version(seq):
    """
    find doesn't use POSIX compatible commandline parsing
    but its "own flavour".
    This function tries its best to gracefully extract
    commandline options to get help or version info.
    """
    o = Values()
    if not seq:
        o.nothing = True
        return o
    skip = False
    skipper = None
    skip_end = None
    for s in seq:
        if skip:
            if s == skip_end:
                skip = False
            continue
        elif s in SKIP_INTRO:
            skipper = s
            skip_end = SKIP_INTRO[skipper]
        if s in HELP_ARGS:
            o.help = True
            return o
        if s in VERSION_ARGS:
            o.version = True
            return o
        try:
            liz = ['<ignored>', s]
            preparsed = gnu_getopt(liz, 'hV')
        except GetoptError:
            # this is very common!
            pass
        else:
            for tup in preparsed[0]:
                if tup == ('-h', ''):
                    o.help = True
                    return o
                if tup == ('-V', ''):
                    o.version = True
                    return o
    return o

def info_dict():
    """
    return a dict for string output
    """
    return {'prog': progname(),
            'version': '.'.join(map(str, VERSION)),
            }

def show_help(myhelp=True, findhelp=True):
    """
    Print the help text for this program and/or for the 
    """
    print _('%(prog)s v%(version)s: call *x find program'
            ) % info_dict()
    print
    if myhelp:
        width = 79
        progname = 'find'
        for txt in (
                ""'Find a "%(progname)s" program like those commonly found '
                'on *X systems, and call it.',
                ""'This script tries its best to support the user '
                'by recognizing the usual --help options (which '
                '"%(progname)s" usually does not), so you can simply '
                'append them to the end of your command line '
                'for quick help.',
                ):
            for line in wrap(_(txt) % locals(), width):
                print line
        print
    if findhelp:
        call_find(['-help'])

def show_version():
    print _('%(prog)s v%(version)s'
            ) % info_dict()
    if hub['find']:
        print '%(find)s: ' % hub,
    call_find(['-version'])

def call_find(args):
    findprog = hub['find']
    if findprog is None:
        error('Sorry, no suitable find executable found')
        return
    cmd = [findprog]
    cmd.extend(args)
    try:
        rc = Popen(cmd).wait()
        raise SystemExit(rc)
    except KeyboardInterrupt:
        info(_('... aborted.\n'))
        raise SystemExit(RC_ABORT)

def main():
    o = parse_for_help_or_version(argv[1:])
    if o.help:
        show_help()
    elif o.version:
        show_version()
    elif o.nothing and HELP_WHEN_EMPTY:
        progname = 'find'
        warn(_('The original %(progname)s won\'t display '
               'help when called without arguments!'
               ) % locals())
        show_help(findhelp=False)
    else:
        call_find(argv[1:])

if __name__ == '__main__':
    main()
