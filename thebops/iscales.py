# -*- coding: utf-8 -*- vim: sw=4 sts=4 ts=8 et ft=python
"""
Python module for image dimensions
"""
__version__ = (0,
               6, # CSS colour parsing moved to colours module
               5, # small bugfix
               'rev-%s' % '$Rev: 1088 $'[6:-2],
               )

import os.path
from sys import stderr, exit

from thebops.optparse import OptionValueError, OptParseError
# TODO: replace
from thebops.errors import fatal, warning

__all__ = ('add_scale_option', 'add_scale_helpers',
           'add_cut_option',
           'add_resampling_option',
           'add_clockwise_option',
           'scales',
           'CSS_CLOCK',
           'importIntFromPIL',
           'outFileName',
           # factories:
           'clip_arg',
           # mirrors:
           'mirror_auto',
           'mirror_zero',
           # info/debugging:
           'clockwise_info',
           # exceptions:
           'IscalesError',
           'FormatRegistryError',
           'DuplicateKeyError',
           'InsufficientSpecsError',
           # data:
           'DOCSTRING',
           'USAGE',
           'HELP_RC',
           )

try:
    set
except NameError:
    from sets import Set as set

try:
    _
except NameError:
    def _(s): return s


__author__ = 'Tobias Herp <tobias.herp@gmx.de>'
USAGE = """
Typical usage:

  from optparse import OptionParser, OptionGroup    # or thebops.optparse
  from thebops.iscales import add_scale_option, add_scale_helpers

  parser = OptionParser()
  group_ = OptionGroup(parser, 'Interesting options')
  add_scale_option(group_)    # adds a '--scale' option
  parser.add_option_group(group_)

  group_ = OptionGroup(parser, 'Image format help')
  add_scale_helpers(group_)
  parser.add_option_group(group_)

  option, args = parser.parse_args()

  print option.scale
"""
DOCSTRING = __doc__

HELP_RC = 1

class IscalesError(Exception):
    """
    root class of the exceptions hierarchy of the iscales module
    """
    def set_message(self):
        self.message = str(self)

class InsufficientSpecsError(IscalesError, AssertionError):
    pass

class FormatRegistryError(IscalesError):
    pass

class DuplicateKeyError(FormatRegistryError):
    pass

class NoSuchDataError(IscalesError, ValueError):
    """\
    The ValueError of the thebops.iscales module
    """

class NoResolutionsForLines(NoSuchDataError):
    def __init__(self, lines):
        self.lines = lines
        self.args = (lines,)
        self.set_message()

    def __str__(self):
        return _('No known resolutions with %r lines'
                 ) % self.lines


def outFileName(inf, outf='',
                img=None, sc=None,
                force_dimensions=0,
                dimname=None):
    """
    return a (full) file name for the new image:

    inf -- the input file name (mandatory)

    outf -- the output file name

    img -- the image object. Needed, if the actual size of the image
           is to be used for the file name

    sc -- the scale tuple (width, height). Needed, if the maximum
          size of the image is to be used for the file name

    force_dimensions -- insert the dimensions into the name, even if
          it wouldn't be necessary to distinguish it from the input name

    dimname -- dimension name (instead of WIDTHxHEIGHT, if "forced")

    if outf is != '', use it. If outf is the name of a directory,
    append the file part of inf
    """
    if outf:
        if outf.endswith(os.path.sep):
            outf += os.path.split(inf)[1]
        elif os.path.exists(outf):
            if os.path.isdir(outf):
                outf = os.path.sep.join((outf,os.path.split(inf)[1]))
        if not force_dimensions:
            return outf
        elif not (img or sc):
            raise InsufficientSpecsError('specify image object or scale '
                                         'tuple, or drop force_dimensions')
    elif not (img or sc):
        raise InsufficientSpecsError('at least outfile, image object'
                                     ' or scale tuple needed')
    else:
        outf = inf
    if dimname:
        size_info = '-%s' % dimname
    elif img:
        size_info = '-%dx%d' % img.size
    elif sc:
        try:
            size_info = '-%dx%d' % sc
        except TypeError:
            raise InsufficientSpecsError('sc must contain exactly two integers')
    else:
        raise AssertionError('Image or scale tuple is specified, isn\'t it?!')
    return size_info.join(os.path.splitext(outf))

