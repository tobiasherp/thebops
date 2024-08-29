#!/usr/bin/env python
# -*- coding: utf-8 -*- »ö« vim: ts=8 sts=4 sw=4 si et tw=79
"""\
termwot - Tobias Herp's terminal waste of time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This module doesn't try to be nearly as complete as Monty Python's
complete waste of time (tm); but it tries to be slightly more useful,
in making using some programs, running in terminal windows,
a little bit more fun.

"""
# available with 2.1, active as of 2.2, used in caterpillar():
from __future__ import nested_scopes

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           5,	# extracted from shtools.py v0.4.2.2
           'rev-%s' % '$Rev: 985 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))
# für Module:
__all__ = [# callable instances:
           'RandomChars',
           'Sleeper',
           # Rotor utility:
           'make_oscillator',
           'make_snake',
           'make_snakes',
           # caterpillars:
           'generate_caterpillar',
           'generate_caterpillars',
           ]

from ConfigParser import ConfigParser
from time import time, sleep as _sleep
from sys import stderr
from os import linesep
from random import choice
from itertools import izip

from thebops.opo import DEBUG

try:
    _
except NameError:
    def _(s): return s
import string
try:
    string
except NameError:
    raise Exception('string module must be imported as such '
            '(because of possible modifications of character classes '
            'by the locale module)')

from thebops.rexxbi import left
from thebops.shtools import ToolsValueError, Rotor, get_console

class InvalidCharacterPoolError(ToolsValueError):   # RandomChars
    msg_tmpl = 'Invalid characters in pool (%(value)r)'

try:
    basestring
except NameError:
    basestring = (str, unicode)

def sequence_iterator(seq):
    assert isinstance(seq, (list, tuple)) or isinstance(seq, basestring)
    while 1:
        for item in seq:
            yield item

class Sleeper:
    def __init__(self, sequence, step, compact=True, tell=True):
        """
        sequence - a strings generator, or a sequence, for an animation
        step - a time (usually a fraction of a second) to sleep between
               two animation strings
        compact - default value for compact argument
        tell - ... about slept seconds
        """
        if isinstance(sequence, (list, tuple)) or \
           isinstance(sequence, basestring):
            self.sequence = sequence_iterator(sequence)
        else:
            self.sequence = sequence
        self.step = step
        self.compact = compact
        self.tell = tell
        self.prev_wakeup = None
        self.console = get_console()
        self._slept = 0

    def __call__(self, duration, compact=None):
        """
        sleep the given time while playing an animation (see the constructor)
        duration -- sleeping duration [seconds]
        compact -- unless manually terminated, erase output
        """
        if duration <= 0:
            return
        stop = float(duration)
        SLEEPSTART = time()
        slept = 0
        msg = _('sleeping %%d/%d seconds ...\r') % stop
        step = self.step
        tell = self.tell
        sequence = self.sequence
        console = self.console
        try:
            try:    # nested: Python 2.4- compability
                first = 1
                minitim = None
                for ani in sequence:
                    tim = time()
                    slept = tim - SLEEPSTART
                    if first:
                        first = 0
                        if self.prev_wakeup is not None:
                            minitim = step-(SLEEPSTART-self.prev_wakeup)
                            if minitim <= 0:
                                minitim = None
                                continue
                    if slept >= stop:
                        break
                    if minitim is None:
                        minitim = min(step, stop-slept)
                    if tell:
                        prevtext = ' '.join((ani, (msg % slept)))
                    else:
                        prevtext = ani
                    console.write(prevtext+'\r')
                    _sleep(minitim)
                if compact is None:
                    compact = self.compact
                if compact:
                    pl = len(prevtext)
                    console.write(''.join([ch * pl
                                           for ch in ' \b']))
            except KeyboardInterrupt:
                tim = time()
                slept = tim - SLEEPSTART
                console.write(linesep)
                raise
        finally:
            self._slept += slept
            self.prev_wakeup = tim

    def slept(self):
        return self._slept

class RandomChars(Rotor):
    """
    like a Rotor, but doesn't cycle through a given sequence but prints
    a fixed number of randomly chosen characters.

    Instead of calling it, you may iterate it to get an arbitrary-length
    sequence which can be fed into a Rotor.
    """
    def __init__(self, chars=None, width=8, device=None):
        if chars is None:
            chars = '0123456789abcdef'
        pool = set(chars)
        assert len(pool) >= 2, \
                ('no point in random choice from less than 2 characters'
                 ' (%(chars)r)') % locals()
        assert isinstance(width, int) and width >= 1, \
                ('width must be an integer >= 1, typically 4 .. 79'
                 ' (%(width)r)') % locals()
        ctrl = list()
        unprintable = list()
        nochar = list()
        for ch in pool:
            if 1: # try:
                if len(ch) != 1:
                    nochar.append(ch)
                    continue
                if ord(ch) < 32:
                    ctrl.add(ch)
                elif ch not in string.printable:
                    unprintable.append(ch)
            else:
                nochar.append(ch)
        if nochar:
            raise InvalidCharacterPoolError(nochar)
        self.width = width
        self.chars = list()
        self.refill = ((max(width*2,
                            len(pool)*2
                            ) // len(pool)
                        ) + 1
                       ) * list(pool)
        self._refill()
        self.backspaces = '\b' * width
        self.device = device or get_console()

    def _refill(self):
        self.chars.extend(self.refill)

    def _getchunk(self):
        for i in range(self.width):
            if not self.chars:
                self._refill()
            ch = choice(self.chars)
            yield ch
            self.chars.remove(ch)

    def __call__(self):
        out = list()
        out.extend(self._getchunk())
        out.append(self.backspaces)
        self.device.write(''.join(out))

    def __iter__(self):
        while 1:
            yield ''.join(list(self._getchunk()))

