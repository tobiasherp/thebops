#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et
"""
sort-po.py - Sortiere gettext-Kataloge

Von Hand bearbeitete .po- und .pot-Dateien sind oftmals nicht sortiert, u. a.
deshalb, weil thematisch zusammenhängende Message-IDs dadurch übersichtlicher
zu bearbeiten sind. Beim Zusammenführen von Änderungen artet dies jedoch in
einen Alptraum aus, weil die IDs nach jeder Generierung wieder sortiert
werden; die Differenzen sind dann absolut unübersichtlich.

Dieses Programm erlaubt es, die Einträge nach Gusto vorzunehmen und das
Ergebnis vor Integration in den Stamm zu sortieren; dadurch werden die
Differenzen übersichtlich und die Gefahr vermeidbarer Konflikte minimiert.

$Id: sort_po.py 1094 2014-03-06 01:38:37Z  $
"""
# TODO:
# - Quellenangaben:
#   - stets eine Quellenangabe je Zeile (bessere Vergleichbarkeit)
# - Kommentare checken:
#   - Quellenangaben ./. "#. source unknown"
#   - Reihenfolge:
#     '#  ' (Übersetzer-Kommentar, bel. Text)
#     '#. ' (automatischer Kommentar, z. B. Defaultwert)
#     '#: ' Quelle
#     '#, fuzzy' Flag
#   - Prüfung auf unbekannte Flags und automatische Kommentare (von Poedit ggf. entfernt!)
# - Zeilenlängen begrenzen
#   - vor oder nach explizit notiertem \n umbrechen
#   - an Wortgrenzen umbrechen
#     - Leerzeichen am Zeilenende (so macht es Poedit)
#   - keine Begrenzung für '#. Default:'-Kommentare
# - Prüfung auf doppelte Message-IDs
# - Testbarkeit:
#   - err-Aufrufe in Funktion sort_catalogue durch Exceptions ersetzen
#   - Ausführbares Objekt
#     - getrennte Methoden für Analyse und Zurückschreiben
# DONE:
# - Quellenangaben normalisieren (überall / statt \)

__version__ = (0,
               3,   # optparse
               'rev-%s' % '$Rev: 4678 $'[6:-2],
               )

from sys import argv, stderr
from os.path import splitext, normcase
from os import linesep
from string import split
from thebops.errors import info, err, warn, check_errors, errline, progname
from thebops.optparse import OptionParser, OptionGroup

NOFIX, FIXEDEOLS, FIXWRITTEN, FIXALWAYS = range(4)

## ----------------------------------------------- [ Optionen erzeugen [

def parse_args():
    p = OptionParser(add_help_option=0,
                     usage='%prog {Datei [...]} [Optionen]')

    p.set_description('Sortiert gettext-Katalogdateien.')
# g = p

    p.add_option('--check-only',
                 dest='check_only',
                 action='store_true',
                 help=u'Dateien nur lesen und prüfen, nicht zurückschreiben')

    g = OptionGroup(p, 'Subversion-Optionen')
    g.add_option('--fix-eol-prop', '-L',
                 action='count',
                 dest='fix_eol_prop',
                 help='Korrigiere bzw. setze das svn-Property "svn:eol-style": '
                 '-L: wenn Zeilenenden korrigiert; '
                 u'-LL: wenn Zeilenenden korrigiert oder sonstige Änderungen'
                      ' vorgenommen; '
                 '-LLL: immer.'
                 u' Es wird möglichst der Wert "native" verwendet.')
    if 'noch nicht fertig!' and 0:\
    p.add_option_group(g)

    g = OptionGroup(p, 'Allgemeine Optionen')
    g.add_option('-h', '-?', '--help',
                 action='help',
                 help='diese Hilfe ausgeben und beenden')
    p.version = '%prog ' + '.'.join(map(str, __version__))
    g.add_option('-V', '--version',
                 action='version',
                 help='die Programmversion ausgeben und beenden')
    g.add_option('--verbose', '-v',
                 action='count',
                 default=0,
                 help=u'ausführliche Ausgaben'
                 )
    p.add_option_group(g)
    return p.parse_args()