def reduce(z, n):
    """
    reduce a fraction by dividing both numbers by the primes 2, 3, 5, and 7
    (which is sufficient for the common screen resolutions), and return the
    reduced tuple

    >>> reduce(1280, 1024)
    (5, 4)
    >>> reduce(1400, 1050)
    (4, 3)
    """
    for p in (2, 3, 5, 7):
        while not (z%p or n%p):
            z, n = z//p, n//p
    return (z, n)

class StandardRatios(dict): # requires Python 2.2+
    """
    a registry of ratios; e.g. 8:5 is better known as 16:10
    """
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return key

normalratio = StandardRatios()
normalratio[(8, 5)] = (16, 10)
normalratio[(9, 5)] = (18, 10)
normalratio[(5, 3)] = (15,  9)
normalratio[(7, 3)] = (21,  9)

def intsb4strings(seq):
    """
    integers before strings

    >>> intsb4strings(('a', '1', 'b', '2'))
    [1, 2, 'a', 'b']
    """
    res = []
    for i in seq:
        try:
            res.append(int(i))
        except ValueError:
            res.append(i)
    return sorted(res)

class ScaleRegistry(object):
    """
    Registry for (width, height) image dimensions
    """
    def __init__(self):
        self.ratios = {}
        self.keys_e = {} # explicit
        self.keys_i = {} # implicit
        self.dims = {}

    def register(self, width, height,
                 names=None,
                 wkey=None,
                 pxratio=1,
                 force=None):
        """
        register the given file format.

        width -- the width [Px]

        height -- the height [Px]

        names -- one or more format names. A single name can be given
                 as a string; more than one must be given as a tuple of strings

        wkey -- take the width value as a key; if None, and no names are given,
                defaults to True.

        pxratio -- width/height ratio of pixels (usually 1, for square pixels;
                   not yet used)

        force -- by default (force=False), duplicate keys yield errors;
                 specify True to make them overwrite existing keys
        """
        tup = width, height
        if wkey is None:
            wkey = not names
        else:
            if not wkey:
                if not names:
                    raise FormatRegistryError('with no name[s] given, '
                            'wkey must not be False')
            wkey = bool(wkey)
        if names:
            if isinstance(names, basestring):
                nlist = [names]
            elif isinstance(names, (list, tuple)):
                nlist = list(names)
            else:
                raise FormatRegistryError('invalid names argument %r'
                        '(%r)' % (names, type(names)))
        else:
            nlist = []
        for n in nlist:
            if not n:
                raise FormatRegistryError('Empty names are not allowed (%r)'
                                          % n)
            elif not isinstance(n, basestring):
                raise FormatRegistryError('Some kind of string expected'
                                          ' (%r)' % n)
        if wkey:
            nlist.append(str(width))
        elif not nlist:
            raise FormatRegistryError('list of names is empty')

        # (width, height) tuple -> names:
        if tup in self.dims:
            print '-' * 79
            print self.dims[tup]
            print tup
            print nlist
            pass    # TODO: perhaps yield some kind of info or warning
        else:
            # self.dims[tup] = set(nlist)
            # a list will preserve the order information:
            self.dims[tup] = nlist

        # name -> (width, height) tuple:
        for n in nlist:
            if n in self.keys_e:
                raise DuplicateKeyError('%r -> %s collides with %s'
                                   % (n, tup, self.keys_e[n],
                                      ))
            else:
                self.keys_e[n] = tup
            un = n.upper()
            if un != n:
                self.keys_i[un] = tup

        # ratio -> list of (width, height) tuples:
        dimtup = w, h = reduce(width, height)
        # dimtup = (w, h)
        if dimtup not in self.ratios:
            self.ratios[dimtup] = []
        self.ratios[dimtup].append(tup)

    def getRatio(self, key):
        if key in self.keys_e:
            return self.keys_e[key]
        ukey = key.upper()
        if ukey in self.keys_e:
            return self.keys_e[ukey]
        if ukey in self.keys_i:
            return self.keys_i[ukey]
        raise KeyError(key)

    def genKeyInfosRaw(self):
        for k, v in self.keys_e.items():
            try:
                yield int(k), v[0], v[1]
            except ValueError:
                yield k, v[0], v[1]

    def showKeysRaw(self):
        for z in sorted(list(self.genKeyInfosRaw())):
            print '%s\t->%5d x%5d' % z
        exit(HELP_RC)

    def genKeysWithLines(self, lines, inorder=1):
        """
        generate (cols, rows, key) tuples with the number of rows which is
        given as the lines argument.

        lines -- a number, e.g. 480
                 (which will generate a (640, 480, 'VGA') tuple, among others)
        inorder -- will sort the entries by the number of columns,
                   preserving the order in which the keys are yielded
                   by self.keys_e.items()
                   (which is currently not predictable yet ...),
                   and generate a (None, None, None) tuple finally
        """
        if inorder:
            liz = []
            idx = 0
            for (cols, rows, key) in self.genKeysWithLines(lines, inorder=0):
                liz.append((cols, idx, rows, key))
                idx += 1
            liz.sort()
            for (cols, idx, rows, key) in liz:
                yield (cols, rows, key)
            yield (None, None, None)
            return
        ok = 0
        for tup in self.keys_e.items():
            key, restup = tup
            cols, rows = restup
            if rows == lines:
                yield (cols, rows, key)
                ok = 1
        if not ok:
            raise NoResolutionsForLines(lines)

    def showKeysWithLines(self, lines):
        first = 1
        prevrows = None
        prevcols = None
        klist = []
        for (cols, rows, key) in self.genKeysWithLines(lines, inorder=1):
            if first:
                print _('Resolutions with %d lines:') % rows
                first = 0
            if cols != prevcols:
                if prevcols is not None:
                    assert klist
                    if rows is not None:
                        assert rows == lines, '%r != %r' % (rows, cols)
                    keys = '/'.join(klist)
                    print ' %(prevcols)5d x%(lines)5d (%(keys)s)' % locals()
                    del klist[:]
                else:
                    assert not klist
                prevcols = cols
            if key is not None:
                klist.append(key)
        exit(HELP_RC)

    def genKeyInfos(self):
        """
        generate key infos in a sortable fashion; yield tuples of equal
        length, containing sorting keys.  The last element is a string
        which can be used directly.

        The resulting sequence is *not* grouped by ratio.
        """
        for dim, keys in self.dims.items():
            num = None
            w, h = dim
            names = []
            for k in keys:
                if num is None:
                    try:
                        num = int(k)
                        assert num == w
                        continue
                    except ValueError:
                        pass
                names.append(k)
            if names:
                names.sort()
            w1, h1 = reduce(w, h)
            rat = float(w1) / h1
            if num:
                yield (num, rat, w, h,
                       ' %5d (x%5d, %d:%d%s)' % (
                           w, h,
                           w1, h1,
                           names and '; %s' % '/'.join(names)
                                 or '',
                        ))
            else:
                yield (None, rat, w, h,
                       '  %s (%d x %d, %d:%d)' % (
                           '/'.join(names),
                           w, h,
                           w1, h1,
                           ))

    def showKeys(self):
        seq = list(self.genKeyInfos())
        seq.sort()
        sel = [tup
               for tup in seq
               if tup[0] is not None]
        if sel:
            print _('Widths with default heights:')
            for tup in sel:
                print tup[-1]
        sel = [tup
               for tup in seq
               if tup[0] is None]
        if sel:
            print _('Specify by name only:')
            for tup in sel:
                print tup[-1]
        exit(HELP_RC)

    def showKeysGroupedByRatio(self):
        seq = list(self.genKeyInfos())
        ratios_dict = {}
        ratios_list = []
        grouped = []
        rest = []
        for (rat, w, h) in self.getRatios():
            if ((w < 10 and h < 10)
                or len(self.ratios[(w, h)]) > 1):
                grouped.append((w, h))
            else:
                rest.append((w, h))

        def diminfo(dim, rat=None):
            res = ['  ']
            res.append('%d x %d ' % dim)
            res.append('(%s'
                       % '/'.join(map(str,
                                      intsb4strings(self.dims[dim]))))
            if rat:
                res.append('; %d:%d' % rat)
            res.append(')')
            return ''.join(res)

        for rat in grouped:
            print '%d:%d:' % normalratio[rat]
            for dim in sorted(self.ratios[rat]):
                print diminfo(dim)
        if rest:
            print 'other:'
            for rat in rest:
                dim = self.ratios[rat][0]
                print diminfo(dim, rat)
        exit(HELP_RC)

    def getRatios(self):
        """
        return a sorted list of ratio tuples (quot, width, height)
        """
        return sorted([(float(w)/h, w, h)
                       for w, h in self.ratios])

    def getKeysByDim(self, dim):
        """
        generate the non-numeric keys which yield the given dimension tuple
        """
        try:
            for key in self.dims[dim]:
                try:
                    int(key)
                except ValueError:
                    yield key
        except KeyError:
            return

    def getKeysByRatio(self):
        """
        generate the keys, grouped by ratio
        """
        for rat, w, h in self.getRatios():
            print "%d:%d:" % (w, h)
            print '\t%s' % self.ratios[(w, h)]
        raise NotImplementedError

    def bestFormatName(self, width, height, given=None):
        strings, numbers = [], []
        normal = {}
        try:
            specs = self.dims[(width, height)]
            given = given.upper()
            for spec in specs:
                try:
                    numbers.append(int(spec))
                except ValueError:
                    if spec.upper() == given:
                        return spec
                    strings.append(spec)
            return strings[0]
        except KeyError:
            return None
        except IndexError:
            return None



