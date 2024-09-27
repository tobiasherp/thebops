#!/usr/bin/python
"""\
thebops.base: base module for other thebops modules
"""

from __future__ import absolute_import
from six.moves import map
__author__ = "Tobias Herp <tobias.herp@gmx.net>"

try: _
except NameError:
    def _(s): return s

from os.path import basename
from sys import argv

VERSION = (0,
           1,	# initial version
           1,	# bugfix for progname function
           'rev-%s' % '$Rev: 995 $'[6:-2],
           )

__version__ = '.'.join(map(str, VERSION))

__all__ = [
        'progname',
        # data:
        'RC_ABORT',
        'RC_CANCEL',
        'RC_ERROR',
        'RC_HELP',
        'RC_OK',
        ]

RC_ERROR = 1   # bei Fehler ans System zurueckzugeben, wenn nicht ein Zaehler o.ae.
RC_OK = 0      # trivial, aber hiermit dokumentiert
RC_HELP = 3    # nach Hilfeausgabe zurueckzugeben
RC_CANCEL = 98 # bei Abbruch durch Benutzer, z. B. nach Prompt
RC_ABORT = 99  # bei Abbruch durch Benutzer durch Interrupt

def progname(stripchar=None, stripext=True, stripscript=True):
    """
    gib den Namen des Programms zurueck, ohne Verzeichnisangaben und
    Extension
    """
    tmp = basename(argv[0])
    tails = []
    if stripext:
        tails.extend(['.py', '.exe',
                      ])
    if stripscript:
        tails.append('-script')
    for tail in tails:
        if tmp.endswith(tail):
            tmp = tmp[:-len(tail)]
    if stripchar:
        tmp = tmp.rstrip(stripchar)
    return tmp

if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=VERSION)
