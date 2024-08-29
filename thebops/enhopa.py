# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 et
"""
enhopa: An enhanced option parser, using the optparse module

NOTE:
    Please don't import / use the new names of this module
    (except the set_collecting_group method);
    they will very likely go away in the next major version!
    Just use the names you are used to from optparse.

    Now that optparse is sort of deprecated as of Python 2.7,
    I consider this bazaar closed; this module won't evolve much further.
    Instead, recent development takes place in the thebops.optparse module.

    I'm not sure whether the set_collecting_group method will be included
    there (probably not, in fact); meanwhile, there is the thebops.opo module.
    Using add_help_option and add_version_option is more explicit, and the
    behaviour is more straight-forward.
"""
__version__ = (0,
               2, # version tuple; tabs; example; etc.
               7, # Python 2.4 compability
               'rev-%s' % '$Rev: 998 $'[6:-2],
               )
VERSION = '.'.join(map(str, __version__))

import optparse
import gettext

from thebops.base import progname
from thebops.errors import err
from thebops.opo import add_help_option, get_the_parser

__all__ = ['OptionParser',
           'OptionGroup',
           'Option',
           'OptionError',
           'Values',
           'EnhancedHelpFormatter',
           # optparse:
           # 'IndentedHelpFormatter',
           ]
__author__ = 'Tobias Herp <tobias.herp@gmx.de>'
gettext.install('optparse')
_ = gettext.gettext

try:
    STD_HELP_OPTION = optparse.STD_HELP_OPTION
    STD_HELP_OPTION._short_opts.append('-?')
except AttributeError:
    optparse.OptionParser._add_help_option = add_help_option

OptionConflictError = optparse.OptionConflictError

# for options which can be specified in more than one way (e.g. using a short
# ("UNIX-style") or a long ("GNU-style") option string), don't repeat the
# 'metavar' every time; instead the value of this 'constant' is used (unless
# overridden by a metavar2 argument).
# Example help output:
#    -s{WIDTH[x{HEIGHT}]}, --scale=...
# To restore the 'normal' behaviour, which would be to display
#    -s{WIDTH[x{HEIGHT}]}, --scale={WIDTH[x{HEIGHT}]},
# set this to None, or use IndentedHelpFormatter.
DEFAULT_METAVAR_2='...'
DEFAULT_METAVAR_2_CHOICES='(...)'

# NOT IMPLEMENTED YET:
SHORTCUTS_AS_OPTIONS, SHORTCUTS_IN_CHOICES = range(1, 3)
# when displaying the help screen, by default treat shortcuts
# (e.g. --portrait, which could be the same as --orientation=portrait)
# as options, e.g.:
#       --orientation={unchanged,portrait,landscape,auto}
#       --portrait     shortcut for --orientation=portrait
SHORTCUT_TREATMENT = SHORTCUTS_AS_OPTIONS

# not translated in Python 2.4.2 optparse module:
optparse.HelpFormatter.NO_DEFAULT_VALUE = _("none")


# not yet used:
DONT_ADD, ADD_STANDARD_OPTION, ADD_COUNTING_OPTION = range(3)

def check_choice(option, opt, value):
    if value in option.choices:
        return value
    else:
        choices = ", ".join(map(repr, option.choices))
        raise OptionValueError(
            _("option %(opt)s: invalid choice: %(value)r"
              " (choose from %(choices)s)"
              ) % locals())

def check_xchoice(option, opt, value):
    try:
        return option._choices_map[value]
    except KeyError:
        choices = ", ".join(map(repr, option.choices))
        raise OptionValueError(
            _("option %(opt)s: invalid choice %(value)r"
              " (choose from %(choices)s)"
              ) % locals())

