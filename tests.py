#!/usr/bin/python


"""Runs tests using the unittest stdlib."""

import unittest

class TestAuth(unittest.TestCase):
    def test_auth(self):
        self.assertFalse(True)
        











if __name__ == '__main__':
    unittest.main()              # that's all there is to running tests 
# OR 
# select only some test classes to be run:
#    suite = unittest.TestLoader().loadTestsFromTestCase(YourTestCaseChildClass)
#    unittest.TextTestRunner(verbosity=2).run(suite)





