#  This file is part of easygdf and is released under the BSD 3-clause license

import unittest

import easygdf.tests as tests

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(tests.all_tests)
