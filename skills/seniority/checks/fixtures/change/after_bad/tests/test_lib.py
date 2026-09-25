import unittest

from lib import total


class TotalTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total([1, 2, 3]), 7)
