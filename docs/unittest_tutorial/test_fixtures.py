#! /usr/bin/env python3
"""Example of unit testing fixtures using the unittest framework."""

import unittest


class TestFixtures(unittest.TestCase):
    """Example of using fixtures in unit testing."""

    # BEGIN test fixtures
    @classmethod
    def setUpClass(cls):
        """Set-up operation performed once at initilization for the entire test case."""
        cls.example_lst = list()

    @classmethod
    def tearDownClass(cls):
        """Tear-down operation performed once after all test methods finish executing."""
        # Useful for e.g. closing a connection
        # Nothing useful to do in this case, though

    def setUp(self):
        """Perform a set-up operation before each test method executes."""
        # Append 1, 2, 3 to the example list
        self.example_lst.extend([1, 2, 3])

    def tearDown(self):
        """Perform a tear-down operation before each test method executes."""
        # Clear the example list of all elements
        self.example_lst.clear()
    # END test fixtures

    def test_list1(self):
        """Test that the example list's contents are [1, 2, 3]."""
        # One way to test contents of list
        self.assertEqual(self.example_lst, [1, 2, 3])
        # Another way specific to lists, will raise exception if given non-list argument
        self.assertListEqual(self.example_lst, [1, 2, 3])

    def test_list2(self):
        """Test that the example list's contents are still [1, 2, 3]."""
        self.assertListEqual(self.example_lst, [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
