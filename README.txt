README.TXT
~~~~~~~~~~

THeBoPS - Tobias Herp's Bag of Python Stuff
~~~~~~~---~------~~-----~---~--~------~----

This is a collection of Python modules I created over the years and improved
every now and then, while programming for fun at home.  Since I consider them
useful and like them a lot, I wanted to have them at work, too, and thus
created this package.

There are a few commandline scripts as well, which are currently only useful
(and thus only installed) on non-*x operating system like e.g. Windows(tm),
where the interpreter is not in the PATH by default:

- py2 - execute the "best" Python 2 interpreter (below v3.0)
- py3 - execute the "best" Python 3 interpreter

The Python interpreters are seeked in the default installation targets;
you can choose to install py2/py3 in you own tools directory
(e.g. setup.py --install-scripts=C:\Tools,
or pip install --install-option="--install-scripts=...")

This one doesn't do much on Linux which you couldn't do directly by
calling 'find', but it is useful on Windows:

- xfind - execute a *x style "find" program (if installed)


Contained modules are:

thebops.anyos
  Tries to help when developing portable programs; includes a find_progs
  function which helps e.g. a suitable *X "find" executable on Windows(tm)
  systems (if there is one installed; used by the xfind script);
  see thebops.likeix below.

thebops.colours
  Collects information about HTML, CSS, SVG colours;
  see colours_demo.

thebops.counters
  A module to help count whatever you want, including different types of
  errors, warnings etc.
  See counters_demo.

thebops.enhopa
  The "enhanced option parser"
  (almost entirely obsoleted by thebops.optparse; see below)
  The optparse/optik module is quite cool.  Some consider it outdated because
  of the newer argparse module; but argparse can't do everything optparse can
  (and vice versa), and thus both have their uses.
  The enhopa module does some minor tweaks to optparse; since optparse is
  "deprecated" now and won't be maintained beyond version 1.5.3 (to my
  knowledge, at least), I replace it step by step by thebops.optparse,
  to which the improvements can be applied much more easily.
  See thebops.opo as well, which (of course) doesn't care which flavour of
  optparse (including thebops.enhopa) is used.

thebops.errors
  An error handling module for console programs. To count the errors as well,
  use the thebops.counters module.

thebops.iscales
  Collects information about image scales and their names;
  see iscales_demo.

thebops.likeix
  Collects knowledge how to find certain *X conforming tools on Windows systems
  (but of course on *X as well, where they should be present in the PATH),
  using the find_progs function from thebops.anyos.
  Perhaps the best way to use this is the ToolsHub class;
  see likeix_demo.

thebops.modinfo
  A module which allows Python modules to tell about themselves.
  Can be used as a commandline tool (and is installed as such), or can be
  imported by a (thus self-documenting) module.  Can execute doctests, of
  course.

thebops.opo
  optparse options:  A collection of often used optparse option definitions,
  including some which use callback functions.
  Interesting for development: add_trace_option/DEBUG;
  see opo_demo.

thebops.optparse
  This module, of course, owes almost everything to the optparse/optik module
  by Greg Ward.  Some (for now) minor enhancements are applied; this copy is
  intended to obsolete the enhopa module (above) entirely.
  v1.6.5: action_... methods (add new actions by adding action_<name> methods,
  e.g. in derived classes), and a "decrease" action, complementing "count".
  The ACTIONS ... tuples must still be maintained.

thebops.rexxbi
  "REXX builtins"; some functions which are built-in to the scripting language
  REXX by Mike Cowlishaw, re-implemented in Python, e.g. "overlay" and the
  swiss army knife of string manipulation (when avoiding regular expressions),
  "translate".  The functions are documented by doctests.
  See rexxbi_demo.

thebops.shtools
  Some utilities for console programs, e.g. an "ask" function which
  understands choices specifications like "yes,sure:1;no,nope:0;always;never"
  which can be internationalized easily;
  see shtools_demo.

thebops.termwot
  This is "Tobias Herp's Terminal Waste of Time".
  Not very useful, but helps to make console programs a little bit more fun.
  See termwot_demo.

thebops.misc1
  This module contains a few functions and classes for which I couldn't find
  a better place yet; eventually they might be moved.  There is a policy about
  how long you can rely on the location, though.


Final remark:
~~~~~~~~~~~~
  This package is not fully internationalized yet, but no effort is spared, and
  I'm quite eager to get this done.  Strings are marked for translation, babel
  finds them, and the first Gettext catalogue (hey, this is Europe!) is
  created.  Any help to make my distribution package use it is appreciated ...

  Meanwhile it helps to understand some German.

  BTW, there is nothing wrong with that:
  It's better (by far!) to document your code well in your own language than to
  write nonsense in a foreign one (and trust me, I know what I'm talking about.
  Some past and present colleagues of mine prove this every single day.)
  The only point in which I strictly disagree with PEP 8.

  Oh, and - since several people have downloaded my package by now:
  Of course I'm interested to know which parts are most interesting to you,
  which you actually use in your private or published projects,
  and what you think about them!

  Tobias Herp
