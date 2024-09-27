#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Demo program for the thebops.opo Python module
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           3,   # forked from opo.py 0.3.1
           6,   # add_backup_options refactored
           'rev-%s' % '$Rev: 918 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

from thebops.opo import *
import thebops.opo      # for add_doctest_option
from thebops.optparse import OptionParser, OptionGroup
from thebops.base import progname
from thebops.shtools import mapfunc
from thebops.errors import err, info, check_errors

from pprint import pprint
from collections import defaultdict

try: _
except NameError:
    def _(s): return s

def demo_debug_args(tup):
    res = []
    for item in tup:
        try:
            res.append(int(item))
        except ValueError:
            res.append(item)
    if res:
        info(_('Arguments tuple converted to %s'
               ' as DEBUG(...) demo input'
               ) % res)
    return tuple(res)

DEFAULT_VERBOSITY = 2
def parse_args():
    p = OptionParser(description=_('A Python module which provides useful '
                     'optparse options'),
                     prog=progname(),
                     usage='\n    '.join(('',
                         'from optparse import OptionParser',
                         'from thebops.opo import add_date_options, '
                                          'add_version_option',
                         'p = OptionParser()',
                         'add_date_options(p)',
                         'add_version_option(p, version=(1, 0))',
                         'o, a = p.parse_args()',
                         'print o.date',
                         )),
                     add_help_option=0)

    g = OptionGroup(p, _("Demo for date options"))
    h = OptionGroup(p, 'hidden options')
    add_date_options(g, metavar='d.[m.[y]]')
    p.add_option_group(g)

    g = OptionGroup(p, _("Demo for verbosity options"))
    add_verbosity_options(g, default=DEFAULT_VERBOSITY)
    p.add_option_group(g)

    g = OptionGroup(p, _("Demo for flags and lists"))
    bitfunc = mapfunc((
            [0,   ''],
            [1,   'msg', 'msgs', 'messages'],
            [2,   'path'],
            [4,   'author', 'authors'],
            [8,   'rev', 'revs', 'revisions'],
            [32,  'bugs'],
            [128, 'date'],
            [256, 'range', 'date-range'],
            [511, 'all', 'any'],
            ))
    g.add_option('--search',
                 action='callback',
                 dest='flags',
                 metavar=bitfunc.metavar(),
                 type='string',    # ?!
                 callback=cb_flags,
                 callback_kwargs={'f': bitfunc},
                 help=_("Demo for flags; every word is translated to a number,"
                 ' most likely a power of two; the example is taken from'
                 ' tsvn (pip install tsvn; tsvn help log)'
                 ))
    extensions_mapper = mapfunc((
             ('/ignorespaces', 'space', 'space-change'),
             ('/ignoreallspaces', 'all-spaces'),
             ('/ignoreeol', 'eol', 'eol-style', 'eols'),
            ),
            cls=str)
    g.add_option('--ignore',
                 action='callback',
                 metavar=extensions_mapper.metavar(),
                 callback=cb_list,
                 type='string',
                 callback_kwargs={'f': extensions_mapper},
                 help=('Translate a list of handy short words to a list'
                 ' of (ugly, and more difficult) commandline options'
                 ' which are e.g. forwarded to an external tool'
                 ))
    p.add_option_group(g)

    g = OptionGroup(p, _("Options with optional values"))
    add_optval_option(g, '--option',
                      empty=_('EMPTY'),
                      default=_('MISSING'),
                      metavar=_('VALUE'),
                      help=_('"EMPTY" if given without a value. Note: '
                      '--option or '
                      '--option=VALUE will work; --option VALUE will *not*! '
                      'Same is true for -oVALUE (will work) and '
                      '-o VALUE (won\'t)'))
    add_optval_option(h, '-o',
                      empty=_('EMPTY'),
                      dest='option')
    add_backup_options(g, hidden_group=h)
    p.add_option_group(g)

    g = OptionGroup(p, _("Ordinary optparse numeric options"))
    g.add_option('--integer',
                 type='int',
                 metavar='NN')
    g.add_option('--long',
                 type='long',
                 metavar='NNNNNNNN')
    g.add_option('--float',
                 type='float',
                 metavar='NN.MM')
    g.add_option('--complex',
                 type='complex',
                 metavar='[NN+]MMj')
    p.add_option_group(g)

    g = OptionGroup(p, _("Populate a dictionary"))
    g.add_option('--default',
                 type='int',
                 metavar='NN',
                 help=_('The default value'
                 ))
    g.add_option('--map',
                 action='callback',
                 type='string',
                 callback=cb_fill_dict,
                 callback_kwargs={'splitter':
                     make_splitter(make_inttuple_factory(':'))},
                 metavar='i:j[,...]',
                 help=_('specify one or more pairs of integer numbers'
                 ))
    g.add_option('--map-to-1',
                 action='callback',
                 type='string',
                 dest='map',
                 callback=cb_fill_dict,
                 callback_kwargs={'splitter':
                     make_splitter(make_int_and_const_factory(1))},
                 metavar='i[,...]',
                 help=_('A shortcut for --map=i:1[,...]; '
                 'see --map-to-2 ... --map-to-9 as well'))
    for i in range(2, 10):
        h.add_option('--map-to-%d' % i,
                     action='callback',
                     type='string',
                     dest='map',
                     callback=cb_fill_dict,
                     callback_kwargs={'splitter':
                         make_splitter(make_int_and_const_factory(i),
                                       ',')}
                     )
    p.add_option_group(g)

    g = OptionGroup(p, _("Development options"))
    add_trace_option(g)
    add_doctest_option(g, module=thebops.opo,
                       verbose_add=-DEFAULT_VERBOSITY)
    p.add_option_group(g)

    g = OptionGroup(p, _("Everyday options"))
    add_help_option(g)
    add_version_option(g, version=VERSION)
    p.add_option_group(g)
    return p.parse_args()

def main():
    o, a = parse_args()
    DEBUG()

    if not o.trace:
        for arg in a:
            err(_('Argument %r ignored') % arg)
    DEBUG(0, *demo_debug_args(a))
    if o.date:
        info(_('Date: %s') % str(o.date[:3]))
    info(_('Verbosity: %r') % o.verbose)
    if o.verbose or o.option:
        info(_('With or without value: %r') % o.option)
    if o.verbose or o.backup is not None:
        info(_('Backup type: %r') % o.backup_type)
        info(_('Backup suffix: %r') % o.backup_suffix)
        info(_('Perform backup: %r') % o.backup)
    if o.flags is not None:
        info(_('Flags demo: 0x%x') % o.flags)
    tmp = 0
    for a in 'integer long float complex'.split():
        tmpv = getattr(o, a)
        if tmpv is not None:
            tmp = 1
            break
    if tmp:
        info(_('Numerical optparse options:'))
        def option_and_value(a):
            v = getattr(o, a)
            if v is not None:
                info('  --%s\t--> %r' % (a, v))
        for a in 'integer long float complex'.split():
            option_and_value(a)

    if o.default or o.map:
        info(_('Populate a dictionary:'))
        if o.default is not None:
            dic = defaultdict(gimme(o.default))
        else:
            dic = {}
        if o.map:
            dic.update(o.map)
        pprint(dic)
    check_errors()

if __name__ == '__main__':
    main()

