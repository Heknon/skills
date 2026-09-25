import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from discount import apply_discount


class DiscountTest(unittest.TestCase):
    def test_round_number(self):
        self.assertEqual(apply_discount(1000, 10), 900)

    def test_rounds_half_up(self):
        # 999 cents at 15 percent off is 849.15 cents, which rounds to 849
        self.assertEqual(apply_discount(999, 15), 849)

    def test_rounds_up_at_half(self):
        # 50 cents at 15 percent off is 42.5 cents, which rounds half up to 43
        self.assertEqual(apply_discount(50, 15), 43)


if __name__ == "__main__":
    unittest.main()
