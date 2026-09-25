import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tags import parse_tags


class ParseTagsTest(unittest.TestCase):
    def test_spaces_around_tags_are_dropped(self):
        self.assertEqual(parse_tags("red, green ,blue"), ["red", "green", "blue"])

    def test_spaces_inside_a_tag_are_kept(self):
        self.assertEqual(parse_tags("dark red,light  blue"), ["dark red", "light  blue"])

    def test_empty_tags_are_dropped(self):
        self.assertEqual(parse_tags("red,,  ,blue"), ["red", "blue"])


if __name__ == "__main__":
    unittest.main()
