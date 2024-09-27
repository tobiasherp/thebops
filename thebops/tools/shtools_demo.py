#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           5,	# termwot and rexxbi functions removed
           2,	# using thebops.optparse/opo
           'rev-%s' % '$Rev: 975 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

from time import sleep as _sleep

from thebops.shtools import *
from thebops.base import progname
from thebops.errors import info, error, check_errors
from thebops.optparse import OptionParser, OptionGroup
from thebops.opo import add_help_option, add_version_option, \
        add_trace_option, DEBUG

try: _
except NameError:
    def _(s): return s

def make_parser():
    p = OptionParser(add_help_option=0) # prog=progname())
    p.set_description(_('Demo for the thebops.shtools Python module'))

    g = OptionGroup(p, 'Rotors and the like')
    g.add_option('--rotate',
                 action='store_true',
                 help=_('build a rotor and use it'
                 ' ("rotate=Rotor(); rotate()")'))
    g.add_option('--rotor-chars',
                 action='store',
                 type='string',
                 metavar=DEFAULT_ROTOR,
                 help=_('characters for the "rotor", e.g. "%(DEFAULT_ROTOR)s"'
                 ' (default)'
                 ) % globals())
    g.add_option('--rotor-words',
                 action='store',
                 type='string',
                 metavar=_('one two three'),
                 help=_('you can even use words (of possibly different '
                 'lengths; for what purpose ever ...); separate them '
                 'by spaces.'
                 ' You might want to have a look at the termwot module ;-)'
                 ) % locals())
    p.add_option_group(g)

    g = OptionGroup(p, 'Adjust the generators')
    g.add_option('--delay', # '-p',
                 type='float',
                 metavar='0.3',
                 help=_('delay in seconds for common iterations'))
    p.add_option_group(g)

    g = OptionGroup(p, 'Options interoperability check demo')
    h = OptionGroup(p, 'hidden options')
    add_trace_option(h)
    g.add_option('--check-options', '-o',
                 action='store_true',
                 help=_('the options in this group fulfill the single'
                 ' purpose of being checked for interoperability using'
                 ' the "one_of" function; just try some ...'
                 ))
    g.add_option('--replace',
                 action='store_true',
                 help=_('... or --content (but not both)'))
    h.add_option('--content',
                 action='store_true')
    g.add_option('--apples',
                 action='store_true',
                 help=_('... or --pears, or --coconuts (at least one is required)'
                 ))
    h.add_option('--pears',
                 action='store_true')
    h.add_option('--coconuts',
                 action='store_true')
    p.add_option_group(g)

    g = OptionGroup(p, 'Misc. other functions')
    g.add_option('--sleep',
                 action='store',
                 type='int',
                 metavar='5',
                 help=_('demonstrate the sleep function; specify a'
                 ' whole number, e.g. 5'))
    g.add_option('--ask',
                 action='store',
                 metavar='QUESTION',
                 help=_('ask a question (quite trivial functionality'
                 ' for now)'))
    g.add_option('--choices',
                 action='store',
                 metavar='{w1[,w2][...][:N]}[;...]',
                 help=_('i18n-friendly choices specification, e.g. '
                 '"yes,sure:1;no,nope:0;always;never"'))
    p.add_option_group(g)
    g = OptionGroup(p, 'General utility functions')
    if 0:\
    p.add_option_group(g)

    g = OptionGroup(p, 'Everyday options')
    add_help_option(g)
    add_version_option(g, version=VERSION)
    p.add_option_group(g)
    return p

def main():
    o, a = make_parser().parse_args()
    DEBUG()

    ok = 0
    for arg in a:
        info(_('ignoring argument "%s"') % arg)

    if o.choices and not o.ask:
        o.ask = _('Frobnicate?')
    if o.ask:
        ok = 1
        info(_('ask() demo (--ask)'))
        try:
            answer = ask(o.ask, o.choices)
            info(_('Answer is %d') % answer)
        except KeyboardInterrupt:
            info(_('Break propagated'))
        except Exception, e:
            info(_('%r exception raised'
                   ) % e.__class__.__name__)

    if (o.check_options or
            o.replace or o.content or
            o.apples or o.pears or o.coconuts):
        info(_('one_of() demo (--check-options)'))
        ok = 1
        try:
            opts = ((o.content, '--content'),
                    (o.replace, '--replace'))
            one_of(opts, accept_allfalse=1)
            optstrings = [s[1] for s in opts]
            info(_('up to one of %(optstrings)r: ok'
                   ) % locals())
        except OptionCheckError, e:
            error(e)
            info(_('think of TAL: *either* tal:content *or* tal:replace'))
        try:
            opts = ((o.apples, '--apples'),
                    (o.pears, '--pears'),
                    (o.coconuts, '--coconuts'))
            one_of(opts)
            optstrings = [s[1] for s in opts]
            info(_('exactly one of %(optstrings)r: ok'
                   ) % locals())
        except OptionCheckError, e:
            error(e)
            info(_('one of these is required'))

    try:
        if o.rotate or one_of(((o.rotor_chars, '--rotor-chars'),
                               (o.rotor_words, '--rotor-words'),
                               ),
                              accept_allfalse=1):
            ok = 1
            info(_('Rotor()() demo (--rotate)'))

            print _('press Ctrl+C to terminate:')
            if o.rotor_words:
                rot = o.rotor_words.split()
            else:
                rot = o.rotor_chars or DEFAULT_ROTOR
            if o.rotor_words:
                print _('using words: '),
            rotate = Rotor(rot)
            delay = o.delay or 0.3
            while True:
                _sleep(delay)
                rotate()
    except KeyboardInterrupt:
        print
    except OptionCheckError, e:
        ok = 1  # there would have been something to do
        error(e)

    if o.sleep:
        info(_('sleep() demo (--sleep)'))
        ok = 1
        step = (o.sleep >= 10
                and 2
                or 1)
        print _('sleeping %d seconds:') % o.sleep
        try:
            sleep(o.sleep, step=step)
        except KeyboardInterrupt, e:
            print '... %s' % e.__class__.__name__
        print _('slept %.2f seconds') % slept()

    if not ok:
        error(_('nothing to do'))
    check_errors()

if __name__ == '__main__':
    main()
