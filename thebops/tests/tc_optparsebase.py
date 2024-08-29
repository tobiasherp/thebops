# vim: ts=8 sts=4 sw=4 si et
import unittest
# from thebops.optparse import *
from optparse import *
from thebops.opo import cb_decrease

DEBUG = 1
REMOVE = tuple('ReMoVe')

def parser_factory(*args, **kwargs):
    parser_kwargs = {'add_help_option': 0,
                     'version': '%prog 1.5.3',
                     'description': 'Tests for options as of optparse v1.5.3',
                     'epilog': 'Ceterum censeo Carthaginem esse delendam.'
                     }
    if kwargs:
        parser_kwargs.update(kwargs)
    p = OptionParser(**parser_kwargs)
    for ospec in args:
        tup, dic = ospec
        p.add_option(*tup, **dic)
    return p

OSPECS = (
        # increasing/decreasing ... 
        (('-v',),
         {'action': 'count',
          'dest': 'verbose',
          'default': 2,
          }),
        (('-q',),
         {'action': 'callback',
          'callback': cb_decrease,
          'dest': 'verbose',
          }),
        (('-z',),
         {'action': 'count',
          'dest': 'zerobased',
          }),
        # directly specified numbers 
        (('--integer', '-i'),
         {'type': 'int',
          'metavar': 'NN',
          }),
        (('--long', '-l'),
         {'type': 'long',
          'metavar': 'NNNNNNNN',
          }),
        (('--float', '-f'),
         {'type': 'float',
          'metavar': 'NN.MM',
          }),
        (('--complex', '-c'),
         {'type': 'complex',
          'metavar': '[NN+]MMj',
          }),
        # constants 
        (('--eins',),
         {'action': 'store_const',
          'const': 1,
          'dest': 'integer',
          }),
        (('--yes',),
         {'action': 'store_true',
          'dest': 'theanswer',
          }),
        (('--no',),
         {'action': 'store_false',
          'dest': 'theanswer',
          }),
        (('-1',),
         {'action': 'append_const',
          'const': 1,
          'dest': 'numbers',
          }),
        (('-2',),
         {'action': 'append_const',
          'const': 2,
          'dest': 'numbers',
          }),
        (('-3',),
         {'action': 'append_const',
          'const': 3.25,
          'dest': 'numbers',
          }),
        # string variants 
        (('--store-string', '-s'),
         {'action': 'store',
          'metavar': 'STR',
          'dest': 'onestring',
          }),
        (('--append-strings', '-S'),
         {'action': 'append',
          'metavar': 'STR[,STR2]',
          'dest': 'strings',
          }),
        # nargs: if != 1, yields tuple
        (('--one-integer',),
         {'type': 'int',
          'nargs': 1,
          'dest': 'nargs1int',
          'metavar': 'II',
          }),
        (('--two-integers',),
         {'type': 'int',
          'nargs': 2,
          'dest': 'nargs2int',
          'metavar': 'II JJ',
          }),
        (('--three-integers',),
         {'type': 'int',
          'nargs': 3,
          'dest': 'nargs3int',
          'metavar': 'II JJ KK',
          }),
    )


def result(**kwargs):
    DEFVALUES = {
        'verbose': 2,
        'zerobased': None,
        'integer': None,
        'long': None,
        'float': None,
        'complex': None,
        'onestring': None,
        'strings': None,
        'nargs1int': None,
        'nargs2int': None,
        'nargs3int': None,
        'theanswer': None,
        'numbers': None,
        }
    if kwargs:
        DEFVALUES.update(kwargs)
    return DEFVALUES


