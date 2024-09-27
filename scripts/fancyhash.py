#!/usr/bin/env python
# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Universelles Hash-Programm
"""

from __future__ import absolute_import
from __future__ import print_function
from six.moves import map
__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           2,   # konstantes Ausgabeintervall; Code aufgeräumt
           2,   # Verwendung von opo
           'rev-%s' % '$Rev: 938 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))
try:
    from thebops.enhopa import OptionParser, OptionGroup
except ImportError:
    from optparse import OptionParser, OptionGroup
try:
    _
except NameError:
    def dummy(s): return s
    _ = dummy

from os import stat
from hashlib import new, algorithms
from time import time
from fractions import gcd

from thebops.shtools import GlobFileGenerator, FilenameGenerator, get_console
from thebops.termwot import generate_caterpillars
from thebops.errors import err, check_errors
from thebops.opo import add_glob_options, add_help_option, add_version_option, \
        add_verbosity_options


p = OptionParser(usage='%prog [Options]',
                 add_help_option=False)
p.set_description(_('Compute cryptographic hashes, especially for large'
    ' files; during calculation, some screen output is displayed'
    ' (unless switched off via --quiet).'
    ))
g = OptionGroup(p, _("Available algorithms"))
g.add_option('--algorithm',
             action='store',
             metavar='|'.join(algorithms),
             help=_('the algorithm to use'
             '; also --%s etc.'
             #', unless given by filename'
             #' (--check/-c option)'
             ) % (algorithms[0],))
p.add_option_group(g)

g = OptionGroup(p, _("Argument evaluation"))
add_glob_options(g)
p.add_option_group(g)

h = OptionGroup(p, "hidden options")
for alg in algorithms:
    h.add_option('--'+alg,
                 action='store_const',
                 dest='algorithm',
                 const=alg)

g = OptionGroup(p, _("Screen output"))
add_verbosity_options(g, default=2)
g.add_option('--refresh-interval',
             dest='refresh_interval',
             action='store',
             type='float',
             default=0.1,
             metavar='0.1[seconds]',
             help=_('the time [seconds] between screen updates, '
             'default: %default'
             ' (unless disabled by --quiet)'
             ))
p.add_option_group(g)

g = OptionGroup(p, _("Everyday options"))
add_version_option(g, version=VERSION)
add_help_option(g)
p.add_option_group(g)

option, args = p.parse_args()

if not args:
    err(_('No files given'))

check_errors()

if option.algorithm is None:
    option.algorithm = 'md5'

digest_lengths = (
        # ermittelt aus hashlib:
        ('md5',       16),
        ('sha1',      20),
        ('sha224',    28),
        ('sha256',    32),
        ('sha384',    48),
        ('sha512',    64),
        # weitere:
        ('whirlpool', 64),
        )

def lcm(a, b):
    """
    least common multiple
    """
    if a and b:
        return abs(a * b) / gcd(a, b)
    else:
        return 0

INTERVAL = option.refresh_interval
algo = option.algorithm
HASH = None
start = None
HASH = new(algo)
chunk = lcm(HASH.block_size, 512 * 2**5)
console = get_console()

FANCYWIDTH = 20
if option.verbose >= 1:
    fancy = generate_caterpillars(width=FANCYWIDTH).__iter__()
else:
    fancy = None
gen = (option.glob
       and GlobFileGenerator
       or  FilenameGenerator
       )(*args).__iter__()
fo = None
try:
    ptime = start = time()
    first = 1
    while 1:
        if fo is None:
            try:
                fn = next(gen)
                total = stat(fn).st_size
                fo = open(fn, 'rb')
                HASH = new(algo)
                pos = 0.0
                eof = 0
            except StopIteration:
                break
        if fancy is not None:
            now = time()
            lap = now - ptime
            if first or (lap > INTERVAL):
                s = next(fancy)
                print(('\r%20s %s (%.2f%%)'
                         % (s, fn,
                            total and (pos*100/total) or 0
                            )), end=' ', file=console)
                ptime = now
                first = 0
        try:
            HASH.update(fo.read(chunk))
            pos += chunk
            if pos >= total:
                proz = 100
                eof = 1
            else:
                proz = pos / total
        except EOFError:
            proz = 100
            eof = 1
        if eof:
            print('\r%*s\r' % (FANCYWIDTH+10+len(fn),
                                           '',
                                           ), end=' ', file=console)
            print('%s *%s' % (HASH.hexdigest(), fn))
            fo.close()
            fo = None
except KeyboardInterrupt:
    print('\r%*s\r%s' % (FANCYWIDTH+10+len(fn),
                                   '',
                                   _('... aborted.')
                                   ), end=' ', file=console)
    raise SystemExit(99)

