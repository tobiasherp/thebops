#!/usr/bin/python
"""
thebops.plustr1 - plural strings module 1

This module is sufficient for languages which use the singular form for
num == 1, and the plural form for all other numbers
"""

VERSION = (0,
           5, # 
           1, # freezeText -> thebops.plustr1
           1, # _splitPluralSwitchableString examples -> doctest
           'rev-%s' % '$Rev: 1086 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))
__all__ = ['freezeText',
	   'applyNumber',
           ]
__author__ = 'Tobias Herp <tobias.herp@gmx.de>'

def freezeText(text, plural):
    """
    return a 'frozen' version of the given text, resolving the
    '{[sing|]plu}' expressions, depending on the 2nd parameter, which
    must be 'true' for plural versions and 'false' for singular.
    Used by --> counted(key, text) (thebops.counters module)

    Examples:

    >>> num = 1
    >>> freezeText('file[s] or director[y|ies]', num!=1)
    'file or directory'
    >>> num = 2
    >>> freezeText('file[s] or director[y|ies]', num!=1)
    'files or directories'
    """
    res, sing, plu, suffix = _splitPluralSwitchableString(text)
    if plural:
        res = res + plu
        while suffix:
            prefix, sing, plu, suffix = _splitPluralSwitchableString(suffix)
            res = ''.join((res, prefix, plu))
    else:
        res = res + sing
        while suffix:
            prefix, sing, plu, suffix = _splitPluralSwitchableString(suffix)
            res = ''.join((res, prefix, sing))
    return res

def applyNumber(text, **kwargs):
    """
    >>> applyNumber('[one|%(num)d] file[s] or director[y|ies]', num=1)
    'one file or directory'
    >>> applyNumber('[one|%(num)d] file[s] or director[y|ies]', num=2)
    '2 files or directories'

    As demonstrated by the above singular string 'one', the placeholder
    for the number can be omitted:

    >>> applyNumber('file[s] or director[y|ies]', num=2)
    'files or directories'
    """
    assert len(kwargs) == 1
    val = kwargs.values()[0]
    plu = val != 1
    return freezeText(text, plu) % kwargs

def _splitPluralSwitchableString(text):
    """
    split a string and return a 4-tuple:
    (prefix, singular, plural, suffix)

    >>> _splitPluralSwitchableString('file[s]')
    ('file', '', 's', '')
    >>> _splitPluralSwitchableString('stor[y|ies] ')
    ('stor', 'y', 'ies', ' ')

    This is a helper function, used by --> freezeText(text, plural)
    """
    sf, pf = (0, 0)
    tup1 = text.split('[', 1)
    if len(tup1) == 1:
        return (text, '', '', '')
    tup2 = tup1[1].split(']', 1)
    if len(tup2) == 1:
        return (text, '', '', '')
    tup3 = tup2[0].split('|', 1)
    if len(tup3) == 1:
        return (tup1[0], '', tup3[0], tup2[1])
    else:
        return (tup1[0], tup3[0], tup3[1], tup2[1])

if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=VERSION)