def importIntValue(libname, valname):
    """
    imports a given integer value from a given module.
    Raises ImportError, if an unknown module is specified;
    catches the AttributeError, raised if the value is unknown.
    Before using this function to import from a module in a
    package, it apparently is necessary to import the package.
    """
    import PIL.Image
    try:
        modu = __import__(libname, globals(), locals(), [])
    except NameError: # doesn't work!!!
        fatal('You might need to import %s before calling importIntValue()' %
              libname.split('.')[0])
    try:
        test = eval('%s.%s' %(libname, valname))
    except AttributeError:
        raise OptionValueError('%s is not known in module %s'
                               % (valname, libname))
    if callable(test):
        fatal('%s.%s is callable!' % (libname, valname))
    elif type(test) == type(0):
        return test
    else:
        fatal('Won\'t import %s.%s %s: not an integer' % (libname, valname, type(test)))

def importIntFromPIL(name):
    return importIntValue('PIL.Image', name)

def cb_int_from_pil(option, opt_str, value, parser, known):
    """
    callback function to get an integer constant from PIL
    """
    val = value.strip().upper()
    if not val:
        raise OptionValueError('%r: invalid value for %s'
                               % (value, opt_str))
    try:
        setattr(parser.values, option.dest,
                importIntFromPIL(val))
    except ImportError, e:
        raise OptionValueError('%s: import error (%r)'
                               % (opt_str, str(e)))
    if not val in known:
        warning('Successfully imported value of unknown symbol %s'
                % val)