class EnhancedOption(optparse.Option):
    """
    Extended version of optparse.Option;
    additional action: decrease, complementing count
    (no way to prevent negative values so far).

    Usage: when creating an OptionParser, specify the
    name argument option_class, or create an EnhancedOptionParser.

    New argument xchoices: a sequence of (value, helptext) tuples;
    when using the EnhancedHelpFormatter object (default for
    EnhancedOptionParser), '%choices' or -- with helptexts --
    '%xchoices' can be used in the help text.

    TODO:
    - Argument xchoices: support sequence of
      ((value1, value2, ...), helptext) tuples
      (equivalent values, only the first listed in standard
      metavar)
    """

    ACTIONS = optparse.Option.ACTIONS + ("decrease",)
    STORE_ACTIONS = optparse.Option.STORE_ACTIONS + (
            "decrease",
            "choice",   # set by _check_type
            "xchoice",  # set by _check_xchoices
            )
    ATTRS = optparse.Option.ATTRS + ['metavar2', 'xchoices']

    TYPE_CHECKER = optparse.Option.TYPE_CHECKER.copy()
    TYPE_CHECKER['xchoice'] = check_xchoice

    # metavar2='...'

    def __init__(self, *opts, **attrs):
        optparse.Option.__init__(self, *opts, **attrs)
        self.enhopa_init_epilog()

    def enhopa_init_epilog(self):
        """
        adjustments for old optparse versions
        """
        tmp = getattr(self, 'CONST_ACTIONS', None)
        if tmp is None:
            tmp2 = getattr(self, 'STORE_ACTIONS', ['store_const'])
            self.CONST_ACTIONS = tuple([s for s in tmp2
                                        if s.endswith('_const')
                                        ])
            print '*** %s: %s' % (self.__class__.__name__, self.CONST_ACTIONS)

    def action_decrease(self, action, dest, opt, value, values, parser):
        """
        complements count
        """
        setattr(values, dest, values.ensure_value(dest, 0) - 1)

    def action_xchoice(self, action, dest, opt, value, values, parser):
        setattr(values, dest, self._choices_map[value])

    def take_action(self, action, dest, opt, value, values, parser):
        """
        take the given action.

        This method doesn't need to be reimplemented in derived classes;
        instead, simply implement (or overwrite) action_<action name>
        methods.
        """
        try:
            func = getattr(self, 'action_'+action)
            func(action, dest, opt, value, values, parser)
        except AttributeError:
            optparse.Option.take_action(self, action, dest,
                               opt, value, values, parser)

    def _check_xchoices(self):
        if self.xchoices is not None:
            if self.choices is not None:
                raise optparse.OptionError('only choices *or* xchoices allowed',
                        self)
            else:
                self.choices = [] # for check_xchoice
            self._choices_map = {}
            mv = []
            for ch, help in self.xchoices:
                if isinstance(ch, tuple):
                    for c in ch:
                        self._choices_map[str(c)] = ch[0]
                    self.choices.extend(list(ch))
                    mv.append(ch[0])
                else:
                    mv.append(ch)
                    self.choices.append(ch)
                    self._choices_map[str(ch)] = ch
            self.type = 'xchoice'
            if self.metavar is None:
                self.metavar = '(%s)' % '|'.join(mv)
        if self.choices is not None and self.metavar is None:
            self.metavar = '(%s)' % '|'.join(self.choices)


    def _check_type(self):
        if self.type is None:
            if self.action in self.ALWAYS_TYPED_ACTIONS:
                if self.xchoices is not None:
                    # The "choices" attribute implies "choice" type.
                    self.type = "xchoice"
        optparse.Option._check_type(self)

    def _check_metavar(self):
        """
        all attributes in self.ATTRS were set before
        """
        if ((self.action in self.STORE_ACTIONS
             or (self.action == 'callback' and self.type is not None))
            and self.action not in self.CONST_ACTIONS
                                   +('store_true', 'store_false')
            ):
            if self.metavar2 is None:
                if self.choices is None:
                    self.metavar2 = DEFAULT_METAVAR_2
                else:
                    self.metavar2 = DEFAULT_METAVAR_2_CHOICES
            elif not str(self.metavar2).strip():
                raise OptionError(
                    "metavar2 must yield a nonempty string", self)
        else:
            if self.metavar is not None:
                raise OptionError(
                    "must not supply metavar for action %r" % self.action, self)
            if self.metavar2 is not None:
                raise OptionError(
                    "must not supply metavar2 for action %r" % self.action,
                    self)

    CHECK_METHODS = optparse.Option.CHECK_METHODS[:]
    try:
        _tmpi = CHECK_METHODS.index(optparse.Option._check_type)
        CHECK_METHODS[_tmpi] = _check_type
    except ValueError:
        CHECK_METHODS.append(_check_type)
    CHECK_METHODS.append(_check_metavar)

