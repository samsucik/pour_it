import unittest

class ExampleTestCase(unittest.TestCase):
    def setUp(self):
        self.greeting = 'Hello World'

    def tearDown(self):
        self.greeting.dispose()
        self.greeting = None

    def test_lowercase(self):
        self.assertEqual(self.greeting.lower(), 'hello world', 'Incorrect lowercased greeting')