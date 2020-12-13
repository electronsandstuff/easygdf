#  This file is part of easygdf and is released under the BSD 3-clause license

from .test_easygdf import *
from .test_initial_distribution import *
from .test_screens_touts import *
from .test_utils import *

# Create a complete test suite for ourselves
all_tests = unittest.TestSuite()
all_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEasyGDFLoad))
all_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEasyGDFSave))
all_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEasyGDFLoadSave))
all_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEasyGDFInitialDistribution))
all_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEasyGDFScreensTouts))
all_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEasyGDFUtils))
all_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestEasyGDFHelpers))
