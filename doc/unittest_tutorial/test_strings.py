#! /usr/bin/env python3
"""Example of unit testing with strings using the unittest framework."""

import unittest


class TestStrings(unittest.TestCase):
    """Example of unit testing with strings."""

    def test_isupper(self):
        """Testing if a string is upper case."""
        # Assert that an object is a string
        self.assertIsInstance("FOO", str)

        # One way to test if string is upper case, using assertTrue
        self.assertTrue("FOO".isupper())

        # Another way using assert False
        self.assertFalse(not "FOO".isupper())

        # Another way using equality test
        self.assertEqual("FOO", "FOO".upper())

    def test_error(self):
        """Testing for error raised."""
        with self.assertRaises(TypeError):
            return "FOO" / 5


if __name__ == '__main__':
    unittest.main()
