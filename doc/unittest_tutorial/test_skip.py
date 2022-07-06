#! /usr/bin/env python3
"""Example of test skipping in the unittest framework."""

import unittest


class TestSkip(unittest.TestCase):
    """Example of unit test skipping."""

    @unittest.skip("Demonstrating skipping.")
    def test_skip(self):
        """This test method will be skipped."""
        self.fail("Shouldn't happen.")

    @unittest.skipIf(True, "Skipped because True.")
    def test_skipif(self):
        """This test method will also be skipped."""
        self.fail("Also shouldn't happen.")

    @unittest.skipUnless(True, "Not skipped.")
    def test_skipunless(self):
        """This test method should not be skipped."""
