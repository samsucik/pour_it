import unittest
from unittest import TestLoader, TextTestRunner

class ExampleTestCase(unittest.TestCase):
    def setUp(self):
        self.greeting = 'Hello World'

    def tearDown(self):
        # self.greeting.dispose()
        self.greeting = None

    # This will pass
    def test_lowercase(self):
        self.assertEqual(self.greeting.lower(), 'hello world', 'Incorrect lowercased greeting')

    # This will pass
    def test_uppercase(self):
        self.assertEqual(self.greeting.upper(), 'HELLO WORLD', 'Incorrect uppercased greeting')

    # This will fail
    def test_unchanged(self):
        self.assertEqual(self.greeting, 'HELLO WORLD', 'Incorrect unchanged greeting')

if __name__ == "__main__":
    test_suite = TestLoader().loadTestsFromTestCase(ExampleTestCase)
    test_runner = TextTestRunner(verbosity=2).run(test_suite)