## ----------------------------------------------- ] Optionen erzeugen ]


## ---------------------------------------------- [ Utility-Funktionen [

def eol_prop_value(foundeols):
    if foundeols == linesep:
        return 'native'
    elif isinstance(foundeols, (tuple,)):
        return None
    elif foundeols == '\r':
        return 'CR'
    elif foundeols == '\n':
        return 'LF'
    elif foundeols == '\r\n':
        return 'CRLF'
    else:
        return None


## ---------------------------------------------- ] Utility-Funktionen ]

class CorrectedID(Exception):
    def __init__(self, bogus, corrected):
        self.bogus = bogus
        self.corrected = corrected
    def __str__(self):
        return 'Fehlerhafte Message-ID %r' % self.bogus

class CommentsError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return 'Kommentar-Fehler: %s' % self.msg

class CommentsOrderError(CommentsError):
    def __init__(self, c1, c2):
        self.c1 = c1
        self.c2 = c2
    def __str__(self):
        return '\n'.join(('Kommentar-Reihenfolge:',
                          '    %s' % self.c2,
                          'nach',
                          '    %s' % self.c1,
                          'gefunden'))

class SourceCommentsConventionError(CommentsError):
    pass

WARNED = 0
def check_comments_order(lst):
    """
    Lies eine Liste von Zeilen, ueberpruefe die Kommentare
    (die am Anfang der Liste stehen, was vom Zustandsautomaten ueberprueft ist)
    und wirf ggf. eine CommentsError-Exception
    """
    global WARNED
    if not WARNED:
        warn('check_comments_order: noch nicht implementiert!')
        WARNED = 1

def generate_info(s):
    first = 1
    last = 0
    prev = None
    ch = None
    for ch in s:
        if first:
            first = 0
        else:
            yield prev
            prev = ch

quote_chars = ("\"", '\'')
def check_postr(s):     # check po-String
    """
    Gib die Message-ID (bzw. allgemein den .po-String) unverändert zurück
    oder wirf eine CorrectedID-Exception, die eine korrigierte Fassung im
    Attribut "corrected"  enthält.

    .po-Strings im Sinne dieser Funktion sind solche, die im Rahmen der
    Katalogsyntax Strings sind, also Bestandteil von Message-IDs oder
    Übersetzungen (keine Kommentare).
    """
    res = []
    quote = None
    terminated = 0
    escaped = 0
    prev = None
    correct = 1
    for ch in s:
        if terminated:          # ... und trotzdem noch Zeichen im Vorrat!
            res.insert(-1, '\\')
            correct = 0
            terminated = 0
        if ch in quote_chars:
            if not res:
                quote = ch
                if quote != "\"":
                    correct = 0
            elif ch == quote:
                if prev != '\\':
                    terminated = 1
        elif not res:
            correct = 0
            quote = "\""
            res.append(quote)
        res.append(ch)
        prev = ch
    if not res:
        correct = 0
        quote = "\""
        res.append(quote)
    if not terminated:
        correct = 0
        res.append(quote)
    if correct:
        return s
    if quote != "\"":
        raise CorrectedID(s, swap_quotes(res))
    raise CorrectedID(s, ''.join(res))

def swap_quotes(liz):
    """
    nur zur Nachbearbeitung, durch check_postr aufgerufen
    """
    res = []
    prev = None
    for ch in liz:
        if prev is None:
            assert ch == '\'', 'ch ist %r' % ch
        if ch == '\'':
            ch = "\""
        elif ch == "\"":
            res.append('\\')
        res.append(ch)
        prev = ch
    return ''.join(res)


def fix_trailing_doubles(liz):
    """
    Workaround für das "Problem" der doppelten Kommentarzeile am Schluß ...
    """
    last = None
    for i in range(len(liz)-1, -1, -1):
        if last is None:
            if liz[i]:
                last = liz[i]
        elif liz[i]:
            if liz[i] == last:
                del liz[i]
                return 1
            break
    return 0

