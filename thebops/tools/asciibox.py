# -*- coding: utf-8 -*- äöü
def asciibox(label, ch='*', width=79):
    """
    Gib eine umrandete Box zurück

    label -- ein String oder eine Sequenz.
             Wenn das erste Element einer (Nicht-String-) Sequenz mit einer
             öffnenden Klammer endet, wird angenommen, daß es sich um
             einen Funktionsaufruf mit Argumenten handelt

    >>> asciibox(['foo(', 'ein string', 123], width=25)
    '''*************************
    *                       *
    *   foo('ein string',   *
    *       123)            *
    *                       *
    *************************'''

    """

    asti = ch * width
    wid_ = width - 2
    empt = (' ' * wid_).join((ch, ch))
    if isinstance(label, basestring):
        liz = [label.strip()]
    else:
        autopar = label[0].endswith('(')
    ham_ = label.strip().center(wid_).join((ch, ch))
    return '\n'.join((asti, empt, ham_, empt, asti))

