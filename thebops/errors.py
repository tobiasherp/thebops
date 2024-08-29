#!/usr/bin/python
# -*- coding: latin-1 -*- vim: ts=8 sts=4 et si sw=4 tw=79 
"""\
%(prog)s.py: Python-Modul fuer Fehlerausgaben (fuer Konsolenprogramme)
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"

# TODO:
# * introspection:
#   - skip foreign functions and objects (from imported modules)
#   - for pairs of identical functions (e.g. err and error),
#     print once and refer to it
#   - filtering by name
#   - put the whole introspection functionality in a special module

from sys import stdout, stderr, exit, argv, exc_info

from thebops.plustr1 import applyNumber

_beispiele = """\
Einfaches Anwendungsbeispiel (Python-Skript):

Das folgende Python-Skript erwartet ganze Zahlen als Argumente.
Es ueberprueft zunaechst alle uebergebenen Argumente und gibt fuer *jedes* falsche
Argument eine Fehlermeldung aus; wenn Fehler aufgetreten sind, beendet es das
Programm, und gibt ansonsten das Produkt aller uebergebenen Zahlen aus:

<snip>
from %(prog)s import err, check_errors
from sys import argv
numbers = []
for a in argv[1:]:
    try:
        numbers.append(int(a))
    except ValueError:
        err('%%r ist keine ganze Zahl' %% a)

check_errors()
print reduce(lambda a, b: a*b, numbers)
</snip>

(In einer interaktiven Python-Sitzung koennen Sie Zeile 2 durch so etwas wie
"argv = 'ignored 1 a 2 b 3 4'.split()" ersetzen.  Wenn argv[1:] Nicht-Zahlen
enthaelt, wird check_errors() die Python-Shell beenden.)

Hilfe, auch zu Funktionen und Daten: %(prog)s.py -h
"""
VERSION = '.'.join(map(str,
                   (0,
                    3, # modinfo
                    2, # prompt function removed (see thebops.shtools.ask);
                       # thebops.base
                    'rev-%s' % '$Rev: 975 $'[6:-2],
                    )))

from thebops.base import progname, RC_ERROR

def set_progname(name=None):
    """
    setze den von warning, err, fatal und info auszugebenden Namen;
    in der Regel nicht noetiger Aufruf:
    set_progname(progname())
    """
    global _PROGNAME, _LOGNAME
    if name:
        _PROGNAME = name+':'
        _LOGNAME = '['+name+']'
    else:
        _PROGNAME = ''
        _LOGNAME = ''

set_progname('errors')

def info(text, to=None):
    """
    gib die uebergebene Info aus, per Default zur Standardausgabe
    """
    if to is None:
        to = stdout
    print >> to, _PROGNAME+'i', text

WARNINGS = 0
def warn(text):
    """
    gib die uebergebene Warnung aus und erhoehe den Warnungszaehler
    """
    global WARNINGS
    WARNINGS += 1
    print >> stderr, _PROGNAME+'W', text
warning = warn

ERRORS = 0
def err(text, code=None):
    """
    gib die uebergebene Fehlermeldung aus und beende das Programm,
    sofern ein Code ungleich None uebergeben wird; andernfalls
    wird der Fehlerzaehler erhoeht
    """
    global ERRORS
    print >> stderr, _PROGNAME+'E', text
    if code is not None:
        exit(code or 1)
    ERRORS += 1
error = err

def fatal(text=None,
          code=None,
          tell=True,
          count=None,
          help=None):
    """
    Gib einen Text aus und beende jedenfalls das Programm.
    Argumente:

    text -- der auszugebende Text

    Optional:

    code -- der Returncode; Default: die Anzahl ERRORS der bisher
            aufgetretenen Fehler, oder 1
    tell -- 1 bzw. true: Info ueber Anzahl bisheriger Fehler ausgeben
            2: auch Info ueber Anzahl bisheriger Warnungen ausgeben
            Wenn None uebergeben wird, schlaegt eine Automatik zu
    count -- boolean: den aktuellen Fehler mitzaehlen?

    help -- wenn uebergeben, ein Hinweis auf die Hilfe
    """
    global ERRORS
    if count is None:
        count = False # bool(text)
    if count:
        ERRORS += 1
    if tell is None: # Automatik
        tell = not text or not count

    if text is not None:
        print >> stderr, _PROGNAME+'!', text
    RC = code or ERRORS or RC_ERROR or 1
    if tell:
        if ERRORS:
            info(applyNumber(_('%(num)d error[s]'),
                             num=ERRORS))
        if WARNINGS and tell > 1:
            info(applyNumber(_('%(num)d warning[s]'),
                             num=ERRORS))
    if help:
        info(help)
    if tell:
        info(_('Returning RC %d') % RC, stderr)
    exit(RC)

def errline(text=''):
    """
    gib eine (per Default leere) Zeile zur Standardfehlerausgabe aus

    text -- der auszugebende Text
    """
    print >> stderr, text

def check_errors(text=None,
                 code=None):
    """
    ggf. zu fatal() durchgereichte Argumente:

    text -- als help-Argument durchgereicht, ein Hinweis
            auf die Hilfe (unterdruecken durch '')
    """
    if text is None:
        text = _("Use -h or --help to get usage help")
    if ERRORS:
        fatal(code=code, tell=True, count=False, help=text)

set_progname(progname())

try:
    from gettext import gettext as _
except ImportError:
    def _(message):
        return message

# direkter Aufruf auf Kommandozeile (nicht ausgefuehrt bei Import):
if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=VERSION)
