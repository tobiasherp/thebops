#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
"""\
Demo program for the rexxbi Python module
(which contains selected functions like those built-in in the REXX language)
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           4,	# initial version: tests for rexxbi.py v0.4
           2,	# overlay
           'rev-%s' % '$Rev: 938 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

from thebops.rexxbi import *

def headline(txt):
    global ok
    if ok:
        print('')
    else:
        ok = 1
    print(txt)
    print('~'*len(txt))

def headline_txt(fname):
    return _('Demo for the %(fname)s function'
             ) % locals()

def generic_demo(f, args, rexx_syntax=0, convert=None, flabel=None):
    u"""
    f -- die demonstrierte Funktion (das Objekt)
    args -- eine Sequenz von Tupeln
    rexx_syntax -- wenn True, werden gültige Rexx-Kommandos ausgegeben
                   und die Funktionsnamen in Großschreibung konvertiert
    """
    fname = f.__name__
    if flabel is None:
        flabel = fname
    headline(headline_txt(flabel))
    if rexx_syntax:
        fname = fname.upper()
    if convert is None:
        convert = (rexx_syntax and rxfunctup
                               or  pyfunctup)
    resl = list(generate_results(f, args, convert))
    maxl = max(*tuple([len(s[0]) for s in resl]))
    mask = '%s%%-%ds -->  %%r' % (fname, maxl)
    for (a, res) in resl:
        print mask % (a, res)

def generate_results(f, args, convert):
    """
    Generiere (fargs, res)-Tupel und filtere (formatiert) identische
    Argumente aus.

    f -- die aufgerufene Funktion
    args -- eine Sequenz von Argumenttupeln
    convert -- Funktion, die ein Argumenttupel zur Ausgabe formatiert
    """
    results = {}
    for atup in args:
        res = f(*atup)
        cnv = convert(atup)
        if cnv in results:
            if res == results[cnv]:
                continue
            else:
                raise InconsistentResult(f, args, cnv, res)
        yield cnv, res
        results[cnv] = res


def test_leftright(s, width, fillchar=None, rexx_syntax=0):
    """
    not "demo_leftright", because implemented the "old way"
    """
    headline(_('Demo for the %s and %s functions'
               ) % ('left', 'right'))
    if fillchar is None:
        fillarg = ''
        fillchar = ' '
    else:
        fillarg = ', %r' % fillchar
    try:
        left(s, width, fillchar or ' ')
        fnames = 'left right'
        if rexx_syntax:
            fnames = fnames.upper()
        mask = '%s(s, %%2d%%s) = %%r   %s(s, %%2d%%s) = %%r' \
               % tuple(fnames.split()) 
        print('s = %r' % s)
        for i in range(width):
            j = width - i - 1
            print mask % (
                    i, fillarg, left(s, i, fillchar),
                    j, fillarg, right(s, j, fillchar),
                    )
    except Exception, e:
        error(e)

def demo_center(s, width, fillchar=None, rexx_syntax=0, fname='center'):
    """
    implemented the "old way", but the only demo for center/centre
    """
    headline(headline_txt('center/centre'))
    if fillchar is None:
        fillarg = ''
        fillchar = ' '
    else:
        fillarg = ', %r' % fillchar
    assert fname in ('center', 'centre')
    if rexx_syntax:
        fname = fname.upper()
    length = len(s)
    width += 1
    k = width // 2
    try:
        center(s, width, fillchar or ' ')
        # print _('s is %r:') % s
        print('s = %r' % s)
        mask = '%s(s, %%2d%%s)  -->  %%r%%*s%%*s%%r' % fname
        for i in range(width):
            j = width - i + 2
            c = center(s, i, fillchar)
            print mask % (
                    i, fillarg, c, j, '==', k, '', c,
                    )
            if i < length:
                if odd(i):
                    k -= 1
            else:
                if even(i):
                    k -= 1
    except Exception, e:
        error(e)

def shorttup(tup):
    liz = list(tup)
    while liz and liz[-1] is None:
        del liz[-1]
    return tuple(liz)

def pyfunctup(a):
    a = shorttup(a)
    if len(a) == 1:
        return '(%r)' % a
    else:
        return repr(a)

def rxfunctup(a):
    res = []
    for item in shorttup(a):
        if item is None:
            res.append('')
        else:
            res.append('%s%r' % (res and ' ' or '', item))
    return '(%s)' % ','.join(res)

def rxfunctup_verify(a):
    mmstrings = ('NOMATCH', 'MATCH')
    if len(a) == 3 and a[2] in (0, 1, False, True):
        return rxfunctup(a[:2]+(mmstrings[a[2]],))
    else:
        return rxfunctup(a)

def demo_overlay(fillchar, rexx_syntax):
    generic_demo(overlay,
            (
             ('XXX', 'ooooo', 1),
             ('XXX', 'ooooo', 2),
             ('XXX', 'ooooo', 3),
             ('XXX', 'ooooo', 1, 1),
             ('XXX', 'ooooo', 1, 2),
             ('XXX', 'ooooo', 1, 3),
             ('XXX', 'ooooo', 1, 4),
             ('XXX', 'ooooo', 1, 5),
             ('', 'oooo', 1, None, '-'),
             ('', 'oooo', 1, 1, '-'),
             ('X', 'oooo', 1, 2, '-'),
             ('XX', 'oooo', 1, 3, '-'),
             ('XX', 'oooo', 2, 3, '-'),
             ('XX', 'oooo', 3, 3, '-'),
             ('XX', 'oooo', 4, 3, '-'),
             ('XX', 'oooo', 5, 3, '-'),
             ), rexx_syntax)

def demo_translate(fillchar, rexx_syntax):
    generic_demo(translate,
            (
                # http://www.kyla.co.uk/other/rexx2.htm#translate:
                ('abcdef', '1', 'abcd', fillchar),
                ('abcdef', '123', 'abc'),
                ('321', 'abc', '123'),
                ('ij.fg.abcd', '2012-12-31', 'abcdefghij'),
                # ('No Exclaiming! Or questions?', '', '!?', '.'),
                # http://www.scoug.com/OPENHOUSE/REXXINTRO/RXBISTTR1.4.HTML:
                ("abcdef", "12", "ec"),
                ("abcdef", "12", "abcd", fillchar),
                # http://www.kilowattsoftware.com/tutorial/rexx/bitranslate.htm:
                ('01101', '01', '10'),    # "same as BitXor('01101')"
                ('abracadabra', 'ba', 'ab'),
                ('abracadabra', None, 'ab'),
                ('abracadabra', None, 'a', fillchar),
                ('AbraCaDabra', 'abcdef...', 'ABCDEF...'),
                ('AbraCaDabra',),
                # ('AbraCaDabra', xrange('a', 'z'), xrange('A', 'Z')),
             ), rexx_syntax)

def demo_verify(rexx_syntax):
    generic_demo(verify,
            (
                ('abcde', 'ab'),
                ('abcde', 'ab', 'nomatch'),
                ('abcde', 'abc', 0),
                ('abcde', 'abcde', 0),
                ('abcde', 'abcde', 'n'),
                ('abcde', 'abcde', 'm'),
                ('abcde', 'abcde'),
                ('abcde', 'cd', 'match'),
                ('abcde', 'abc', 1),
                ('abcde', 'abcde', 1),
            ), rexx_syntax,
            rexx_syntax and rxfunctup_verify or None)

def demo_compare(rexx_syntax):
    generic_demo(compare, (
        ('abc', 'abc '),
        ('abc', 'abc ', ' '),
        ('abc', 'xyz'),
        ('abc', 'abc  e'),
        ('abc', 'abc  e', ' '),
        ), rexx_syntax)

def demo_delstr(rexx_syntax):
    generic_demo(delstr,
            (
                ('abcde', 1),
                ('abcde', 3),
                ('abcde', 30),
                ('abcde', 3, 1),
                ('abcde', 3, 0),
                ), rexx_syntax)

def demo_left(data, rexx_syntax):
    generic_demo(left, data, rexx_syntax)

def demo_right(data, rexx_syntax):
    generic_demo(right, data, rexx_syntax)

def demo_substr(rexx_syntax, fillchar=None):
    if fillchar is None:
        fillchar = ' '
    generic_demo(substr,
            (
                ('abcde', 1),
                ('abcde', 3),
                ('abcde', 3, 1),
                ('abcde', 3, 0),
                ('abcde', 3, 5),
                ('abcde', 3, 5, fillchar),
                ('abcde', 3, None, fillchar),
                ), rexx_syntax)

def leftright_testdata(s, maxwidth, fillchar):
    swid = len(s)
    res = [(s, 0, fillchar)]
    w = 1
    while 1:
        res.append((s, min(w, maxwidth), fillchar))
        if w >= maxwidth:
            break
        w *= 2
    res.extend([tup[:-1] for tup in res])
    return res

# ----------------------------------------------------[ word functions [
def demo_word(rexx_syntax):
    generic_demo(word, (
        ('  follow the white rabbit', 2),
        ('  one.word.only  ', 1),
        ('  one.word.only  ', 2),
        ), rexx_syntax)

def demo_words(rexx_syntax):
    generic_demo(words, (
        ('  follow the white rabbit',),
        ('  one.word.only  ',),
        ), rexx_syntax)

def demo_wordpos(rexx_syntax):
    generic_demo(wordpos, (
        ('rabbit', '  follow the white rabbit'),
        ('  follow  ', '  follow the white rabbit'),
        ('word', '  one.word.only  '),
        ), rexx_syntax)

def demo_wordindex(rexx_syntax):
    generic_demo(wordindex, (
        ('  follow the white rabbit', 2),
        ('one.word.only  ', 1),
        ('  one.word.only  ', 2),
        ), rexx_syntax)

def demo_subword(rexx_syntax):
    generic_demo(subword, (
        ('  follow the  white rabbit  ', 2),
        ('  follow the white  rabbit  ', 3, 2),
        ('  follow the white  rabbit  ', 3),
        ('  follow the white rabbit  ', 1),
        ('  one.word.only  ', 2),
        ), rexx_syntax)

def demo_delword(rexx_syntax):
    generic_demo(delword, (
        ('  nothing to delete ', 5),
        ('  follow   the white rabbit ', 2, 2),
        ('  follow   the white rabbit ', 3, 1),
        ), rexx_syntax)

# ----------------------------------------------------] word functions ]

class DemoException(Exception):
    def __str__(self):
        return self.msg

class InconsistentResult(DemoException):
    def __init__(self, func, raw_args, norm_args, res):
        self.func = func
        self.raw_args = raw_args
        self.norm_args = norm_args
        self.res = res
        fname = func.__name__
        self.msg = '\n'.join(('Unerwartetes Ergebnis'
                              ' der Funktion %(fname)s:',
                              '  %(fname)s%(raw_args)s',
                              '  `--> %(res)r',
                              '( %(fname)s%(norm_args)s )',
                              )) % locals()


if __name__ == '__main__':
    try:
        from thebops.enhopa import OptionParser, OptionGroup
        from optparse import OptionConflictError
    except ImportError:
        from optparse import OptionParser, OptionGroup, OptionConflictError
    from thebops.errors import error, warn, check_errors
    try:
        _
    except NameError:
        _ = lambda s: s

    p = OptionParser(add_help_option=0) # see below
    p.set_description(_('Demo for the "rexxbi" Python module'
    ' which provides some functions '
    'like those built-in to the '
    'REXX programming language by Mike Cowlishaw'))
    p.version='%prog '+__version__

    g = OptionGroup(p, _('Demonstrated functions'))
    h = OptionGroup(p, 'hidden')
    functions = set([demoname[5:]
                     for demoname in globals().keys()
                     if demoname.startswith('demo_')])
    # functions.remove('center')
    functions.add('centre')
    # functions.add('center/centre')
    g.add_option('--function', '-f',
                 dest='functions',
                 action='append',
                 metavar='left,right[,...]',
                 default=[],
                 help=_('names of functions to demonstrate'
                 '; you may separate values with commas, use this option '
                 'more than once, or --all. Available functions: %s'
                 ' (also --center/--centre, --delstr, ...)'
                 ) % ', '.join(sorted(functions)))
    def cb_addfunction(option, opt_str, value, parser):
        parser.values.functions.append(opt_str[2:])
    def cb_word_functions(option, opt_str, value, parser):
        parser.values.functions.extend('words word wordpos wordindex'
                ' subword delword'.split())
    g.add_option('--left-right',
                 dest='left_right', 
                 action='store_true',
                 help=_('combined demo of the left and right functions, '
                 'inspired by the Rexx built-ins LEFT and RIGHT'))
    h.add_option('--right-left', dest='left_right', action='store_true')
    g.add_option('--verify',
                 action='callback', callback=cb_addfunction,
                 help=_('(same as --function=verify) demonstrate the verify'
                 ' function which checks for mismatching/matching characters'
                 '; with --rexx, variants with numeric 3rd '
                 'arguments are "rexxified"'
                 ' (i.e. "MATCH" or "NOMATCH" used instead)'
                 ))
    g.add_option('--word-functions',
                 action='callback',
                 callback=cb_word_functions,
                 help=_('demo for word-related functions (whitespace-delim'
                 'ited, whitespace-preserving)'))
    p.add_option_group(g)
    for fn in functions:
        try:
            h.add_option('--'+fn, action='callback', callback=cb_addfunction)
        except (OptionConflictError,    # FIXME: not caught!
                Exception):
            pass

    g = OptionGroup(p, _('Demo options'))
    g.add_option('--all',
                 action='store_true',
                 help=_('run all demos'))
    g.add_option('--input-string', '-s',
                 dest='input_string',
                 action='store',
                 metavar='1234567',
                 default='1234567',
                 help=_('input string for left, right ... demos, '
                 'default: \'%default\''))
    g.add_option('--max-width',
                 dest='max_width',
                 type='int',
                 metavar='10',
                 action='store',
                 default=10,
                 help=_('max. width for several demos, '
                 'default: %default'))
    g.add_option('--fillchar',
                 action='store',
                 metavar=repr(' '),
                 help=_('fill character for left, right, center, centre'
                 ', translate, verify'
                 '; the space character (ASCII #32 resp. 0x20) by default'
                 ))
    g.add_option('--rexx',
                 action='store_true',
                 dest='rexx_syntax',
                 help=_('show the usage examples in Rexx syntax'
                 ', which allows to omit positional arguments'
                 '; yield calls which can be fed to a Rexx interpreter'
                 ', and print uppercased function names'
                 ' (for distinction only, of course)'
                 ))
    h.add_option('--rexx-syntax', dest='rexx_syntax', action='store_true')
    p.add_option_group(g)

    g = OptionGroup(p, _('Everyday options'))
    g.add_option('--help', '-h', '-?',
                 action='help',
                 help=_('Display this help message and exit'))
    g.add_option('--version', '-V',
                 action='version',
                 help=_('Display the module version and exit'))
    p.add_option_group(g)
    o, args = p.parse_args()

    if o.max_width < 5:
        error(_('--max-width should be >= 5 (%r)') % o.max_width)
    elif 0:
        o.max_width += 1

    funcs_selected = set()
    for s in o.functions:
        for fn in s.lower().split(','):
            if fn in functions:
                funcs_selected.add(fn)
            else:
                error(_('no demo for %r, or no such function'
                        ) % fn)

    def show_function(fname):
        global o
        return o.all or fname in funcs_selected

    ok = 0
    # functions without fillchar support first: 
    if show_function('compare'):
        demo_compare(o.rexx_syntax)

    if show_function('verify'):
        demo_verify(o.rexx_syntax)

    if show_function('delstr'):
        demo_delstr(o.rexx_syntax)

    if o.fillchar is not None:
        if len(o.fillchar) != 1:
            error(_('length of fill-character %r should be 1'
		    ) % o.fillchar)
    s = o.input_string
    if s[0] in '\'"':
        if s.endswith(s[0]):
            o.input_string = s[1:-1]
    if not s:
        error(_('--input-string is empty'))
    elif not set(s).difference(set(o.fillchar or ' ')):
        warn(_('--input-string %r contains only --fillchar characters'
               ) % s)


    check_errors()
    if show_function('substr'):
        demo_substr(o.rexx_syntax, o.fillchar)

    if show_function('left') or show_function('right'):
        testinput = leftright_testdata(o.input_string,
                                       o.max_width,
                                       o.fillchar or ' ')
        if show_function('left'):
            demo_left(testinput, o.rexx_syntax)
        if show_function('right'):
            demo_right(testinput, o.rexx_syntax)

    if o.left_right or o.all:
        test_leftright(o.input_string,
                       o.max_width,
                       fillchar=o.fillchar,
                       rexx_syntax=o.rexx_syntax)

    if show_function('center'):
        demo_center(o.input_string, o.max_width, o.fillchar, o.rexx_syntax)
    elif show_function('centre'):
        demo_center(o.input_string, o.max_width, o.fillchar, o.rexx_syntax, 'centre')

    if show_function('overlay'):
        demo_overlay(o.fillchar, o.rexx_syntax)

    if show_function('translate'):
        demo_translate(o.fillchar, o.rexx_syntax)

    if show_function('word'):
        demo_word(o.rexx_syntax)

    if show_function('words'):
        demo_words(o.rexx_syntax)

    if show_function('wordpos'):
        demo_wordpos(o.rexx_syntax)

    if show_function('wordindex'):
        demo_wordindex(o.rexx_syntax)

    if show_function('subword'):
        demo_subword(o.rexx_syntax)

    if show_function('delword'):
        demo_delword(o.rexx_syntax)

    if not ok:
        error(_('nothing to do'))
    check_errors()