BACKWARDS = {
        '>': '<',
        'd': 'b',
        'p': 'q',
        '`': '´',
        ')': '(',
        ']': '[',
        '/': '\\',
        u'»': u'«',
        
        # '(o-': '-o)',
        # '°ooo'
        # '·.  (u'\xb7')
        }
def make_oscillator(ch, width=10):
    """
    let a character oscillate from left to right and vice versa
    """
    liz = list()
    for i in range(1, width):
        liz.append('%*s' % (i+1, ch))
    ch2 = BACKWARDS.get(ch, None)
    if ch2 is not None:
        for i in range(width-1, 0, -1):
            liz.append('%*s' % (i+1, ch2))
    return liz

def make_collider(ch, width=10):
    assert not width % 2
    assert ch
    half = width // 2
    res = list()
    chars = list(ch)
    assert len(chars) <= 2
    if len(chars) == 1:
        chars.append(_BACKWARDS.get(chars[0], chars[0]))
    halflist = list()
    for i in range(2):
        liz = list()
        for j in range(half):
            liz.append(('%*s' % (j+1, chars[i],),
                        ' ' * (half - 1 - j)))
        halflist[i].append(liz)
    res = list()
    for j in range(half):
        res.append(''.join(halflist[0]+halflist[1]))
    for j in range(half):
        res.append(''.join(halflist[1]+halflist[0]))

def make_snake(ch='o.', width=10, length=4):
    """
    create a snake which appears on the left, goes right,
    turns over and disappears again on the left, for use
    in a --> Rotor
    """
    def turn_snake(head, body, length):
        snklist = [body] * (length-2) + [head]
        yield ''.join(snklist)
        done = 0
        while not done:
            if snklist[0] == head:
                done = 1
            else:
                del snklist[0]
            snklist.append(body)
            yield ''.join(snklist)

    assert width > length + 1
    head, body = tuple(ch)
    liz = list()
    snake = ''.join([body]*(length-1)+[head])
    for i in range(1, width+1):
        liz.append('%*s' % (i, snake[-min(length, i):]))
    for snake in turn_snake(head, body, length):
        liz.append('%*s' % (width, snake))
    for i in range(width-1, 0, -1):
        liz.append('%*s' % (i, snake[-min(length, i):]))
    liz.append('')
    return liz

def make_snakes(ch='o.', width=15, length=4, distance=None):
    """
    creates two snakes (see --> make_snake), for use in a -> Rotor
    """
    snake1 = make_snake(ch, width, length)
    if distance is None:
        distance = length-1
    else:
        assert isinstance(distance, int)
        assert 1 <= distance <= 0.76 * len(snake1)
    assert width >= 2 * length + distance
    snake2 = [''] * (length+distance)
    snake2.extend(snake1)
    head, body = tuple(ch)
    return overlay_snakes(snake1, snake2, head, body)

def overlay_snakes(s1, s2, head, body):
    part1 = min(len(s1), len(s2))
    res = list()
    minilist = list()
    for i in range(part1):
        if not s1[i]:
            res.append(s2[i])
        elif not s2[i]:
            res.append(s1[i])
        else:
            del minilist[:]
            for (c1, c2) in zip(s1[i], s2[i]):
                if head in (c1, c2):
                    minilist.append(head)
                elif body in (c1, c2):
                    minilist.append(body)
                else:
                    minilist.append(c1)
            l1 = len(s1[i])
            l2 = len(s2[i])
            if l1 < l2:
                minilist.extend(s2[i][l1:])
            else:
                minilist.extend(s1[i][l2:])
            res.append(''.join(minilist))
    l1 = len(s1)
    l2 = len(s2)
    if l1 < l2:
        res.extend(s2[l1:])
    else:
        res.extend(s1[l2:])
    return res

def overlay(*generators):
    """
    overlays the outputs of the given generators
    """
    this = list()
    for tup in izip(*generators):
        res = list(tup)
        res.reverse()
        m = max(*tuple(map(len, tup)))
        for i in range(m):
            ch = ' '
            for r in res:
                try:
                    if r[i] != ' ':
                        ch = r[i]
                        break
                except IndexError:
                    pass
            this.append(ch)
        yield ''.join(this)
        del this[:]


