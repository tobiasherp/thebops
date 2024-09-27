#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Demo program for the thebops.likeix Python module
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           3,   #
           7,   # demo for likeix 0.3.7
           'rev-%s' % '$Rev: 1088 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

from os.path import pathsep, sep, join, abspath

from thebops.likeix import *
from thebops.optparse import OptionParser, OptionGroup
from thebops.opo import add_version_option, add_verbosity_options, \
        add_help_option, \
        add_trace_option, DEBUG
from thebops.errors import err, check_errors, info
from thebops.modinfo import main as modinfo

try: _
except NameError:
    def _(s): return s

search_opts = []

def evaluate_options():
    global search_opts
    p = OptionParser(description='find Posix-conforming tools,'
                     ' even on Win* systems'
                     ' (if installed, of course)',
                     usage='%prog [--options] [prog] [...]',
                     add_help_option=0)

    g = OptionGroup(p, "Demo options")
    g.add_option('--find',
                 action='append',
                 metavar=_('find,grep,...'),
                 help=_('use the special function find_find, find_grep '
                 'etc. to find the specified program'))
    g.add_option('--find-all',
                 action='store_true',
                 help=_('demonstrate all special find_... functions'))
    g.add_option('--find-progs',
                 action='append',
                 metavar=_('prog|cfg.ini|...'),
                 help=_('the program, script or config file to find, using'
                 ' the unwrapped find_progs function'))
    p.add_option_group(g)

    g = OptionGroup(p, "Options for find_... functions")
    h = OptionGroup(p, "hidden options")
    meta_dirseq = pathsep.join(('DIR1', 'DIR2', '...'))
    search_opts.append('parentsof')
    g.add_option('--parentsof',
                 action='store',
                 metavar=_('DIR'),
                 help=_('a directory which is searched first, and then all '
                 'of its parents.'))
    search_opts.append('indirs')
    g.add_option('--indirs',
                 action='store',
                 metavar=meta_dirseq,
                 help=_('some directories to be looked in next, separated by '
                 '"%(pathsep)s". Environment '
                 'variables can be given in Python syntax (e.g. '
                 '"%%(HOME)s%(sep)sbin")'
                 ) % globals())
    search_opts.append('scanpath')
    g.add_option('--scanpath',
                 action='store',
                 dest='scanpath',
                 metavar=_('y[es]|n[o]'),
                 help=_('whether to scan the PATH'
                 ' (see also --pathvar)'))
    search_opts.append('xroots')
    g.add_option('--xroots',
                 action='store',
                 metavar=meta_dirseq,
                 help=_('root directories which contain inappropriate objects'
                 ' which should be ignored (syntax like --indirs)'))
    search_opts.append('pathvar')
    g.add_option('--pathvar',
                 action='store',
                 metavar='PATH',
                 help=_('the PATH-like environment variable which contains '
                 'directories, separated by "%(pathsep)s"'
                 ) % globals())
    # not implemented yet by find_progs(), is it?
    search_opts.append('inroots')
    h.add_option('--inroots',
                 action='store',
                 metavar=meta_dirseq,
                 help=_('root directories to search'
                 ' (NOT IMPLEMENTED YET)'
                 '; syntax like --indirs and --xroots. Since this can take a '
                 'very long time, it is done last.'))
    p.add_option_group(g)

    g = OptionGroup(p, 'Everyday options')
    add_help_option(g)
    add_version_option(g, version=VERSION)
    add_verbosity_options(g)
    p.add_option_group(g)

    add_trace_option(h)
    return p.parse_args()


def main():
    option, args = evaluate_options()
    DEBUG()

    def makebool(raw):
        if raw is None:
            return raw
        if raw in ('0', '1'):
            return int(raw)
        if not raw:
            raise ValueError('(false/empty) %r not understood' % raw)
        s = raw.lower()
        if 'yes'.startswith(s):
            return 1
        if 'no'.startswith(s):
            return 0
        if 'true'.startswith(s):
            return 1
        if 'false'.startswith(s):
            return 0
        if s == 'on':
            return 1
        if s == 'off':
            return 0
        raise ValueError('boolean value "%s" not understood' % s)

    args_hint = 0
    if option.find_progs or option.find or option.find_all:
        fargs = dict()
        for k in search_opts:
            v = getattr(option, k)
            if v is None:
                continue
            if k in ('scanpath',
                     ):
                try:
                    fargs[k] = makebool(v)
                except ValueError, e:
                    err('--%(k)s: %(e)s' % locals())
            elif k in ('indirs', 'xroots',
                       'inroots',
                       ):
                fargs[k] = v.split(pathsep)
            else:
                fargs[k] = v
        args_hint = len(fargs) == 0
    else:
        boo = 0
        for k in search_opts:
            v = getattr(option, k)
            if v is not None:
                err('--%s: nothing to seek '
                    '(use one of --find, --find-all, --find-progs)' % k)
                boo = 1
        if not boo and not args:
            err('nothing to do')

    if option.find_progs:
        progs = []
        for tmp in option.find_progs:
            progs.extend(tmp.split(','))
        first = 1
        for p in progs:
            if option.verbose:
                if first:
                    first = 0
                else:
                    print
                print 'find_progs(%s):' \
                      % ',\n           '.join(['%s=%r' % tup
                                               for tup in [('progname', p),
                                                   ]+fargs.items()])
            found = 0
            for f in find_progs(progname=p, **fargs):
                print '-', f
                found += 1
            if found:
                args_hint = 0
            else:
                err('%s not found' % p)
        if args_hint:
            info('hint: try at least one of %s'
                 % ', '.join(['--%s' % o
                              for o in ('parentof', 'indirs', 'scanpath',
                                        # 'pathvar', 'xroots',
                                        # 'inroots',
                                        )]))
        if option.find or option.find_all:
            print

    topics = []
    if option.find:
        for s in option.find:
            topics.extend(s.split(','))
    if option.find_all:
        for k in dedicated_finders():
            if k in topics:
                continue
            else:
                topics.append(k)
    first = 1
    for t in topics:
        try:
            if first:
                first = 0
            elif option.verbose:
                print
            _ffunc = globals()['find_%s' % t]
        except KeyError:
            print t
        else:
            DEBUG()
            _ffunc(t, verbose=option.verbose, **fargs)

    if args:
        DEBUG()
        hub = ToolsHub()
        for a in args:
            print a, '->', hub[a]

    check_errors()

if __name__ == '__main__':
    main()

