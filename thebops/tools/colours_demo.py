# -*- coding: utf-8 -*- vim: sw=4 ts=8 sts=4 si et
"""
Demo for the colours module: Colours conversions
"""

__version__ = (0,
               3,   # add_colour_option, hsl(), hsla()
               1,   # demo for thebops.colours 0.3.1
               'rev-%s' % '$Rev: 959 $'[6:-2],
               )

import sys
from thebops.colours import *
from thebops.rexxbi import x2d
from thebops.modinfo import main as modinfo
from thebops.errors import warn, error
from thebops.optparse import OptionParser, OptionGroup
from thebops.plustr1 import freezeText

try: _
except NameError:
    def _(s): return s

ok = 0

def headline(txt):
    from sys import stderr
    global ok
    print >> stderr, txt
    print >> stderr, '~' * len(txt)
    ok = 1

_ORDER = ['fuchsia', 'purple', 'maroon', 'red', 'yellow',
          'lime', 'green', 'olive', 'teal', 'aqua', 'blue', 'navy',
          'black', 'gray', 'silver', 'white']
def makekey(n):
    try:
        return (_ORDER.index(n),) + HTML4_COLOURS[n]
    except ValueError:
        return (1000,) + SVG_COLOURS[n]

def shortesthex(tup):
    """
    >>> shortesthex((0, 0, 255))
    '00f'
    >>> shortesthex((0, 0, 0))
    '000'
    >>> shortesthex((1, 2, 3))
    '010203'
    """
    assert isinstance(tup, tuple)
    longhex = (3 * '%02x') % tup
    shorthex = (longhex[0], longhex[2], longhex[4])
    comp = ''.join([2*ch for ch in shorthex])
    if comp == longhex:
        return ''.join(shorthex)
    else:
        return longhex

def cascade(str, astuple=0):
    """
    generate the conversion cascade for the given spec

    str -- the colour spec (symbolic names are allowed)

    astuple -- if True, the final generated element is returned as a 3-tuple
               of integers rather than a string

    >>> list(cascade('magenta'))
    ['magenta', '#f0f', '#ff00ff', 'rgb(255, 0, 255)']
    """
    s = str.lower().strip()
    if s.startswith('#'):
        s = s[1:]
    if s in CSS_COLOURS.keys():
        yield s
        s = shortesthex(CSS_COLOURS[s])
    try:
        if len(s) == 3:
            yield '#'+s
        tup = splitcolour(s)
        yield '#' + ''.join(tup)
        rgb = map(x2d, tup)
        if not astuple:
            rgb = 'rgb(%d, %d, %d)' % tuple(rgb)
        yield rgb
    except KeyError:
        raise InvalidColourSpec

def print_cascade(s):
    """
    print the conversion cascade for the given spec
    """
    try:
        print '\t-> '.join(list(cascade(s)))
    except InvalidColourSpec:
        error(_('%s:\tinvalid colour specification'
                ) % s)

def comp(d1, d2):
    """
    comparison function for the colours list (print_table):
    sort by key
    """
    return cmp(d1['sort'], d2['sort'])

def comp2(d1, d2):
    """
    comparison function for the colours list (--print):
    sort by name
    """
    return cmp(d1['name'], d2['name'])

def print_table():
    global colours
    print '<table style="empty-cells:show"><thead><tr>'
    print '  <th scope="col">Name</th>'
    print '  <th scope="col">Ansicht</th>'
    print '  <th scope="col">hex</th>'
    print '  <th scope="col" class="r">rot</th>'
    print '  <th scope="col" class="g">gr&uuml;n</th>'
    print '  <th scope="col" class="b">blau</th>'
    print '  <th scope="col">rgb()</th>'
    print '</tr></thead><tbody>'
    colours.sort(comp)
    for dic in colours:
        dic['hex'] = normalhex(dic['hex'])
        dic['r'], dic['g'], dic['b'] = CSS_COLOURS[dic['name']]
        print '<tr>'
        print '  <th scope="row">%(name)s</th>' % dic
        print '  <td style="background-color:#%(hex)s"></td>' % dic
        print '  <td class="hex">%(hex)s</td>' % dic
        print '  <td class="r">%(r)d</td>' % dic
        print '  <td class="g">%(g)d</td>' % dic
        print '  <td class="b">%(b)d</td>' % dic
        print '  <td><tt>rgb(%(r)d, %(g)d, %(b)d)</tt></td>' % dic
        print '</tr>'
    print '</tbody></table>'

def parse_args():
    p = OptionParser(usage='%prog [COLORSPEC] [...] | [Optionen]')

    g = OptionGroup(p, 'Print tables')
    g.add_option('--print',
                 action='store_true',
                 dest='print_raw',
                 help=_('Print the known colour names'
                 ))
    g.add_option('--html',
                 action='store_true',
                 dest='print_html',
                 help=_('print an HTML colour table to standard '
                 'output'))
    g.add_option('--svg-colours', '--svg-colors',
                 action='store_true',
                 dest='svg_colours',
                 help=_('include the colour names taken from SVG '
                 '(which are part of CSS 3)'))
    add_colour_option(g)
    add_colour_option(g, '--alpha-colour', alpha=1)
    p.add_option_group(g)

    return modinfo(parser=p,
                   version=__version__)

def ignored_args_warning(a):
    if not a:
        return
    quantity = len(a)
    warn(freezeText(_('Argument[s] %s [is|are] ignored'
                      ),
                    quantity > 1)
                    % ', '.join(a))

colours = []
def main():
    o, args = parse_args()
    global colours
    if o.print_html or o.print_raw or o.print_html:
        colours = []
        for name, tup in (o.svg_colours
                          and SVG_COLOURS
                          or  HTML4_COLOURS).items():
            colours.append({
                'name': name,
                'hex': shortesthex(tup),
                'sort': makekey(name),
                })
    if o.colour:
        headline('--colour')
        print o.colour
    if o.alpha_colour:
        headline('--alpha-colour')
        print o.alpha_colour
    if o.print_html:
        headline('--html')
        ignored_args_warning(args)
        print_table()
    elif o.print_raw:
        headline('--print')
        ignored_args_warning(args)
        colours.sort(comp2)
        done = set()
        for dic in colours:
            name = dic['name']
            if name not in done:
                print_cascade(name)
                done.add(name)
    if args:
        headline(_('Arguments'))
        for arg in args:
            print_cascade(arg)
    if not ok:
        try:
            print_cascade(raw_input(_('Specify a colour: ')))
        except KeyError:
            print

