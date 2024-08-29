#!/usr/bin/python
"""\
thebops.modinfo: Python module to enable modules to tell about themselves
"""

__author__ = "Tobias Herp <tobias.herp@gmx.net>"

try: _
except NameError:
    def _(s): return s

__usage__ = _("""
In your Python module:

if __name__ == '__main__':
    from thebops.%(prog)s import main as %(prog)s
    # optionally specify version and usage info for your module:
    %(prog)s(version=VERSION,
                 usage=USAGE)

... or use as a commandline tool to introspect other modules:

%(prog)s [-fdct] [other options] [module] [...]\
""")

VERSION = '.'.join(map(str,
                       (0,
                        4, # module filtering
                        6, # thebops.base, thebops.optparse
                        'rev-%s' % '$Rev: 970 $'[6:-2],
                        )))

from thebops.opo import get_the_parser, add_trace_option, DEBUG

# TODO:
# * introspection:
#   - for pairs of identical functions, print once and refer to it
#   - handle modules separately
# * classtree:
#   - --implicit-object
#     + simply ignore the 'object' parent might not work, since
#       it could be added explicitly later, and in this case its
#       children won't be complete
# * misc.:
#   - cleanup
#   - import from packages
#   - prepare for nestable OptionGroups
#   - work out usage of verbosity levels
#   - i18n
#   - futher doctest options incl. --doctest-help?
# BUGS:
# * classtree:
#   When filtering, parents of skipped classes can remain, despite
#   the children which caused their addition are gone (or invisible).
#   Strategy:
#   - implicitly/explicitly added class objects?
# DONE:
# * introspection:
#   - skip foreign functions and objects (from imported modules;
#                                         option.include_imported)
#     -> refactoring of categorized() function required
# * classtree
#   - package/module/builtin info (important for --classtree)
# * misc.:
#   - filtering by name
#   - make ClassForest iterable (do the same for ClassNode?)
#   - hide not-yet-working options

from sys import stdout, stderr, exit, argv, exc_info
from os import linesep
from os.path import basename
from inspect import getmro, \
        getargspec, \
        isclass, isfunction, ismodule, isbuiltin, \
        getmembers, getsourcefile, getmodule

from thebops.optparse import OptionParser, OptionGroup, OptionConflictError
from thebops.base import progname
from thebops.errors import err, info, warn, check_errors

try:
    set
except NameError:
    from sets import Set as set

def _(s):
    """dummy i18n function"""
    return str(s)

def getdoc(o):
    """
    inspect.getdoc dedents the lines;
    this version is simpler, but usually Does The Right Thing
    """
    try:
        doc = o.__doc__
    except AttributeError:
        return None
    return doc and doc.strip()

def _get_collecting(parser):
    """
    return a parser object which supports the set_collecting_group method
    (from the enhopa module) or None
    """
    use = get_the_parser(parser)
    try:
        use.set_collecting_group
        return use
    except AttributeError:
        return None

def _add_classes_option(parser):
    parser.add_option('-c', '--classes',
                      action='store_true',
                      help=_('tell about classes; base classes are listed'
                      ' in method resolution order.'
                      ' See also --classtree (below)'))

def _add_functions_option(parser):
    parser.add_option('-f', '--functions',
                      action='store_true',
                      help=_('tell about functions'))

def _add_module_option(parser):
    parser.add_option('-m', '--modules',
                      action='store_true',
                      help=_('tell about modules'))

def _add_data_option(parser):
    parser.add_option('-d', '--data',
                      action='store_true',
                      help=_('tell about data'))

def cb_all(option, opt_str, value, parser):
    for o in 'classes functions data'.split():
        setattr(parser.values, o, 1)

def _add_all_option(parser):
    parser.add_option('-a', '--all',
                      action='callback',
                      callback=cb_all,
                      help=_('tell about everything provided by the module'
                      ' (grouped by type)'
                      '; like -cfd'))

def _add_all2_option(parser):
    parser.add_option('-A',
                      action='count',
                      dest='include_all',
                      help=_('show *all* entries, disregarding the __all__ '
                      'attribute'))