CSS_CLOCK = ('top', 'right', 'bottom', 'left')

def cb_clockwise(option, opt_str, value, parser,
                 sep, factory, mirror=None, mirror2=None):
    """
    optparse callback function for clockwise options
    """
    if not value:
        raise OptionValueError('%s: empty value not allowed'
                               % opt_str)
    try:
        liz = map(factory, value.split(sep))
    except ValueError, e:
        raise OptionValueError((str(e)))
    if len(liz) > 4:
        raise OptionValueError('%s takes at most 4 values %s'
                               % (opt_str, tuple(liz)))
    if mirror is None:
        mirror = lambda x: x
    if mirror2 is None:
        mirror2 = mirror
    dic = {}
    for k, i in zip(CSS_CLOCK, range(len(liz))):
        dic[k] = liz[i]
    if not 'right' in dic:
        dic['right'] = mirror2(dic['top'])
    if not 'bottom' in dic:
        dic['bottom'] = mirror(dic['top'])
    if not 'left' in dic:
        dic['left'] = mirror(dic['right'])
    setattr(parser.values, option.dest, dic)

def cb_clockwise_single(option, opt_str, value, parser,
                        factory, key):
    """
    optparse callback function for single-value-spin-offs of clockwise options
    """
    try:
        val = factory(value)
    except ValueError: #, e:
        raise OptionValueError
    # getattr returns the dict itself:
    dic = getattr(parser.values, option.dest)
    writeback = dic is None
    if writeback:
        dic = dict(zip(CSS_CLOCK,
                       (0, 0, 0, 0)))
    dic[key] = val
    if writeback:
        setattr(parser.values, option.dest, dic)

