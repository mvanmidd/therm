import unittest

import therm


class ThermTestCase(unittest.TestCase):

    def setUp(self):
        self.app = therm.app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        self.assertIn('Welcome to therm', rv.data.decode())


if __name__ == '__main__':
    unittest.main()