def _add_imported_options(parser):
    parser.add_option('--skip-imported',
                      action='store_false',
                      dest='include_imported',
                      help=_('exclude imported objects from the list, as'
                      ' far as possible (for classes and functions; default). '
                      ' For --classtree, imported base'
                      ' classes are still contained.')
                      )
    parser.add_option('--include-imported', '-I',
                      action='store_true',
                      dest='include_imported',
                      help=_('include imported objects; negates --skip-'
                      'imported'))
    return      # not yet implemented

def _add_classtree_options(parser):
    """
    options for the classtree functionality
    """
    parser.add_option('-t', '--classtree',
                      action='store_true',
                      help=_('tree (or forest) view of classes'))
    parser.add_option('-u', '--unique-classes',
                      action='count',
                      dest='unique_classes',
                      default=0,
                      help=_('for multiple inheritance; you may specify this'
                      ' option multiple times:\n'
                      '-u, to skip the children of a class node when it is'
                      ' visited the 2nd and following times in a tree;\n'
                      '-uu, to regard the occurences in the whole forest;\n'
                      '-uuu, to *really* have every node only once.'))
    return      # not yet implemented
    parser.add_option('-o', '--implicit-object',
                      action='store_true',
                      dest='implicit_object',
                      help=_('include the "object" class even when not'
                      ' explicitly stated in list of classes (but only'
                      ' added to the parents by the inspect module).'
                      ' This is currently ALWAYS the case, but it shouldn\'t.'
                      ' Will for certain forests affect the number of trees'
                      ' and the difference between -u and -uu.'))

def _add_filter_option(parser):
    parser.add_option('--filter',
                      action='store',
                      metavar='REGEX',
                      help=_('filter entries of interest by name'
                      ' (specify a regular expression)'))

def _add_ignorecase_options(parser):
    parser.add_option('--ignore-case',
                      action='store_true',
                      dest='ignore_case',
                      default=True,
                      help=_('ignore case when filtering (default)'))
    parser.add_option('--dont-ignore-case',
                      action='store_false',
                      dest='ignore_case',
                      help=_('regard case when filtering'
                      ' (negates --ignore-case)'))

def _add_inversion_option(parser):
    parser.add_option('--invert-match',
                      action='store_true',
                      dest='invert_match',
                      help=_('invert match'))

def _add_doctest_options(parser):
    vector = ['--doctest']
    kwargs = dict(action='store_true',
                  dest='doctest',
                  help=_('execute doctests (if any)'))
    while vector:
        try:
            parser.add_option(*tuple(vector), **kwargs)
            break
        except OptionConflictError:
            vector.pop()
            if not vector:
                return
    _add_verbosity_options(parser)

def _add_test_group(parser):
    _group = OptionGroup(parser, _('Tests'))
    _add_doctest_options(_group)
    parser.add_option_group(_group)

_module_support_enabled = 0  ## modules don't seem to work
def _add_modinfo_options(parser):
    _add_classes_option(parser)
    _add_functions_option(parser)
    if _module_support_enabled:
        _add_module_option(parser)
    _add_data_option(parser)
    _add_all_option(parser)
    _add_all2_option(parser)
    _add_imported_options(parser)
    _add_filter_option(parser)
    _add_ignorecase_options(parser)
    _add_inversion_option(parser)
    _add_classtree_options(parser)

def _add_trivial_options(parser, version=None):
    # for another approach, see thebops.opo.add_help_option
    # and ...add_version_option
    vector = ['--help', '-?', '-h']
    kwargs = dict(action='help',
                  help=_('show this help message and exit'))
    while vector:
        try:
            parser.add_option(*tuple(vector), **kwargs)
            break
        except OptionConflictError:
            vector.pop()
    _add_verbosity_options(parser)
    if version is not None:
        add_to = get_the_parser(parser)
        add_to.version = version
        vector = ['--version', '-V']
        kwargs = dict(action='version',
                      help=_('show the version and exit'))
        while vector:
            try:
                parser.add_option(*tuple(vector), **kwargs)
                break
            except OptionConflictError:
                vector.pop()

