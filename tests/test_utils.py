import unittest
import easygdf


class TestEasyGDFUtils(unittest.TestCase):
    def test_get_example_screen_tout_filename(self):
        # Just run the function and make sure we don't error out
        easygdf.get_example_screen_tout_filename()

    def test_get_example_initial_distribution(self):
        easygdf.get_example_initial_distribution()