class EnhancedHelpFormatter(optparse.IndentedHelpFormatter):
    """
    supports:

    metavar2, default: '...' -- for alternate switches for an option,
        don't repeat metavar (which easily becomes lenghty and doesn't
        contain any new information) but use metavar2 instead;
        specify metavar=Null to get the old behaviour

    Untested: help text keys %choices and %xchoices
    """
    def __init__(self,
                 indent_increment=2,
                 max_help_position=24,
                 width=None,
                 short_first=1):
        optparse.IndentedHelpFormatter.__init__(self,
                                 indent_increment, max_help_position,
                                 width, short_first)
        self.choices_tag = "%choices"
        self.xchoices_tag = "%xchoices"
        self._mask_xchoices_1 = '%s: %s\r'
        self._mask_xchoices_2 = '%s (%s): %s\r'

    def default_option_metavar(self, option):
        try:
            mvf = getattr(option, 'default_metavar_'+option.action)
            return mvf(option)
        except AttributeError:
            return option.dest.upper()

    def format_option_strings(self, option):
        """\
        Return a comma-separated list of option strings (including metavar
        values, if any).

        If a 'metavar2' attribute is present and not Null,
        use this instead of metavar for the 2nd and all further versions.
        """
        if not hasattr(option, 'metavar2'):
            return optparse.IndentedHelpFormatter.format_option_strings(self, option)

        if option.takes_value():
            metavar = option.metavar or self.default_option_metavar(option)
            short_opts = [self._short_opt_fmt % (sopt, '%s')
                          for sopt in option._short_opts]
            long_opts = [self._long_opt_fmt % (lopt, '%s')
                         for lopt in option._long_opts]
            if self.short_first:
                opts = short_opts + long_opts
            else:
                opts = long_opts + short_opts

            def gen_mv(mv, mv2):
                """
                generate metavars
                """
                yield mv
                if mv2 is None:
                    while 1:
                        yield mv
                else:
                    assert str(mv2) # choke on empty string etc.
                    while 1:
                        yield mv2

            opts = [s % o
                    for (s, o) in zip(opts,
                                      gen_mv(metavar, option.metavar2))
                    ]
        elif self.short_first:
            opts = option._short_opts + option._long_opts
        else:
            opts = option._long_opts + option._short_opts

        return ", ".join(opts)

    def expand_help(self, option):
        """
        expand:
        %default (optparse.Option.expand_default)
        %choices
        """
        text = self._expand_default(option)
        import textwrap
        if option.xchoices is not None:
            text = text.replace(self.xchoices_tag,
                                '\r'+self._expand_xchoices(option))
        elif option.choices is not None:
            text = text.replace(self.choices_tag,
                                '\r'+self._expand_choices(option))
        return text

    def _expand_choices(self, option):
        """\
        simply return the replacement text for %choices
        """
        def up(choice):
            try:
                return (choice == option.default) and choice.upper() or choice
            except:
                return choice
        thelist = map(up, option.choices)
        return '%s oder %s' % (','.join(thelist[:-1]), thelist[-1])

    def _expand_xchoices(self, option):
        """
        xchoices: choices with help.
        No emphasition of %default value yet
        """
        res = ['',]
        i1 = " "*self.current_indent
        i2 = " "*(self.current_indent+self.indent_increment)
        import textwrap
        text_width = self.width - self.current_indent
        for ch, help in option.xchoices:
            if isinstance(ch, tuple) and len(ch) > 1:
                res.append(textwrap.fill(self._mask_xchoices_2 %
                                             (ch[0],
                                              ', '.join(ch[1:]),
                                              help),
                                         text_width,
                                         initial_indent=i1,
                                         subsequent_indent=i2))
            else:
                if isinstance(ch, tuple):
                    ch = ch[0]
                res.append(textwrap.fill(self._mask_xchoices_1 %
                                             (ch,
                                              help),
                                         text_width,
                                         initial_indent=i1,
                                         subsequent_indent=i2))
        res.append(i1)
        return ';\r'.join(res)

    def _expand_default(self, option):
        return optparse.HelpFormatter.expand_default(self, option)

    def expand_default(self, option):
        return self.expand_help(option)
        raise NotImplementedError('%r: use expand_help instead' % option)

