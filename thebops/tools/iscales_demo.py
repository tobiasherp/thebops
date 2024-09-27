# -*- coding: utf-8 -*- vim: sw=4 sts=4 ts=8 et ft=python
"""
Python module for image dimensions
"""
__version__ = (0,
               6, # CSS colour parsing moved to colours module
               2, # forked from iscales v0.6.2
               'rev-%s' % '$Rev: 962 $'[6:-2],
               )

from thebops.iscales import *
from thebops.optparse import OptionParser, OptionGroup
from thebops.opo import add_trace_option, DEBUG, \
        add_help_option, add_version_option
from thebops.base import progname
from thebops.errors import err

try:
    _
except NameError:
    def _(s): return s

def evaluate_options():
    p = OptionParser(usage='import %(prog)s | %%prog f1 f2 | %%prog --help'
                           % dict(prog=progname()),
                     add_help_option=0,
                     prog=progname())
    g = OptionGroup(p, _('Usage'))
    h = OptionGroup(p, 'hidden options')
    def cb_usage(*args):
        print (DOCSTRING + USAGE)#  % dict(prog=progname())
        exit(HELP_RC)

    g.add_option('--usage',
                 action='callback',
                 callback=cb_usage,
                 help=_('show a usage example'))
    p.add_option_group(g)

    g = OptionGroup(p, _('Known scales'))
    add_scale_helpers(g)
    p.add_option_group(g)

    g = OptionGroup(p, _('Everyday options'))
    add_help_option(g)
    add_version_option(g, version=__version__)
    p.add_option_group(g)

    add_trace_option(h)
    return p.parse_args()

def main():
    try:
        o, a = evaluate_options()
        DEBUG()
        if a:
            for x in a:
                try:
                    print x, '->', scales.getRatio(x)
                except KeyError:
                    print '%s: unknown' % x
        elif o:
            print __doc__
            print '(usually imported by other other Python scripts)'
            print 'Enter --help to get some help, or try some format specs.'
            exit(HELP_RC)
    except IscalesError, e:
        err(e)

if __name__ == '__main__':
    main()