def _mkkey_s(s):
    # Anf.zeichen und \ entfernen
    return s[1:-1].replace('\\"', "\"")

def join_msgid(liz):
    """
    Die msgid kann sich (wie auch der msgstr) über mehrere Zeilen erstrecken;
    alles zusammenfassen und überschüssige Gänsefüßchen entfernen
    (zur Verwendung als Sortierschlüssel)
    """
    assert liz[0].startswith('msgid '), 'liz = %r' % (liz,)
    res = [liz[0][6:].lstrip()]
    if len(liz) == 1:
        return _mkkey_s(res[0])
    try:
        first = 1
        for part in liz:
            if first:
                part = part[6:].strip()
                first = 0
            assert part, 'part ist leer (%r)' % (part,)
            assert part[0] == "\"", 'part beginnt mit %r' % part[0]
            assert part[-1] == "\"", 'part endet mit %r' % part[-1]
            if res:
                res[-1] = res[-1][:-1]
                res.append(part[1:])
            else:
                res.append(part)
    except AssertionError, e:
        print str(e)
        raise
    return _mkkey_s(''.join(res))


PROG = progname()
def sort_catalogue(fname, o):
    """
    Sort a gettext catalogue file
    """
    def show_processed():
        return o.verbose >= 1
    def show_skipped():
        return o.verbose >= 2

    def fix_eol_prop(given):
        return given <= o.fix_eol_prop

    ext = normcase(splitext(fname)[1])
    if ext not in ('.po', '.pot'):
        if show_skipped():
            err('keine .po-Datei: %s' % fname)
        else:
            print >> stderr, 'skip: %s   \b\b\b\r' % fname,
        return
    if show_processed():
        info('Verarbeite %s' % fname)
    else:
        print >> stderr, '%s ...\b\b\b\b\r' % fname,
    fo = open(fname, 'rU')
    zn = 0      # Zeilennummer
    errors = []
    def lineerr(txt):
        errline('%s:e:%s:%d:%s' % (PROG, fname, zn, txt))
        errors.append(txt)

    def append_postring(liz, value, prefix=None):
        try:
            v = check_postr(value)
        except CorrectedID, e:
            v = e.corrected
            lineerr('%(value)s  -->  %(v)s' % locals())
        if prefix is not None:
            assert prefix in ('msgid', 'msgstr'), 'prefix ist %r' % prefix
            v = ' '.join((prefix, v))
        liz.append(v)

    def comment_or_id(s):
        """
        0: msgid oder (optional) Kommentar erwartet
        """
        if s.startswith('#'):
            comments.append(s.rstrip())
            return 0
        elif s.startswith('msgid '):
            assert not theid
            append_postring(theid, split(s, maxsplit=1)[1], 'msgid')
            return 1
        elif not s:
            if not msgstr \
                and not theid \
                and not [s for s in comments
                         if not s.startswith('#~')
                         and not s.startswith('#,') # z. B. '#, fuzzy'
                         ]:
                if comments:
                    trailing_comments.extend(comments+[''])
                    del comments[:]
                return 0
            if comments or theid or msgstr:
                lineerr('Kommentar oder msgid erwartet: %s' % s)
            else:
                return 0

    def string_or_msgstr(s):
        """
        1: msgid gefunden; Fortsetzung oder msgstr erwartet
        """
        if s.startswith('msgstr '):
            assert not msgstr
            append_postring(msgstr, split(s, maxsplit=1)[1], 'msgstr')
            return 2
        elif not s:
            lineerr('Leerzeile gefunden; msgstr erwartet!')
        elif s[0] in quote_chars:
            append_postring(theid, s)
            return 1

    def string_or_end(s):
        """
        2: msgstr gefunden; Fortsetzung oder Leerzeile erwartet
        """
        if not s:
            return 3
        elif s[0] in quote_chars:
            append_postring(msgstr, s)
            return 2
        else:
            lineerr('Fortsetzung des msgstr oder Leerzeile erwartet! (%s)'
                    % s)

    def add_block(s):
        """
        3: Leerzeile gefunden; jetzt den kompletten Block verarbeiten
        """
        res = []
        if comments:
            res.extend(comments)
            del comments[:]
        if theid:
            res.extend(theid)
            key = join_msgid(theid)
            del theid[:]
        elif not msgstr and not [s for s in comments
                                 if not s.startswith('#~')
                                 ]:
            trailing_comments.extend(res+[''])
            return 3
        else:
            lineerr('Keine msgid vorhanden!')
            return None
        if msgstr:
            res.extend(msgstr)
            del msgstr[:]
        else:
            lineerr('Kein msgstr vorhanden!')
            return None
        msgids.append((key, res))
        return comment_or_id(s)

    modefunc = (comment_or_id,
                string_or_msgstr,
                string_or_end,
                add_block,
                )

    # Arbeitslisten für einzelne Blocks: 
    theid = []
    msgstr = []
    comments = []
    # Ergebnislisten:
    msgids = []
    trailing_comments = []
    # Modus als Funktionsindex:
    mode = 0
    fixeol = None
    try:
        for z in fo:
            zn += 1
            z = z.rstrip()
            mode = modefunc[mode](z)
            if mode is None:
                err('mode ist None; %s bitte reparieren! (Zeile %s)'
                     % (fname, zn))
                return
        mode = modefunc[mode]('')
        if mode not in (0, 3):
            err('Hoppla - mode ist %s!' % mode)
            return
    finally:
        if mode is not None:
            mode = modefunc[mode]('')
        fix_eols = 0
        eolprop = None
        if fo.newlines is None:
            err('Keine newlines gefunden?!')
        elif isinstance(fo.newlines, tuple):
            fix_eols = len(fo.newlines) != 1
            if fix_eols:
                fixeol = FIXEDEOLS
        else:
            eolprop = eol_prop_value(fo.newlines)
        fo.close()
    header_found = 0
    previd = None
    i = 0
    needs_sorting = 0
    for (id, val) in msgids:
        if id == '':
            if header_found:
                err('Header zweimal gefunden!')
                return
            if i:
                err('Header nicht an erster Stelle!')
                return
            header_found = 1
        else:
            if id < previd:
                if not needs_sorting:
                    info('%s < %s  --> Sortierung notwendig'
                         % (id, previd))
                    needs_sorting = 1
            if header_found and needs_sorting:
                break
        try:
            check_comments_order(val)
        except CommentsError, e:
            info('msgid %(id)s: %(e)s' % locals())
            info('`-> Sortierung notwendig')
            needs_sorting = 1
        previd = id
        i += 1
    if not header_found:
        err('Kein Header gefunden')
        return
    if not (needs_sorting or fix_eols or errors):
        if show_processed():
            info('%s erfordert keine Modifikationen' % fname)
        return
    if needs_sorting:
        info('%s wird sortiert' % fname)
        msgids.sort()
    if fix_eols:
        info('%s: Korrektur der Zeilenenden %s'
             % (fname, tuple(fo.newlines)))
    if o.check_only:
        info('%s: nicht geschrieben, --check-only aktiv'
             % (fname,))
        return
    # Änderung der Originaldatei; 
    # die wird ja wohl versioniert sein!
    fo = open(fname, 'w')
    for (id, lines) in msgids:
        fo.write(linesep.join(lines+['','']))
    if trailing_comments:
        if fix_trailing_doubles(trailing_comments):
            err(u'fix_trailing_doubles sollte nicht mehr nötig sein!')
        fo.write(linesep.join(trailing_comments))
    fo.close()
    eolprop = 'native'
    info('%s geschrieben' % fname)
    return

def main():
    o, args = parse_args()
    if not args:
        err('Nichts zu tun')
    else:
        for a in args:
            sort_catalogue(a, o)
    check_errors()

if __name__ == '__main__':
    main()