OptionContainer = optparse.OptionContainer

class EnhancedOptionGroup(optparse.OptionGroup):
    pass

EnhancedOptionGroup.add_help_option = add_help_option

OptionGroup = EnhancedOptionGroup

class EnhancedOptionParser(optparse.OptionParser):
    """
    enhanced OptionParser class:

    - method set_collecting_group
    - uses EnhancedOption class by default
    - uses EnhancedHelpFormatter by default
    """

    def __init__(self,
                 usage=None,
                 option_list=None,
                 option_class=EnhancedOption,
                 version=None,
                 conflict_handler="error",
                 description=None,
                 formatter=None,
                 add_help_option=True,
                 prog=None,
                 epilog=None):
        """
        just a few defaults changed
        """
        if formatter is None:
            formatter = EnhancedHelpFormatter()
        done = 0
        if epilog is not None:
            try:
                optparse.OptionParser.__init__(self,
                         usage,
                         option_list,
                         option_class,
                         version,
                         conflict_handler,
                         description,
                         formatter,
                         add_help_option,
                         prog,
                         epilog)
                done = 1
            except TypeError:
                err(_('enhopa: epilog option ist not supported by optparse of '
                      'Python %d.%d.%d'
                      ) % sys.version_info[:3])
        if not done:
            optparse.OptionParser.__init__(self,
                     usage,
                     option_list,
                     option_class,
                     version,
                     conflict_handler,
                     description,
                     formatter,
                     add_help_option,
                     prog)

    def format_option_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        formatter.store_option_strings(self)
        result = []
        if self.option_list:
            result.append(formatter.format_heading(_("options")))
            formatter.indent()
            result.append(OptionContainer.format_option_help(self, formatter))
            result.append("\n")
        for group in self.option_groups:
            result.append(group.format_help(formatter))
            result.append("\n")
        if self.option_list:
            formatter.dedent()
        # Drop the last "\n", or the header if no options or option groups:
        return "".join(result[:-1])
    # OptionParser.format_option_help = format_option_help

    def set_collecting_group(opa, title='Everyday options', move=0):
        """
        to the calling OptionParser, add an OptionGroup with the given
        title and move all so-far added options to it.
        """
        ogr = None
        try:
            assert opa._collecting_group is None
        except AttributeError:
            pa = get_the_parser(opa)
            ogrcls = pa.option_group
            ogr = ogrcls(opa, title)
            opa.add_option_group(ogr)
            opa._collecting_group = ogr
        except AssertionError:
            if move:
                ogr = opa._collecting_group
            else:
                raise
        for o in opa.option_list:
            ogr.option_list.append(o)
        del opa.option_list[:]

    def get_collecting_group(opa):
        assert opa._collecting_group is not None
        return opa._collecting_group

    # OptionParser.set_collecting_group = set_collecting_group
    # OptionParser.get_collecting_group = get_collecting_group

OptionParser = EnhancedOptionParser

try:
    long
except NameError:
    long = int

