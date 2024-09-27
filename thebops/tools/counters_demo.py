#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Demo program for the thebops.counters Python module
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           5, # counters_demo forked
           'rev-%s' % '$Rev: 961 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

from thebops.counters import *
from thebops.base import progname
from thebops.optparse import OptionParser, OptionGroup
from thebops.opo import add_help_option, add_version_option
        
try: _
except NameError:
    def _(s): return s

def evaluate_options():
    p = OptionParser(prog=progname(),
                     usage="from thebops.counters import count, error, "
                     'register_counters, all_counters',
                     add_help_option=0)
    p.set_description(_('A python module for all counting needs; '
                        'read the docstring for details'))

    g = OptionGroup(p, _('Demo options'))
    g.add_option('-r', '--recursive',
                 action='store_true',
                 help=_("every count('key:subkey') implies "
                 "count('error:key')"))
    g.add_option('--subtype-text',
                 metavar=_('STRING'),
                 action='store',
                 help=_('used for unregistered counter subtypes, '
                 'default: ", subtype: "'))
    p.add_option_group(g)

    g = OptionGroup(p, _('Everyday options'))
    add_help_option(g)
    add_version_option(g, version=VERSION)
    p.add_option_group(g)
    return p.parse_args()

def main():
    o, args = evaluate_options()
    if o.recursive:
        recursion(True)
        
    if o.subtype_text:
        TEXT_SUBTYPE = o.subtype_text

    register_counters({'char:digit': 'decimal digit[s]',
                       'char': 'characters',
                       ('char','alpha'): 'letter[s]',
                       ('char','alpha', 'vowel'): 'vowel[s]',
                       ('char','misc'): '[|misc. ]other character[s]',
                       })
    for s in args:
        for ch in s:
            if ch.isalpha():
                if ch in 'aeiouAEIOU':
                    count('char:alpha:vowel')
                elif ch in 'yY':
                    count('char:alpha:misc')
                elif ch.islower():
                    count('char:alpha:consonant:lower')
                else:
                    count('char:alpha:consonant:upper')
            elif ch.isdigit():
                count('char:digit:%s' % ch)
            else:
                count(('char', 'misc', ch))
    all_counters()

if __name__ == '__main__':
    main()