def caterpillar(prolog=0, copies=1, period=None):
    """
    generates a caterpillar, crawling from left to right;
    the caterpillar is completely visible initially and will
    continue to crawl forever;  thus this generator is not used
    directly.

    prolog -- number of empty lines to generate first
    copies -- 1 by default; each iteration is generated <copies> times
    period -- if given, the generated caterpillar is repeatedly copied
              by <period> positions to the left; often matches the <width>
              given to the generate_caterpillar[s] functions

    """
    assert prolog >= 0
    assert period is None or period >= 10
    head=list(u'ö') # 'ö'
    tail=list('o')
    body=list('oooooo')
    left=list()

    def makestring0():
        minilist = left+tail+body+head
        return ''.join(minilist)
    def makestring1():
        "mit periodischer Wiederholung"
        minilist = left+tail+body+head
        lil = len(minilist)
        if lil > period:
            for po in range(lil-period-1, -1, -1):
                minilist[po] = minilist[po+period]
        return ''.join(minilist)
    makestring = (period is None
                  and makestring0
                  or  makestring1)

    turns, odd = divmod(len(body), 2)
    assert not odd
    for i in range(prolog):
        yield ''
    s = makestring()
    for c in range(copies):
        yield s
    while 1:
        for i in range(turns):
            del body[i]
            body[i] = 'O'
            left.append(' ')
            s = makestring()
            for c in range(copies):
                yield s
        for i in range(turns):
            body[i*2] = 'o'
            body.insert(0, 'o')
            s = makestring()
            for c in range(copies):
                yield s

def generate_caterpillars(width=None, maxbuf=300,
        number=None,
        advance=41,
        *generators):
    """
    use the caterpillar() generator and generate a caterpillar
    which crawls across a limited-width area;  since the strings
    will repeat, the generator will switch to serving from a buffer.

    width -- the width of the crawling area, default: 20

    maxbuf -- maximum number of strings which are stored in the buffer.
              If this number is exceeded, buffering is disabled,
              and the buffer is destroyed.

    number -- number of animals, default: 2 (unless generators are given)

    advance -- advance to use between animals, default: 41
    """
    prevlen = None
    offset = None
    buf = list()
    pos = None
    if generators:
        assert number is None
    else:
        if number is None:
            number = 2
        else:
            assert isinstance(number, int)
            assert number >= 2
        DEBUG(number > 3)
        if width is None:
            width = 10 * (number + 2)
        tmplist = [caterpillar(copies=number, period=width)]
        for i in range(1, number):
            tmplist.append(caterpillar(copies=number, period=width,
                                       prolog=i*advance))
        generators = tuple(tmplist)
    if width is None:
        if number is None:
            number = len(generators)
        width = 10 * (number + 2)
    i = 0
    nobuf = 0
    localdebug = 0
    for s in overlay(*generators):
        if offset is None:
            l = len(s)
            if prevlen is None:
                prevlen = l
            elif l != prevlen:
                offset = l - 1
        if offset is not None:
            t = left(s[offset:], width)
            if nobuf:
                yield t
                continue
            i += 1
            if s in buf[:-1]:
                pos = buf.index(s)
                if localdebug:
                    yield left('*** Pos: %d '%pos, width, '*')
                break
            elif not t.strip():
                pos = 0
                if localdebug:
                    yield left('*** empty ', width, '*')
                break
            elif i > maxbuf:
                nobuf = 1
                if localdebug:
                    yield width*'!'
                del buf
            else:
                buf.append(s)
            yield t
    for p in range(pos):
        yield buf[pos-1][offset:]
        del buf[0]
    for i in range(len(buf)):
        buf[i] = left(buf[i][offset:], width)
    while 1:
        for s in buf:
            yield s

def generate_caterpillar(width=20, period=None):
    """
    use the caterpillar() generator and generate a caterpillar
    which crawls across a limited-width area;  since the strings
    will repeat, the generator will switch to serving from a buffer.
    """
    if period is None:
        period = width
    elif not period:
        period = None
    if period:
        assert isinstance(period, int) and period > 0
    prevlen = None
    offset = None
    buf = list()
    pos = None
    for s in caterpillar(period=period):
        if offset is None:
            l = len(s)
            if prevlen is None:
                prevlen = l
            elif l != prevlen:
                offset = l - 1
        if offset is not None:
            t = left(s[offset:], width)
            if s in buf:
                pos = buf.index(s)
                break
            elif not t.strip():
                pos = 0
                break
            else:
                buf.append(s)
                yield t
    for p in range(pos):
        yield buf[pos-1][offset:]
        del buf[0]
    for i in range(len(buf)):
        buf[i] = left(buf[i][offset:], width)
    while 1:
        for s in buf:
            yield s

if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=__version__)