def _add_verbosity_options(parser):
    # for another approach, see thebops.opo.add_verbosity_options
    vector = ['--verbose', '-v']
    kwargs = dict(action='count',
                  default=0,
                  help=_('increase verbosity'))
    while vector:
        try:
            parser.add_option(*tuple(vector), **kwargs)
            break
        except OptionConflictError:
            vector.pop()

def module_match(tup, mod):
    """
    check the (k, o) tuple, if the module (if any) matches mod
    """
    k, o = tup
    m = getmodule(o)
    if m is None:
        return 1
    return m is mod

def _sf_false(s):
    return 0

def _sf_byprefix(s):
    return s.startswith('_')

def module_dict(mod, droptuples, opt):
    """
    take a module and return a dictionary, containing
    lists and module information

    mod -- the module
    droptuples -- a function to filter the sequence
    """
    global _global_classlist, _global_modules
    _global_modules.append(mod)     # for --classtree
    seq = getmembers(mod)
    _c, _f, _d, _m = list(), list(), list(), list()
    if droptuples:
        seq = filter(droptuples, seq)
    if not opt.include_imported:
        seq = [tup
               for tup in seq
               if module_match(tup, mod)]
    seq.sort()
    do_filter = not opt.include_all
    if do_filter:
        try:
            ALL = getattr(mod, '__all__')
            skipfunc = lambda s: s not in ALL
            if not isinstance(ALL, (list, tuple)):
                err(_('__all__ attribute of module of wrong type (%r)'
                      ) % (ALL,))
            elif not ALL:
                warn(_('__all__ attribute is empty'))
        except AttributeError:
            skipfunc = _sf_byprefix
            if opt.verbose:
                info(_('module %s lacks an __all__ attribute'
                       ) % mod.__name__)
    else:
        skipfunc = _sf_false
    for k, o in seq:
        if skipfunc(k):
            continue
        if isclass(o):
            _c.append((k, o))
            _global_classlist.append(o)
        elif isfunction(o):
            _f.append((k, o))
        elif _module_support_enabled and ismodule(o):
            _f.append((k, o))
        else:
            _d.append((k, o))
    return {'classes':   _c,
            'functions': _f,
            'modules':   _m,
            'data':      _d,
            'mod_name':  mod.__name__,
            'module':    mod,
            }

def base_classes(cls):
    """
    return the names of the base classes in method resolution order,
    excluding the given class
    """
    res = []
    for p in getmro(cls):
        if not p in (object, cls):
            res.append(p.__name__)
    return res

def list_classes(classes, filt=None):
    """
    take a list of (name, class) tuples and print a list.

    Options:
    filt -- an optional function to filter a sequence of (name, object) tuples
    """
    if not classes:
        print _('sorry, no classes')
        print
        return
    if filt:
        classes = [(n, o)
                   for n, o in classes
                   if filt.match(n)]
        if not classes:
            print _('sorry, no matching classes')
            print
            return
    print _('classes:')
    for n, o in classes:
        doc = getdoc(o)
        parents = base_classes(o)
        print '  %s%s%s%s' % (
                n,
                parents and '(%s)' % ', '.join(parents) or '',
                doc and ':\n    ' or '\t',
                doc or _('(sorry, no docstring)'),
                )

def pretty_args(fo):
    """
    return a pretty string, representing the argument specification
    for the given function object
    """
    names, args, kwargs, defaults = getargspec(fo)
    if names:
        names = list(names)
    if defaults:
        defaults = list(defaults)
    res = list()
    while defaults:
        dflt = defaults.pop()
        name = names.pop()
        res.insert(0, '%s=%r' % (name, dflt))
    while names:
        res.insert(0, names.pop())
    if args:
        res.append('*'+args)
    if kwargs:
        res.append('**'+kwargs)
    return '(%s)' % ', '.join(res)

