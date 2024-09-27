#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Demo program for the thebops.optparse Python module
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (1,
           6,   # forked from opo_demo.py
           5,   # demo for decrease action
           1,   #  ... and cb_decrease
           'rev-%s' % '$Rev: 918 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

from thebops.optparse import *
from thebops.opo import cb_decrease
from thebops.base import progname
from thebops.errors import err, info, check_errors

try: _
except NameError:
    def _(s): return s

def main():
    p = OptionParser(description=_('An optparse Python module how I like '
                     'it to be (or at least on the way). '
                     'See also thebops.opo, or opo_demo.'
                     ),
                     prog=progname(),
                     usage='\n    '.join(('',
                         'from thebops.optparse import OptionParser',
                         'p = OptionParser()',
                         '...',
                         'o, a = p.parse_args()',
                         )),
                     add_help_option=0)

    g = OptionGroup(p, _("Demo for increasing/decreasing options"))
    g.add_option('-v',
                 action='count',
                 dest='verbose',
                 default=2,
                 help=_('be verbose (-vv: even more verbose)'
                 ', default: %default (standard action: "count")'
                 ))
    g.add_option('-q',
                 action='decrease',
                 dest='verbose',
                 help=_('be quiet (-qq: even quieter)'
                 '. Decreases verbosity'
                 ' (thebops.optparse 1.6.5+ action: "decrease")'
                 ))
    g.add_option('-Q',
                 action='callback',
                 callback=cb_decrease,
                 dest='verbose',
                 help=_('be quiet (-QQ: even quieter)'
                 '. Decreases verbosity, using the cb_decrease callback'
                 ' function from thebops.opo, which won\'t decrease the'
                 ' value below the default floor value of 0.'
                 ))
    p.add_option_group(g)

    g = OptionGroup(p, _("Ordinary optparse numeric options"))
    g.add_option('--integer',
                 type='int',
                 metavar='NN',
                 help=_('this recognizes prefixes to adjust the base:'
                 ' 0 -> octal (base 8), 0x -> hexadecimal (16), and'
                 ' 0b -> binary (base 2)'))
    g.add_option('--long',
                 type='long',
                 metavar='NNNNNNNN',
                 help=_('like --integer, but creates a long integer'
                 ' (of unlimited size)'))
    g.add_option('--float',
                 type='float',
                 metavar='NN.MM')
    g.add_option('--complex',
                 type='complex',
                 metavar='[NN+]MMj')
    p.add_option_group(g)

    g = OptionGroup(p, _("Everyday options"))
    g.add_help_option()
    p.version='thebops.optparse '+__version__
    g.add_version_option()
    p.add_option_group(g)

    o, a = p.parse_args()

    info(_('Verbosity: %r') % o.verbose)
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
    check_errors()

if __name__ == '__main__':
    main()