class TestParse(unittest.TestCase):
    """
    tests for successful options evaluation
    """

    def test_000defaults(self):
        """\
        call without options yields default values
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args([])
        expected = result()
        self.assertEqual(o, expected)

    def test_001defaults(self):
        """\
        options after '--' are ignored
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-- -vvv'.split())
        expected = result()
        self.assertEqual(o, expected)

    def test_100count(self):
        """\
        count action increases default value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-z'.split())
        expected = result(zerobased=1)
        self.assertEqual(o, expected)

    def test_101count(self):
        """\
        count action increases non-None default value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-vvv'.split())
        expected = result(verbose=5)
        self.assertEqual(o, expected)

    def test_200decrease_callback(self):
        """\
        decrease callback decreases default value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-q'.split())
        expected = result(verbose=1)
        self.assertEqual(o, expected)

    def test_200decrease_callback_floor(self):
        """\
        decrease callback won't decrease below floor value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-qqqqqq'.split())
        expected = result(verbose=0)
        self.assertEqual(o, expected)

    def test_300string_short1(self):
        """\
        store a string (short, explicit)
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-sTheString'.split())
        expected = result(onestring='TheString')
        self.assertEqual(o, expected)

    def test_300string_short2(self):
        """\
        store a string (short, implicit)
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-s TheString'.split())
        expected = result(onestring='TheString')
        self.assertEqual(o, expected)

    def test_300string_long1(self):
        """\
        store a string (long, explicit)
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--store-string=TheString'.split())
        expected = result(onestring='TheString')
        self.assertEqual(o, expected)

    def test_300string_long2(self):
        """\
        store a string (long, implicit)
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--store-string TheString'.split())
        expected = result(onestring='TheString')
        self.assertEqual(o, expected)

    def test_400repeated_call(self):
        """\
        parse_args can be called repeatedly, forgetting previous arguments
        """
        p = parser_factory(*OSPECS)
        o1, a = p.parse_args('-sfirst-call'.split())
        expected = result(onestring='first-call')
        self.assertEqual(o1, expected)
        o2, a = p.parse_args('-S2nd-call'.split())
        self.assertEqual(o2.onestring, None)

    def test_500nargs1(self):
        """\
        store one integer
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--one-integer 1 2 3'.split())
        expected = result(nargs1int=1)
        self.assertEqual(o, expected)

    def test_500nargs2(self):
        """\
        store two integers
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--two-integers 1 2 3'.split())
        expected = result(nargs2int=(1, 2))
        self.assertEqual(o, expected)

    def test_500nargs2a(self):
        """\
        store two integers, the 1st given explicitly
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--two-integers=1 2 3'.split())
        expected = result(nargs2int=(1, 2))
        self.assertEqual(o, expected)

    def test_500nargs3(self):
        """\
        store three integers
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--three-integers 1 2 3'.split())
        expected = result(nargs3int=(1, 2, 3))
        self.assertEqual(o, expected)

    def test_600append_separate(self):
        """\
        append values given separately
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-S eins -S zwei'.split())
        expected = result(strings=['eins', 'zwei'])
        self.assertEqual(o, expected)

    def test_601append_ignores_comma(self):
        """\
        append ignores commas in values
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-Seins,zwei'.split())
        expected = result(strings=['eins,zwei'])
        self.assertEqual(o, expected)

    def test_701integer(self):
        """\
        store integer value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--integer 47'.split())
        expected = result(integer=47)
        self.assertEqual(o, expected)

    def test_702integer_0x(self):
        """\
        accept integer value with 0x prefix
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--integer 0x20'.split())
        expected = result(integer=32)
        self.assertEqual(o, expected)

    def test_703integer_o(self):
        """\
        integer: recognise leading zero as octal prefix
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--integer 033'.split())
        expected = result(integer=27)
        self.assertEqual(o, expected)

    def test_704integer_0b(self):
        """\
        integer: recognise leading 0b as binary prefix
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--integer 0b1111'.split())
        expected = result(integer=15)
        self.assertEqual(o, expected)

    def test_711long(self):
        """\
        store long value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--long 47'.split())
        expected = result(long=47)
        self.assertEqual(o, expected)

    def test_712long_0x(self):
        """\
        accept long value with 0x prefix
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--long 0x20'.split())
        expected = result(long=32)
        self.assertEqual(o, expected)

    def test_713long_o(self):
        """\
        long: recognise leading zero as octal prefix
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--long 033'.split())
        expected = result(long=27)
        self.assertEqual(o, expected)

    def test_714long_0b(self):
        """\
        long: recognise leading 0b as binary prefix
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--long 0b1111'.split())
        expected = result(long=15)
        self.assertEqual(o, expected)

    def test_721float(self):
        """\
        store float value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--float 12.34'.split())
        expected = result(float=12.34)
        self.assertEqual(o, expected)

    def test_731complex(self):
        """\
        store complex value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--complex 1+2j'.split())
        expected = result(complex=1+2j)
        self.assertEqual(o, expected)

    def test_801const_integer(self):
        """\
        store constant integer value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--eins'.split())
        expected = result(integer=1)
        self.assertEqual(o, expected)

    def test_802const_true(self):
        """\
        store true value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--yes'.split())
        expected = result(theanswer=True)
        self.assertEqual(o, expected)

    def test_803const_false(self):
        """\
        store false value
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('--no'.split())
        expected = result(theanswer=False)
        self.assertEqual(o, expected)

    def test_821append_const1(self):
        """\
        append const integer value 1
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-1'.split())
        expected = result(numbers=[1,])
        self.assertEqual(o, expected)

    def test_822append_const2(self):
        """\
        append const integer values 1 and 2
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-12'.split())
        expected = result(numbers=[1, 2])
        self.assertEqual(o, expected)

    def test_823append_const3(self):
        """\
        append mixed-type const values
        """
        p = parser_factory(*OSPECS)
        o, a = p.parse_args('-12 -3'.split())
        expected = result(numbers=[1, 2, 3.25])
        self.assertEqual(o, expected)

class TestErrors(unittest.TestCase):
    """
    tests for errors during options evaluation
    """

    def test_fail_nargs1(self):
        """\
        error for missing required value
        """
        p = parser_factory(*OSPECS)
        def f():
            p.parse_args_testable(['-s'])
        self.assertRaises(OptionValueError, f)

    def test_fail_nargs1_2(self):
        """\
        error for missing required value, if another option follows
        """
        p = parser_factory(*OSPECS)
        def f():
            p.parse_args_testable(['-s', '--yes'])
        self.assertRaises(OptionValueError, f)


if __name__ == '__main__':
    import sys
    print '\n'.join(dir(sys.modules['thebops.optparse']))
    print sys.modules['thebops.optparse'].__file__
    unittest.main()