def print_headline(txt, ch='~'):
    print txt
    print ch * len(txt)

def generic_list(tuples, headline, func, filt=None, modname=None):
    """
    take a list of (name, object) tuples and print the human-readable list

    Options:
    tuples   -- a sequence of (name, object) tuples
    headline -- category of objects, e.g. 'functions:'
    func     -- a printing function, suitable for the given category
    filt     -- a boolean function as a filter for the sequence (optional)
    modname  -- the name of the module (optional)
    """
    if not modname:
        print_headline(headline)
        if not tuples:
            print _('  (none)')
            print
            return
        if filt:
            tuples = filter(filt, tuples)
            if not tuples:
                print _('  (none matching)')
                print
                return
        for tup in tuples:
            func(*tup)
        print
    else:
        if not tuples:
            return
        if filt:
            tuples = filter(filt, tuples)
            if not tuples:
                return
        kwargs = {'modname': modname,
                  }
        for tup in tuples:
            func(*tup, **kwargs)
        print

def print_class(name, obj):
    doc = getdoc(obj)
    parents = base_classes(obj)
    print '  %s%s%s%s' % (
            name,
            parents and '(%s)' % ', '.join(parents) or '',
            doc and ':\n    ' or '\t',
            doc or _('(sorry, no docstring)'),
            )
    print

def print_function(name, obj):
    doc = getdoc(obj)
    print '  %s%s%s%s' % (
            name,
            pretty_args(obj),
            doc and ':\n    ' or '\t',
            doc or _('(sorry, no docstring)'),
            )
    print

def print_module(name, obj):
    doc = getdoc(obj)
    print '  %s%s%s%s' % (
            name,
            pretty_args(obj),
            doc and ':\n    ' or '\t',
            doc or _('(sorry, no docstring)'),
            )
    print

def print_data(name, obj):
    try:
        print '  %-13s\t%r\t(%s)' % (
                name+':',
                obj,
                obj.__class__.__name__,
                )
    except AttributeError:
        print '  %-13s\t%r' % (
                name+':',
                obj,
                )

def print_class2(name, obj, modname):
    doc = getdoc(obj)
    parents = base_classes(obj)
    print '  %s.%s%s%s%s' % (
            modname,
            name,
            parents and '(%s)' % ', '.join(parents) or '',
            doc and ':\n    ' or '\t',
            doc or _('(sorry, no docstring)'),
            )
    print

def print_function2(name, obj, modname):
    doc = getdoc(obj)
    print '  %s.%s%s%s%s' % (
            modname,
            name,
            pretty_args(obj),
            doc and ':\n    ' or '\t',
            doc or _('(sorry, no docstring)'),
            )
    print

def print_module2(name, obj, modname):
    doc = getdoc(obj)
    print '  %s.%s%s%s%s' % (
            modname,
            name,
            pretty_args(obj),
            doc and ':\n    ' or '\t',
            doc or _('(sorry, no docstring)'),
            )
    print

def print_data2(name, obj, modname):
    try:
        print '  %-13s\t%r\t(%s)' % (
                modname+'.'+name+':',
                obj,
                obj.__class__.__name__,
                )
    except AttributeError:
        print '  %-13s\t%r' % (
                modname+'.'+name+':',
                obj,
                )

def show_filter(o):
    return o.verbose >= 1

def make_re_filters(o):
    """
    take the options object
    and return a 2-tuple (str_filter, tuple_filter) of functions:

    str_filter -- takes a string and returns a boolean value
    tuple_filter -- takes a tuple and returns a boolean value
    """
    import re, sre_constants
    re_options = 0
    if o.ignore_case:
        re_options |= re.IGNORECASE
    if not o.filter.startswith('^'):
        o.filter = '.*'+o.filter
    if not o.filter.endswith('$'):
        o.filter += '.*'
    try:
        REGEX = re.compile(o.filter, re_options)
    except sre_constants.error:
        err(_('Error compiling regular expression %r') % o.filter)
        return
    if o.invert_match:
        if show_filter(o):
            info(_('filtering entries for not matching "%s"') % o.filter)
        return (lambda s: not REGEX.match(s),
                lambda t: not REGEX.match(t[0]),
                )
    else:
        if show_filter(o):
            info(_('filtering entries for "%s"') % o.filter)
        return (lambda s: REGEX.match(s) and True or False,
                lambda t: REGEX.match(t[0]) and True or False,
                )

