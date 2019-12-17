# Unittest Tutorial
The standard Python Unit Testing library `unittest` provides a good unit testing framework for Python projects. It supports the following basic features:

## Test Cases
Create a test case:
```py
import unittest

# Test Case is a class, inherits from unittest.TestCase
class TestExample(unittest.TestCase):
    pass
```
There can be multiple test cases in a module to better organize unit tests.
```py
import unittest

# First Test Case in module
class TestExample1(unittest.TestCase):
    pass

# Second Test Case in module
class TestExample2(unittest.TestCase):
    pass
```

## Test Methods
Test cases are comprised of test methods (names must start with 'test'). These implement the tests.
```py
import unittest

# Test Case
class TestExample(unittest.TestCase):
    # First Test Method in Test Case
    # Name must start with 'test'
    def test_method1(self):
        # Run tests
        
    # Second Test Method in Test Case
    # Name must start with 'test'
    def test_method2(self):
        # Run tests
```

## Unit tests
Test methods can run unit tests using the following methods of `TestCase` (non-exhaustive):
* `assertAlmostEqual`: test if float `a` almost equals `b` within a specified threshold
* `assertDictEqual`: test if dict `a` equals dict `b`
* `assertEqual`: test if `a == b` (not type-specific)
* `assertFalse`: test if an expression evaluates to `False`
* `assertGreater`: test if `a > b`
* `assertGreaterEqual`: test if `a >= b`
* `assertIn`: test if `a in b`
* `assertIs`: test if `a is b`
* `assertIsInstance`: test if `a` is an instance of `b`
* `assertIsNone`: test if an object is `None`
* `assertIsNot`: test if `a is not b`
* `assertIsNotNone`: test if an object is not `None`
* `assertLess`: test if `a < b`
* `assertLessEqual`: test if `a <= b`
* `assertListEqual`: test if list `a` equals list `b` (fails if either is not a list)
* `assertNotEqual`: test if `a != b`
* `assertNotIn`: test if `a not in b`
* `assertNotIsInstance` test if `a` is not an instance of `b`
* `assertRaises`: test if a callable raises a given exception given `*args` and `**kwargs`
* `assertSetEqual`: test if set `a` is equal to set `b`
* `assertTrue`: test if an expression evaluates to `True`
* `assertTupleEqual`: test if a tuple `a` is equal to tuple `b`
* `fail`: causes the test method to fail

If any of these tests fail, the entire Test Method fails and is skipped. An error message will be produced explaining how a test method failed. The number of passing tests out of the total number of tests is listed at the end of the unit test run.
```py
import unittest

class TestExample(unittest.TestCase):
    def test_method(self):
        # The following tests succeed
        self.assertEqual(1, 1)
        self.assertAlmostEqual(1, 1.0001, places=3)
        self.assertIsNone(None)
        self.assertListEqual([1, 2, 3], [1, 2, 3])
        self.assertSetEqual({1, 2, 3}, {3, 2, 1})
        self.assertRaises(ValueError, foo)
        # Alternate usage of assertRaises using context manager
        with self.assertRaises(ValueError):
           foo()
        
        # The following tests fail
        self.assertAlmostEqual(1.0, 1.0001, places=4)
        self.assertGreater(1, 2)
        self.assertFalse(True)
        self.fail()
        

def foo():
    raise ValueError
```

## Testing Fixtures
Procedures can be set up to run at the beginning or end of a Test Case or at the beginning or end of each test method in a Test Case. These are methods with the special names `setUpClass`, `tearDownClass`, `setUp`, and `tearDown` respectively.
```py
import unittest

class TestExample(unittest.TestCase):
    @classmethod
    setUpClass(cls):
        # Run once at initialization of test case

    @classmethod
    tearDownClass(cls):
        # Run once at termination of test case
        
    setUp(self):
        # Run at the beginning of each test method
        
    tearDown(self):
        # Run at the end of each test method
```

## Skipping Tests
A test method can be conditionally or unconditionally skipped using decorators.
```py
import unittest

class TestExample(unittest.TestCase):
    @unittest.skip("Skip message")
    def test_skip(self):
        # This test will be skipped

    @unittest.skipIf(cond, "Skip message")
    def test_skipif(self):
        # This test will be skipped if cond evaluates to true
        
    @unittest.skipUnless(cond, "Skip message")
    def test_skipunless(self):
        # This test will be skipped if cond evaluates to false
```

## Running Tests
Unit tests can be run for an entire file/module(s), a specific Test Case (class) in the module(s), or a specific Test Method of a Test Class in the module(s).
* Run all Test Methods for each Test Case in a module(s):
   - `python -m unittest path.to.module`
* Equivalent to the previous command, using the file path:
   - `python -m unittest path/to/module.py`
* Run each Test Method in the `TestExample` Test Case in the module
   - `python -m unittest path.to.module.TestExample`
* Run the `test_method1` Test Method in the `TestExample` Test Case in the module
   - `python -m unittest path.to.module.TestExample.test_method1`
   
If a unit test module calls `unittest.main`, then `python -m path.to.module` suffices to run each test in a module, but will not produce as much useful output.
```py
import unittest

class TestExample(unittest.TestCase):
    def test_method(self):
        # Run unit tests

if __name__ == "__main__":
    unittest.main()
```