def add_clockwise_option(parser,
                         *args,
                         **kwargs):
    """
    create an option which takes 1 to 4 comma-separated values
    which populate a dict with top, right, bottom, left keys
    in CSS fashion; e.g., if only a single value is given, it is
    used for all sides.

    help -- the help text
    dest -- the dest value (should look like a valid Python identifier)
    factory -- a callable which takes one of the separated values
    mirror -- a callable to 'mirror' the top to bottom, right to left value
    mirror2 -- a callable to 'mirror' the top to right value; default: mirror
    detail_options -- create ...-top, ...-right etc. options?
                      Default: yes, if long option string given
    group2 -- a separate group for the detail_options
    sep -- the separator, default: the comma (',')
    *args -- the option strings (at least one required)
    """
    # Notloesung...
    defaults = {'dest':           None,
                'factory':        int,
                'mirror':         None,
                'mirror2':        None,
                'detail_options': None,
                'sep':            ',',
                'help':           None,
                'single_metavar': None,
                'metavar':        None,
                'group2':         None,
                }
    defaults.update(kwargs)
    firstlong = None
    dest = defaults['dest']
    for a in args:
        if a.startswith('--'):
            firstlong = a
            if not dest:
                dest = a[2:]
            break
        elif not a.startswith('-'):
            raise OptParseError('not a valid option string: %r'
                                % a)
    if not args:
        raise OptParseError('no long nor short option strings')
    help = defaults['help']
    if help.find('%(') != -1:
        help = help % defaults
    detail_options = defaults['detail_options']
    sep = defaults['sep']
    factory = defaults['factory']
    metavar = defaults['metavar'] or sep.join(['top[', 'right[',
                                               'bottom[', 'left]]]'])
    kwargs1 = dict(help=help,
                   dest=dest,
                   type='string',    # ?!
                   metavar=metavar,
                   action='callback',
                   callback=cb_clockwise,
                   callback_kwargs=dict(sep=sep,
                                        factory=factory,
                                        mirror=defaults['mirror'],
                                        mirror2=defaults['mirror2']))
    parser.add_option(*args, **kwargs1)
    if detail_options is None:
        detail_options = bool(firstlong)
    elif detail_options and not firstlong:
        raise OptParseError('detail_options requested, but no long '
                            'option given')
    if detail_options:
        try:
            group_ = defaults['group2']
        except KeyError:
            group_ = parser
        for key in CSS_CLOCK:
            group_.add_option('-'.join((firstlong, key)),
                              dest=dest,
                              type='string',    # ?!
                              action='callback',
                              metavar=defaults['single_metavar'],
                              callback=cb_clockwise_single,
                              callback_kwargs=dict(factory=factory,
                                                   key=key))