def handle_dict(dic, o, tuple_filt, modname=None):
    """
    called by main; options:

    dic -- a dictionary of lists of (name, object) tuples
    o -- the option object
    tuple_filt -- a boolean function for tuples
    modname -- the module name (optional)
    """
    if o.classes:
        generic_list(dic['classes'],
                     ""'Classes:',
                     modname and print_class2 or print_class,
                     tuple_filt,
                     modname)
    if o.functions:
        generic_list(dic['functions'],
                     ""'Functions:',
                     modname and print_function2 or print_function,
                     tuple_filt,
                     modname)
    if _module_support_enabled and o.modules:
        generic_list(dic['modules'],
                     ""'Modules:',
                     modname and print_module2 or print_module,
                     tuple_filt,
                     modname)
    if o.data:
        generic_list(dic['data'],
                     ""'Data:',
                     modname and print_data2 or print_data,
                     tuple_filt,
                     modname)
    try:
        if o.doctest:
            import doctest
            doctest.testmod(dic['module']
                            , verbose=bool(o.verbose)
                            )
    except AttributeError:
        pass

def no_leading_underscore(tup):
    return not tup[0].startswith('_')

def accept_any(tup):
    return 1

def mark_last(seq):
    """
    iterate a sequence and yield (is_last, o) tuples,
    with is_last being 0 for all but the last element

    >>> list(mark_last('abc'))
    [(0, 'a'), (0, 'b'), (1, 'c')]
    """
    first_done = 0
    for next in seq:
        if first_done:
            yield 0, prev
        else:
            first_done = 1
        prev = next
    if first_done:
        yield 1, next

class ClassNode:
    """
    a node, storing a class in a ClassForest,
    suitable for filtered classtrees
    """
    # _order = None

    def __init__(self, forest, co, parents=None, match_func=None):
        """
        forest -- the ClassForest object. *Might go away!*
        co -- the class object
        parents -- a tuple of class objects
        match_func -- not stored in the ClassNode
        """
        assert isinstance(forest, ClassForest)
        self._name = co.__name__
        self._matches = (match_func is None) or match_func(self._name)
        self._set_module_info(co)
        self._set_order_attribute()
        self._parents = list()
        self._children = list()
        for p in parents or ():
            self.add_parent(p)

    def _set_module_info(self, co):
        """
        co -- the class object

        sets the attributes _module, _mod_info and (boolean) _builtin.
        The inspect.isbuiltin function doesn't work for classes.
        """
        mod = getmodule(co)
        self._module = mod
        m_name = mod.__name__
        self._builtin = m_name == '__builtin__'
        if self._builtin or m_name == '__main__':
            self._mod_info = ''
            return
        pkg = mod.__package__
        if pkg:
            self._mod_info = '%s.%s.' % (pkg.__name__, m_name)
        else:
            self._mod_info = '%s.' % (m_name,)

    def _set_order_attribute(self):
        self._order = (not self._builtin,
                       self._name,
                       self._mod_info,
                       )

    def __str__(self):
        """
        the name of the class; might be extended to tell about
        the module, too
        """
        return ''.join((self._mod_info,
                        self._name,
                        self._builtin and ' (built in)' or ''))
        return self._name

    def shortname(self):
        return ''.join((self._mod_info,
                        self._name,
                        ))

    def longname(self, skip_parent=None):
        """
        the name of the class, and an information about the parents, if
        more than one
        """
        if len(self._parents) < 2:
            p_info = ''
        else:
            pl = list()
            for p in self._parents:
                if p is skip_parent:
                    pl.append(PARENT_ABBREV)
                else:
                    pl.append(p.shortname())
            p_info = '(%s)' % ', '.join(pl)
        return '%s%s' % (self, p_info)

    def _add_child(self, node):
        if not node in self._children:
            self._children.append(node)

    def add_parent(self, node):
        if not node in self._parents:
            self._parents.append(node)
            node._add_child(self)

    def is_interesting(self):
        return self._matches or self._has_interesting_children()

    def _has_interesting_children(self):
        for child in self._children:
            if child.is_interesting():
                return 1
        return 0

    def is_root_node(self):
        return not self._parents

    def tree_strings(self, prefix='', prefix2='', parent=None, visited=None):
        """
        node traversal and string generation.

        prefix, prefix2 -- ASCII graphics, drawing a tree structure
        parent -- allows to abbreviate the parent class which arises from
                  the tree anyway
        visited -- ignored in this class (needed in UniqueClassNode etc.)
        """
        if not self.is_interesting():
            return
        yield prefix + self.longname(parent)
        children = [child
                    for child in self._children
                    if child.is_interesting()]
        children.sort()
        for islast, child in mark_last(children):
            for s in child.tree_strings(prefix2+PREFIX['child'][islast],
                                        prefix2+PREFIX['grandchild'][islast],
                                        self):
                yield s

    def __cmp__(self, other):
        return cmp(self._order, other._order)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self._name)

