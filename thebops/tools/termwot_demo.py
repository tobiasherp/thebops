﻿#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79

from time import sleep as _sleep

from thebops.termwot import *
from thebops.shtools import Rotor, one_of, OptionCheckError, ToolsValueError
from thebops.base import progname
from thebops.errors import info, error, check_errors
from thebops.optparse import OptionParser, OptionGroup
from thebops.opo import add_trace_option, DEBUG, \
        add_help_option, add_version_option

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           5,	# extracted from shtools_demo.py v0.4.2.2
           1,   # --number
           'rev-%s' % '$Rev: 971 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

try: _
except NameError:
    def _(s): return s

DEFAULT_CHARS = '.: '
def make_parser():
    p = OptionParser(add_help_option=0,
                     prog=progname())
    p.set_description(_('Demo for the thebops.termwot Python module: '
        '"Tobias Herp\'s terminal waste of time"'))
    h = OptionGroup(p, 'hidden options')

    g = OptionGroup(p, _('Fancy rotors'))
    g.add_option('--random-chars',
                 action='store_true',
                 help=_('instead of cycling through a sequence, print '
                 'fixed numbers of randomly chosen characters'
                 ' (demo for RandomChars()())'))
    g.add_option('--rotor-chars',
                 action='store',
                 type='string',
                 metavar='abc',
                 help=_('characters for the "rotor", e.g. "%(DEFAULT_CHARS)s"'
                 ' (default)'
                 ) % globals())
    p.add_option_group(g)

    g = OptionGroup(p, _('Breeding station '
                         '(generate snakes and caterpillars)'))
    g.add_option('--snake',
                 action='store_true',
                 help=_('a funny example of what is possible with '
                 "shtools's rotors"))
    g.add_option('--snakes',
                 action='store_true',
                 help=_('generate two snakes'))
    g.add_option('--caterpillar',
                 action='store_true',
                 help=_('generate a caterpillar'))
    g.add_option('--caterpillars',
                 action='store_true',
                 help=_('generate two caterpillars'))
    p.add_option_group(g)

    g = OptionGroup(p, _('Adjust the generators'))
    g.add_option('--width', '-w',
                 type='int',
                 metavar='NN',
                 help=_('width of crawling, wiggling ... area; '
                 'default depends on the specific generator'))
    h.add_option('--number', '-n',
                 type='int',
                 default=2,
                 metavar='2',
                 help=_('number of animals at a time'
                 ' (if supported by the generator)'
                 '; default: %default'
                 ))
    g.add_option('--period', '-p',
                 type='int',
                 metavar='NN',
                 help=_('for caterpillars (which crawl rightwards only); '
                 'should be larger than the maximum length, and defaults '
                 'to the area width'))
    g.add_option('--crawl-delay',
                 type='float',
                 metavar='0.2',
                 dest='crawl_delay',
                 help=_('delay in seconds for the movement of a single'
                 ' animal (use decimal points);'
                 ' will be divided by the number of animals'
                 ' e.g. for --caterpillars'))
    g.add_option('--delay',
                 type='float',
                 metavar='0.3',
                 default=0.3,
                 help=_('delay in seconds for common iterations'))
    p.add_option_group(g)

    g = OptionGroup(p, _('Misc. other functions'))
    g.add_option('--sleep',
                 action='store',
                 type='int',
                 metavar='5',
                 help=_('demonstrate the sleep function; specify a'
                 ' whole number, e.g. 5'))
    p.add_option_group(g)

    g = OptionGroup(p, _('Everyday options'))
    add_help_option(g)
    add_version_option(g, version=VERSION)
    add_trace_option(g)
    p.add_option_group(g)

    return p

def main():
    o, a = make_parser().parse_args()
    def tmpf():
        print 'hint: b <function name> [, condition]'
        return 1
    DEBUG(tmpf)
    ok = 0
    for arg in a:
        info(_('ignoring argument "%s"') % arg)

    try:
        if one_of(((o.snakes,      '--snakes'),
                   (o.snake,       '--snake'),
                   ),
                  accept_allfalse=1):
            ok = 1
            info(_('Rotor()() demo (--rotate)'))

            print _('press Ctrl+C to terminate:')
            if o.snake:
                rot = make_snake(width=o.width or 10)
                # rot = make_oscillator('>')
                o.rotor_words = 'snake'
            elif o.snakes:
                rot = make_snakes(width=o.width or 15)
                o.rotor_words = 'snakes'
            rotate = Rotor(rot)
            if o.rotor_words in ('snake',
                                 'snakes',
                                 ):
                delay = o.crawl_delay or o.delay or 0.1
            else:
                delay = o.delay or 0.3
            while True:
                _sleep(delay)
                rotate()
    except KeyboardInterrupt:
        print
    except OptionCheckError, e:
        ok = 1  # there would have been something to do
        error(e)

    crawl_delay = o.crawl_delay or 0.2
    if o.caterpillar:
        ok = 1
        info(_('demo for the caterpillar generator'))
        try:
            w = o.width or 20
            p = o.period or w
            for s in generate_caterpillar(width=w, period=p):
                print s+'\r',
                _sleep(crawl_delay)
        except KeyboardInterrupt:
            pass

    if o.caterpillars:
        ok = 1
        info(_('demo for the caterpillars generator'))
        delay = float(crawl_delay) / 2
        DEBUG(o.number > 2)
        try:
            for s in generate_caterpillars(width=o.width,
                                           number=o.number):
                print s+'\r',
                _sleep(delay)
        except KeyboardInterrupt:
            pass

    try:
        if o.rotor_chars or o.random_chars:
            info(_('RandomChars()(%s) demo (--random-chars)'
                   ) % (o.rotor_chars and repr(str(o.rotor_chars)) or ''))
            ok = 1
            rotate = RandomChars(o.rotor_chars or DEFAULT_CHARS,
                                 o.width or 20)
            while True:
                _sleep(o.delay)
                rotate()
    except KeyboardInterrupt:
        pass
    except (ToolsValueError, OptionCheckError), e:
        ok = 1  # there would have been something to do
        error(e)

    if o.sleep:
        info(_('sleep() demo (--sleep)'))
        ok = 1
        w = o.width or 20
        p = o.period or w
        sleep = Sleeper(generate_caterpillar(width=w, period=o.period or w),
                        o.crawl_delay or o.delay or 0.2)

        print _('sleeping %d seconds:') % o.sleep
        try:
            sleep(o.sleep)
        except KeyboardInterrupt, e:
            print '... %s' % e.__class__.__name__
        print _('slept %.2f seconds') % sleep.slept()

    if not ok:
        error(_('nothing to do'))
    check_errors()


if __name__ == '__main__':
    main()