def add_resampling_option(parser,
                          help=None,
                          default='ANTIALIAS',
                          dest='filter',
                          *args):
    if help is None:
        help = _('the resampling filter to use; one of: '
                 'antialias (default; best known as of PIL 1.1.5), '
                 'nearest, bilinear, bicubic (not case sensitive)')
    if not args:
        args = ('--resampling-filter', '--rf')
    kwargs = dict(action='callback',
                  callback=cb_int_from_pil,
                  callback_kwargs=dict(known=set((
                      'NEAREST', 'NONE',    # the same; PIL default
                      'ANTIALIAS',          # best as of PIL 1.1.5
                      'BILINEAR', 'BICUBIC',
                      'LINEAR',   'CUBIC',
                      ))),
                  type='string',
                  default=default,
                  metavar=default,
                  dest=dest,
                  help=help)
    parser.add_option(*args, **kwargs)

scales = ScaleRegistry()

def cb_resolve_scale(option, opt_str, value, parser):
    try:
        val = scales.getRatio(value)
    except KeyError:
        val = value.split('x')
        if len(val) != 2:
            raise OptionValueError('x between two integer values, or known'
                    ' format spec. expected (%r)' % str(value))
        try:
            # TODO: dict(width, height, scalespec) anstelle des Tupels
            val = tuple(map(int, val))
        except ValueError:
            raise OptionValueError('%r: not a known/valid format spec' % value)
    val = dict(width=val[0],
               height=val[1],
               given=value)
    val['name'] = scales.bestFormatName(**val) \
                  or ('%(width)dx%(height)d' % val)
    setattr(parser.values, option.dest, val)

def add_scale_option(parser, help=None, dest='scale', *args):
    if help is None:
        help = _('width [px] of the resulting image, which is completed'
                 ' with the common companion height, '
                 'e.g. 1280 (x1024), 1024 (x768) or 640 (x480). '
                 'Some scales are known by name, e.g. VGA (640x480); '
                 'you may specify any other scale explicitly, '
                 'e.g. 1280x960.')
    elif not help:
        help = None
    parser.add_option('-s', '--scale',
                      action='callback',
                      type='string',    # callback yields tuple
                      metavar=_('WIDTH[xHEIGHT]|Name'),
                      dest=dest,
                      callback=cb_resolve_scale,
                      help=help)

def cb_resolve_cut(option, opt_str, value, parser):
    cut_opt={'vertical': 'middle',
             'horizontal': 'center',
             }
    for o in value.split(','):
        if o in ('top', 'middle', 'bottom'):
            cut_opt['vertical']=o
        elif o in ('left', 'center', 'right'):
            cut_opt['horizontal']=o
        else:
            fatal('%s: illegal option for --cut' % o, 5)
    setattr(parser.values, option.dest, cut_opt)

def add_cut_option(parser, help=None, dest='cut', *args):
    if help is None:
        help = _("specify up to one of 'middle' (default), 'top' and 'bottom', "
                 "and up to one of 'center' (default), 'left' and 'right', "
                 'divided by comma. If this option is omitted, the resulting '
                 'image will reach the maximum possible size only '
                 'if it features exactly the same side length ratio.')
    elif not help:
        help = None
    parser.add_option('--cut',
                      action='callback',
                      type='string',    # callback yields tuple
                      metavar=_('HORI,VERT'),
                      dest=dest,
                      callback=cb_resolve_cut,
                      help=help)

def cb_showKeys(option, opt_str, value, parser):
    scales.showKeys()

def cb_showKeysGroupedByRatio(option, opt_str, value, parser):
    scales.showKeysGroupedByRatio()

def cb_showKeysRaw(option, opt_str, value, parser):
    scales.showKeysRaw()

def cb_showKeysWithLines(option, opt_str, value, parser):
    scales.showKeysWithLines(value)