class UniqueClassNode(ClassNode):
    """
    like ClassNode, but the tree_strings method won't yield
    the children of a node visited the 2nd (or 3rd...) time
    """
    def tree_strings(self, prefix='', prefix2='', parent=None,
                     visited=None):
        if not self.is_interesting():
            return
        yield prefix + self.longname(parent)

        # skip children from 2nd visit on
        if visited is None:
            visited = list()
        if self in visited:
            return
        visited.append(self)

        children = [child
                    for child in self._children
                    if child.is_interesting()]
        children.sort()
        for islast, child in mark_last(children):
            for s in child.tree_strings(prefix2+PREFIX['child'][islast],
                                        prefix2+PREFIX['grandchild'][islast],
                                        self, visited):
                yield s

class VeryUniqueClassNode(UniqueClassNode):
    """
    like UniqueClassNode, but the tree_strings method really won't yield
    the same node twice.
    Since not just children are involved, care must be taken for the
    prefixes
    """
    def __init__(self, forest, co, parents=None, match_func=None):
        UniqueClassNode.__init__(self, forest, co, parents, match_func)
        self._visited = 0

    def is_interesting(self):
        if self._visited:
            return 0
        return UniqueClassNode.is_interesting(self)

    def tree_strings(self, prefix='', prefix2='', parent=None,
                     visited=None):
        if not self.is_interesting():
            return

        self._visited = 1

        yield prefix + self.longname(parent)

        children = [child
                    for child in self._children
                    if child.is_interesting()]
        children.sort()
        for islast, child in mark_last(children):
            for s in child.tree_strings(prefix2+PREFIX['child'][islast],
                                        prefix2+PREFIX['grandchild'][islast],
                                        self, visited):
                yield s

# indexed by option.unique_classes:
NODECLASS = [ClassNode,
             UniqueClassNode,
             UniqueClassNode,
             VeryUniqueClassNode,
             ]

show_docstring, show_nodocstring = dict(), dict()
show_docstring['classes']   = lambda o: o.verbose > 0
show_docstring['functions'] = show_docstring['classes']
show_docstring['data']      = show_docstring['classes']
show_nodocstring['classes']   = lambda o: o.verbose > 1
show_nodocstring['functions'] = show_nodocstring['classes']
show_nodocstring['classes']   = lambda o: o.verbose > 2