_builtin_cvt_i18n = {
    "int" : (int, _("option %(opt)s: invalid integer value: %(value)r")),
    "long" : (long, _("option %(opt)s: invalid long integer value: %(value)r")),
    "float" : (float, _("option %(opt)s: invalid floating-point value: %(value)r")),
    "complex" : (complex, _("option %(opt)s: invalid complex value: %(value)r")),
                     }

class OptionValueError(optparse.OptionValueError):
    pass

def check_builtin(option, opt, value):
    (cvt, msg_string) = _builtin_cvt_i18n[option.type]
    try:
        return cvt(value)
    except ValueError:
        raise OptionValueError(_(msg_string) % locals())

Option = EnhancedOption

# OptionGroup

OptionError = optparse.OptionError

class Values(optparse.Values):
    def __getitem__(self, y):
        return self.__dict__.__getitem__(y)
    def __iter__(self):
        return self.__dict__.__iter__()
    def keys(self):
        return self.__dict__.keys()
    def iterkeys(self):
        return self.__dict__.iterkeys()
    def values(self):
        return self.__dict__.values()
    def itervalues(self):
        return self.__dict__.itervalues()
    def items(self):
        return self.__dict__.items()
    def iteritems(self):
        return self.__dict__.iteritems()

optparse.Values = Values

class HtmlHelpFormatter(EnhancedHelpFormatter):
    """
    create some smart HTML thingy containing the options help
    """
    def __init__(self):
        raise NotImplementedError

class HtmlTableHelpFormatter(HtmlHelpFormatter):
    """
    create an HTML table containing the options help
    """
    def __init__(self):
        raise NotImplementedError

if __name__ == '__main__':
    # TODO: line breaks/tabs in description
    descr = _('''\
A tweak to the optparse module, with the following enhancements:
- allows to collect the everyday options (for help, version etc.)
  in their own group, even when created by the __init__ method;
- if all options are grouped, the unnecessary "options:" headline is omitted;
- adding new actions easier (new action: decrease);
and more.'''
    )
    parser = OptionParser(version='%prog '+VERSION,
                          prog=progname(),
                          usage=_("""Typical fail-safe usage:
  try:
      from thebops.enhopa import OptionParser
  except ImportError:
      from optparse import OptionParser
  p = OptionParser(version='1.0')
  try:
      p.set_collecting_group()
  except AttributeError:
      pass
  p.add_option('--interesting-option', ...)
  option, args = p.parse_args()
"""))
    parser.set_description(descr)
    parser.add_option('-v', '--verbose', action='count')
    group_ = EnhancedOptionGroup(parser, 'Demo options')
    group_.add_option('-i', '--number',
                      action='store',
                      type='int',
                      help=_('specify an integer number'))
    group_.add_option('-u', '--increase',
                      dest='number',
                      action='count',
                      help=_('increase the --number ("up")'))
    group_.add_option('-d', '--decrease',
                      dest='number',
                      action='decrease',
                      help=_('decrease the --number ("down").  This action'
                      ' is not available in the standard optparse module'))
    group_.add_option('--number-five', '-5',
                      action='store_const',
                      const=5,
                      dest='number',
                      help=_('set number to 5'))
    choices=(('1', 'eins'),
             ('2', 'zwei'),
             )
    group_.add_option('--choose', '-c',
                      action='store',
                      type='int',
                      xchoices=choices,
                      metavar='|'.join([tup[0]
                                        for tup in choices]),
                      help=_('xchoices example (value: %r): %%xchoices'
                             ) % (choices,))
    group_.add_option('-x',
                      action='store')
    tmp_long = ('--option-one', '--option-two',)
    kwargs = dict(action='store',
                  help=_('an option with more than one long switches %r'
                         ) % (tmp_long,))
    group_.add_option(*tmp_long, **kwargs)
    group_.add_option('-s', '--string', action='store',
                      help=_('specify a string of characters'))
    parser.add_option_group(group_)
    parser.set_collecting_group()

    (option, args) = parser.parse_args()
    for o in option:
        print(' %s:\t%r' % (o, getattr(option, o)))

