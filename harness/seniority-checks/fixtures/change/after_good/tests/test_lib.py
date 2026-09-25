import unittest

from lib import total


class TotalTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total([1, 2, 3]), 6)

    def test_negative_discount_is_ignored(self):
        self.assertEqual(total([1, 2], discount=-5), 3)