class ClassForest:
    """
    A bunch of class trees, built from ClassNodes.
    Intended usage: build trees from a sequence of classes,
    then show a tree (or forest) view

    You can print your ClassForest directly, or you can iterate it
    and print the lines one at a time (and insert e.g. line numbers).
    """
    def __init__(self,
                 classes,
                 unique=0,
                 filter_func=None,
                 nodeclass=ClassNode):
        """
        classes -- a sequence of class objects
                   (handed over to inspect.getclasstree)
        unique -- if 1, classes with more than one direct parent
                  occur only once (default: 0)
        filter_func -- a function to tell whether or not the classname
                       matches the optional filter expression
        nodeclass -- the class of the nodes; ClassNode or a subclass
        """
        assert issubclass(nodeclass, ClassNode)
        from inspect import getclasstree
        self.unique = unique
        self.filter_func = filter_func
        self.nodeclass = nodeclass
        self._co_node = dict()
        self._eat_classtree(getclasstree(classes), parent=None)

    def _eat_classtree(self, classes, parent):
        local_parent = None
        for l_or_t in classes:
            if isinstance(l_or_t, tuple):
                local_parent = self._checkNode(*l_or_t)
            else:
                assert isinstance(l_or_t, list)
                assert local_parent
                self._eat_classtree(l_or_t, local_parent)

    def _checkNode(self, co, pt=()):
        """
        look up the given class object;
        if already present, return the correspoding ClassNode,
        otherwise create it first

        co -- the class object (from an inspect.getclasstree tuple)
        pt -- the tuple of parents (dto.)
        """
        parents = [self._checkNode(p) for p in pt]
        try:
            node = self._co_node[co]
            for p in parents:
                node.add_parent(p)
        except:
            node = self.nodeclass(self, co, parents, self.filter_func)
            self._co_node[co] = node
        return node

    def __len__(self):
        return len(self._co_node)

    def __iter__(self):
        roots = [node
                 for node in self._co_node.values()
                 if node.is_root_node()
                 and node.is_interesting()]
        roots.sort()
        if self.unique:
            visited = list()
        else:
            visited = None
        for root in roots:
            for s in root.tree_strings('', '', None, visited):
                yield s

    def __str__(self):
        return linesep.join(list(self))

_global_classlist = None
_global_modules = None   # to distinguish explicitly imported modules
PARENT_ABBREV = '*'
PREFIX = dict()        # all but... last
PREFIX['child'] =      ['+- ',      '`- ']
PREFIX['grandchild'] = ['|  ',      '   ']

def refine_usage(s, ndict):
    """
    return a refined usage string, using the given namespace

    s -- the usage string, containing something like %prog *or* %(prog)s

    ndict -- the namespace, e.g. locals()
    """
    assert isinstance(ndict, dict), '%r: dict expected' % ndict
    try:
        return s % ndict
    except KeyError:
        raise
    except ValueError:
        if '%(' in s:
            raise
        s = s.replace('%prog', '%(prog)s')
        return s % ndict

