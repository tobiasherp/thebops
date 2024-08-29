# vim: ts=8 sts=4 sw=4 si et tw=79
import unittest
from thebops.rexxbi import *
# not yet public:
from thebops.rexxbi import d2x

DEBUG = 1

class TestConverters(unittest.TestCase):
    """
    Tests for the d2x, x2d, b2x, x2b functions
    """

    def test_d2x_positivesimple(self):
        """
        d2x yields expected results for positive numbers w/o length spec
        """
        for (d, res) in (
                (1,    '1'),
                (127, '7F'),
                (129, '81'),
                ):
            self.assertEqual(d2x(d), res)

    def test_d2x_positivefilled(self):
        """
        d2x yields exp. results for positive numbers padded to greater length
        """
        for (tup, res) in (
                ((1,   2),   '01'),
                ((127, 3),  '07F'),
                ((129, 4), '0081'),
                ):
            self.assertEqual(d2x(*tup), res)

    def test_d2x_positivecropped(self):
        """
        d2x yields exp. results for positive numbers cropped to smaller length
        """
        for (tup, res) in (
                ((129,  1),  '1'),
                ((257,  2), '01'),
                ((12,   0),   ''),
                ((1234, 2), 'D2'),
                ((127,  1),  'F'),
                ):
            self.assertEqual(d2x(*tup), res)

    def test_d2x_negativesimple(self):
        """
        d2x raises an error when given a negative number w/o a length
        """
        self.assertRaises(RexxArgumentValueError,
                          d2x,
                          (-1,))

    def test_d2x_negativefilled(self):
        """
        d2x yields exp. results for negative numbers padded to greater length
        """
        for (tup, res) in (
                ((-1,   2),   'FF'),
                ((-127, 2),   '81'),
                ((-127, 3),  'F81'),
                ((-127, 4), 'FF81'),
                ):
            self.assertEqual(d2x(*tup), res)

    def test_d2x_negativecropped(self):
        """
        d2x yields exp. results for negative numbers cropped to smaller length
        """
        for (tup, res) in (
                ((-127, 1),   '1'),
                ((-12,  0),    ''),
                ):
            self.assertEqual(d2x(*tup), res)


if __name__ == '__main__':
    unittest.main()
