#! /usr/bin/env python3
"""Example of unit testing with numbers using the unittest framework."""

import unittest


class TestNumbers(unittest.TestCase):
    """Example of unit testing with numbers."""

    def test_relations(self):
        """Testing relations between numbers."""
        # Test if 1 == 1
        self.assertEqual(1, 1)

        # Test if 1 != 2
        self.assertNotEqual(1, 2)

        # Test if 1 > 0
        self.assertGreater(1, 0)

        # Test if 1 >= 1
        self.assertGreaterEqual(1, 1)

        # Test if 1 < 2
        self.assertLess(1, 2)

        # Test if 1 <= 1
        self.assertLessEqual(1, 1)

        # Test if 1 ~= 1.0001 using rounding to decimal places
        self.assertAlmostEqual(1, 1.0001, places=3)

        # Test if 1 ~= 1.0001 using delta threshold
        self.assertAlmostEqual(1, 1.0001, delta=0.0001)