def main(version=None,
         parser=None,
         usage=None,
         droptuples=None,
         doctest=1):
    """
    Tell about the calling module, using the optparse and inspect modules.

    Options:
    version --  the version argument
    parser --   an OptionParser or OptionGroup object (if None given,
                the function takes care of this itself);
                if you create the parser object yourself,
                you must take care of the --version and --help options
                yourself, and of the usage string as well
    usage --    a usage info string about the calling module.
                If none is given, and a given parser has the default usage
                string (unsuitable for modules), a default version is used
    droptuples -- boolean function (for filter function);
                None by default, since the __all__ attribute / leading
                underscore rule is executed via the -A option
    doctest --  if True, create a --doctest option
    """
    global _global_classlist, _global_modules

    _global_classlist = list()
    _global_modules = list()

    def get_main_module():
        return __import__('__main__')
        return getmembers(__import__('__main__'))

    def default_usage(demo=False):
        return ('import %%(prog)s | %%%%prog {%sintrospection options}'
                % (demo and 'demo/' or ''))

    ## ------------------------------------------- create OptionParser
    create_group = None
    parser_given = parser is not None
    from thebops.optparse import OptionParser, OptionGroup, OptionConflictError
    prog = progname()
    if not parser_given:
        parser = OptionParser(add_help_option=False,
                              # prog=proginfo(),
                              usage=refine_usage(usage or default_usage(),
                                                 locals()))
        pa = parser
        h = OptionGroup(pa, 'hidden options')
        add_trace_option(h)
    else:
        pa = get_the_parser(parser)
        if usage or pa.usage == '%prog [options]':
            pa.set_usage(refine_usage(usage or default_usage(1),
                                      locals()))
    del prog
    collect_on = _get_collecting(parser)
    try:
        parser.add_option_group
        create_group = 1
    except AttributeError:
        create_group = 0

    if create_group:    # Parser uebergeben oder erzeugt
        _group = OptionGroup(parser, _('Module introspection'))
        _add_modinfo_options(_group)
        parser.add_option_group(_group)
        if doctest:
            _add_test_group(parser)
            doctest = 0 # done

    if parser_given:
        if collect_on:
            _add_trivial_options(collect_on, version)
            collect_on.set_collecting_group()
        else:
            _add_trivial_options(pa, version)
        if not create_group:
            _add_modinfo_options(parser)
            if doctest:
                _add_doctest_options(parser)
    else:
        assert create_group, ('kein Parser o.ae. uebergeben, also'
                'haette ein OptionParser erzeugt sein und create_group '
                'True sein muessen!')
        if doctest:
            _add_test_group(pa)
        _group = OptionGroup(pa, _('Everyday options'))
        _add_trivial_options(_group, version)
        pa.add_option_group(_group)

    option, args = parser.parse_args()
    DEBUG() # -TT?

    ## ------------------------------------ evaluate and check options
    if option.filter:
        s_filt, t_filt = make_re_filters(option)
    else:
        s_filt, t_filt = None, None

    DEBUG() # -T?
    if __name__ not in ('__main__', 'thebops.modinfo'):
        if args and not parser_given:
            err(_('surplus arguments: %s') %
                    ', '.join([repr(a)
                               for a in args]))
    doctest = 0
    try:
        if option.doctest:
            doctest = 1
    except AttributeError:
        pass

    something_to_do = bool(option.classes or option.functions or option.data or
            # option.modules or
            doctest or
            option.classtree
            )
    if not (something_to_do or parser_given):
        err(_('nothing to do (specify at least one of -cfdt, or --all)'))
    if option.unique_classes > 3:
        info(_('%d -u(s) ignored') % (option.unique_classes - 3))
        option.unique_classes = 3

    check_errors()

    ## --------------------------- handle the module(s) like requested
    def nontree_action(o):
        return (o.classes or o.functions or o.data)

    DEBUG() # -T?
    if args and __name__ == '__main__':
        done = set()
        for m in args:
            if m in done:
                continue
            done.add(m)
            if m == '.':
                if nontree_action(option):
                    print_headline(_('module %s (current):') % progname(), '=')
                dic = module_dict(get_main_module(), droptuples, option)
            else:
                if nontree_action(option):
                    print_headline(_('module %s:') % m, '=')
                try:
                    the_module = __import__(m)
                except ImportError, e:
                    err(_('error %(e)s importing module %(m)s'
                          ) % locals())
                    continue
                dic = module_dict(the_module, droptuples, option)
            handle_dict(dic, option, t_filt)
    else:
        dic = module_dict(get_main_module(), droptuples, option)
        handle_dict(dic, option, t_filt)

    ## --- display a class forest for classes from all handled modules
    if option.classtree:
        print_headline(_('Class forest:'))
        ct = ClassForest(_global_classlist,
                         unique=option.unique_classes > 1,
                         nodeclass=NODECLASS[option.unique_classes],
                         filter_func=s_filt)
        for line in ct:
            print line
    if parser_given:
        if something_to_do:
            raise SystemExit
        else:
            return (option, args)

# not executed when imported:
if __name__ == '__main__':
    _g = globals()  # ???
    prog = progname()
    main(version='%prog '+VERSION,
         usage=__usage__ % locals())

# vim: tabstop=8 softtabstop=4 expandtab smartindent shiftwidth=4 textwidth=79