def add_scale_helpers(parser):
    parser.add_option('--help-scales',
                      action='callback',
                      callback=cb_showKeys,
                      help=_('show known scales'))
    parser.add_option('--help-scales-grouped',
                      action='callback',
                      callback=cb_showKeysGroupedByRatio,
                      help=_('show known scales, grouped by side ratio'))
    parser.add_option('--help-scales-raw',
                      action='callback',
                      callback=cb_showKeysRaw,
                      help=_('show known scales in "raw" format'))
    parser.add_option('--help-scales-by-lines',
                      action='callback',
                      type='int',
                      metavar='NNN',
                      callback=cb_showKeysWithLines,
                      help=_('show known scales with '
                      'given number of lines'))


for tup in (
        ( 640,  480, ('VGA',
                      '480p',	# <http://en.wikipedia.org/wiki/480p>
                      ), 1),
        ( 800,  600, ('SVGA',
                      ), 1),
        ( 800,  480, ('WVGA',
                      ), 0),
        (1024,  600, ('WSVGA',
                      ), 0),
        (1024,  768, ('XGA',
                      'EVGA',	# http://en.wikipedia.org/wiki/Extended_Video_Graphics_Array
                      ), 1),
        (1600,  768, ('UWXGA',
                      ), 0),
        (1152,  864, ('XGA+',	# http://en.wikipedia.org/wiki/Graphics_display_resolution#XGA.2B_.281152.C3.97864.29
                      ), 1),
        (1200,  800, ('DSVGA',	# Double SVGA (double number of pixels)
                      ), 0),
        (1200,  900, ('OLPC',	# One Laptop Per Child
                      ), 0),
        (1280,  720, ('720p',	# smaller HDTV format, non-interlaced
                      'HD',	# http://en.wikipedia.org/wiki/Graphic_display_resolutions#HD
                      'HD720',	# https://de.wikipedia.org/wiki/Grafikmodus
                      ), 0),
        (1280,  800, ('WXGA',	# a.k.a. "Vesa 1280"
                      ), 0),
        ( 320,  240, ('240p',
                      'qVGA',	# quarter; systematic meaning "quadruple"
                      ), 1),
        ( 240,  160, ('hqVGA',	# half quarter VGA; http://en.wikipedia.org/wiki/Graphics_display_resolution#HQVGA_.28240.C3.97160.29
                      ), 1),
        ( 160,  160, ('LoRES',	# Palm Low Resolution
                      ), 0),
        ( 320,  320, ('HiRES',	# Palm High Resolution
                      ), 0),
        (1280, 1024, ('SXGA',	# a.k.a. "Vesa 1280"
                      ), 1),
        (1400, 1050, ('SXGA+',
                      ), 1),
        (1280,  960, ('SXGA-',	# sometimes called SXGA, http://en.wikipedia.org/wiki/UXGA#SXGA_.281280.C3.971024.29
                      'UVGA',	# sometimes also QVGA
                      ), 0),
        (1440,  900, ('WXGA+',
                      ), 0),
        (1600,  900, ('HD+',
                      ), 0),
        (1600, 1200, ('UXGA',	# http://en.wikipedia.org/wiki/UXGA#UXGA_.281600.C3.971200.29
                      'UGA',	# ... Dell name
                      ), 1),
        (1600, 1024, ('WSXGA',
                      ), 0),
        (1680, 1050, ('WSXGA+',
                      ), 1),
        (1920, 1200, ('WUXGA',	# maximum for Single-Link DVI
                      ), 1),
        (1920, 1080, ('FullHD',
                      'FHD',	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
                      '1080i',	# well, "interlaced" doesn't apply to image formats ...
                      '1080p',	# ... neither does 'p'
                      'HD1080',	# https://de.wikipedia.org/wiki/Grafikmodus
                      ), 0),
        (1920, 1440, ('TXGA',	# "Tesselar XGA", also: 1920x1400, 48:35;
                                # http://de.wikipedia.org/wiki/Grafikmodus#Liste_der_Bildaufl.C3.B6sungen_in_der_computernahen_Technik
                      ), 0),
        (2560, 1080, ('UWFullHD',	# "official" name? Ratio: 64/27
                      'UWFHD',	# http://www.heise.de/ct/foren/S-Name-des-Formats/forum-260255/msg-23834092/read/
                      ), 0),
        (960,   540, ('qHD',	# quarterHD; http://en.wikipedia.org/wiki/Graphics_display_resolution#qHD
                      ), 1),	# resolution of fairphone, http://buy-a-phone-start-a-movement.fairphone.com/en/specs/
        (2048, 1536, ('QXGA',
                      'SUXGA',
                      ), 1),
        (2048, 1152, ('QWXGA',
                      ), 0),
        (2560, 2048, ('QSXGA',
                      ), 1),
        (2560, 1536, ('WQXGA',	# c't 1/2011, S. 96: 2560x1600
                      ), 0),
        (3200, 1800, ('WQXGA+',	# http://en.wikipedia.org/wiki/Graphics_display_resolution#WQXGA.2B_.283200x1800.29
                      ), 0),
        (2560, 1440, ('WQHD',	# c't 1/2011, S. 96: 'Pixel-Autobahn'
                      ), 0),
        (3200, 2048, ('WQSXGA',
                      ), 0),
        # (854,  480,  '480p', 0),	# non-standard according to wp
        # <http://en.wikipedia.org/wiki/Low-definition_television>:
        (640,  360,  ('360p',
                      ), 0),
        # (400,  226,  '240p', 0),	# ?!
        (480,  360,  ('HQ6',
                      ), 0),
        (176,  144,  ('HQ13',
                      ), 0),
        (3200, 2400, ('QUXGA',
                      ), 1),
        (3840, 2160, ('4K',	# UHD; http://en.wikipedia.org/wiki/Ultra-high-definition_television
                      '2160p',
                      # also QHD, but conflicting with qHD
                      'UHDTV1',
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        (3840, 2400, ('QWUXGA',
                      'WQUXGA',
                      ), 1),
        (4096, 3072, ('HXGA',
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        (5120, 3200, ('WHXGA',
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        (5120, 4096, ('HSXGA',
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        (6400, 4096, ('WHSXGA',
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        (7680, 4320, ('8K',	# UHD; http://en.wikipedia.org/wiki/Ultra-high-definition_television
                      '4320p',
                      'UHDTV2',
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        (7680, 4800, ('WHUXGA',
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        (6400, 4800, ('HUXGA',	# http://en.wikipedia.org/wiki/WSXGA%2B#HUXGA_.286400.C3.974800.29
                      ), 0),	# http://en.wikipedia.org/wiki/Graphic_display_resolutions
        # ( 320,  240),
        ( 180,  135),
        ( 160,  120, ('qqVGA',
                      ), 1),
        (  88,   31),		# small banner buttons, e.g. for W3C validation links
        ):
    scales.register(*tup)   # width, height[, names[, wkey]]
del tup

def clip_arg(val):
    """
    take a string, and
    return an integer number, a percent value (as a string), or 'auto'
    (a possible 'factory' function, e.g. for add_clockwise_option)

    Will raise ValueErrors if something else is given.

    >>> clip_arg('50')
    50
    >>> clip_arg('50%')
    '50%'
    >>> clip_arg('0%')
    0
    """
    val = val.strip().lower()
    if val == 'auto':
        return val
    if val.endswith('%'):
        i = int(val[:-1])
        if not i:
            return i
        return '%d%%' % i
    return int(val or 0)

def mirror_auto(val):
    """
    mirror 0 to 0, and any other value to 'auto'

    >>> mirror_auto(0)
    0
    >>> mirror_auto(1)
    'auto'
    """
    if val == 0:
        return 0
    return 'auto'

def mirror_zero(val):
    """
    return 0 for any given value

    >>> mirror_zero(0)
    0
    >>> mirror_zero(1)
    0
    """
    return 0

def clockwise_info(val):
    """
    take None or a dictionary with top, right, bottom, left keys,
    and return a string
    """
    if val is None:
        return _('not specified')
    return ('{%s}' % ', '.join(['%s: %%(%s)r' % (k, k)
                                for k in CSS_CLOCK])
            ) % val


if __name__ == '__main__':
    from thebops.modinfo import main as modinfo
    modinfo(version=__version__)

