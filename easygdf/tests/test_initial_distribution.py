#  This file is part of easygdf and is released under the BSD 3-clause license

import datetime
import os
import tempfile
import unittest

import numpy as np
import pkg_resources

import easygdf


class TestEasyGDFInitialDistribution(unittest.TestCase):
    def setUp(self):
        """
        This section looks really ugly :(

        It's a dump of testing data to validate against real GDF initial distribution files w/ different formats.
        :return:
        """
        self.ref = {
            'x': np.array([3.389e-05, 2.314e-05, 3.261e-05, 3.295e-05, 3.559e-05]),
            'y': np.array([3.096e-08, 3.241e-08, 3.506e-08, 3.717e-08, 3.990e-08]),
            'z': np.array([0., 0., 0., 0., 0.]),
            'GBx': np.array([0., 0., 0., 0., 0.]),
            'GBy': np.array([0., 0., 0., 0., 0.]),
            'GBz': np.array([0., 0., 0., 0., 0.]),
            't': np.array([1.865e-11, -1.712e-11, -1.367e-11, -9.963e-12, -1.238e-11]),
            'q': np.array([-1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19]),
            'nmacro': np.array([8.752, 8.752, 8.752, 8.752, 8.752]),
            'creation_time': datetime.datetime(2019, 8, 7, 20, 47, 1, tzinfo=datetime.timezone.utc),
            'creator': 'ASCI2GDF',
            'destination': '',
            'gdf_version': (1, 1),
            'creator_version': (1, 0),
            'destination_version': (0, 0),
            'dummy': (0, 0)
        }

        self.ref2 = {
            'x': np.array([3.389e-05, 2.314e-05, 3.261e-05, 3.295e-05, 3.559e-05]),
            'y': np.array([3.096e-08, 3.241e-08, 3.506e-08, 3.717e-08, 3.990e-08]),
            'z': np.array([0., 0., 0., 0., 0.]),
            'Bx': np.array([0., 0., 0., 0., 0.]),
            'By': np.array([0., 0., 0., 0., 0.]),
            'Bz': np.array([0., 0., 0., 0., 0.]),
            't': np.array([1.865e-11, -1.712e-11, -1.367e-11, -9.963e-12, -1.238e-11]),
            'q': np.array([-1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19]),
            'nmacro': np.array([8.752, 8.752, 8.752, 8.752, 8.752]),
            "m": np.array([8.752, 8.752, 8.752, 8.752, 8.752]),
            "G": np.array([1., 1., 1., 1., 1.]),
            "ID": np.array([1., 2., 3., 4., 5.]),
            'rmacro': np.array([8.752, 8.752, 8.752, 8.752, 8.752]),
            'creation_time': datetime.datetime(2019, 8, 7, 20, 47, 1, tzinfo=datetime.timezone.utc),
            'creator': 'ASCI2GDF',
            'destination': '',
            'gdf_version': (1, 1),
            'creator_version': (1, 0),
            'destination_version': (0, 0),
            'dummy': (0, 0)
        }

    def test_load(self):
        # Try to load the file
        with pkg_resources.resource_stream("easygdf.tests", "data/initial_distribution.gdf") as f:
            all_data = easygdf.load_initial_distribution(f)

        # Confirm that the keys are the same
        self.assertEqual(self.ref.keys(), all_data.keys())
        for k in self.ref:
            if isinstance(self.ref[k], np.ndarray):
                np.testing.assert_almost_equal(self.ref[k], all_data[k])
            else:
                self.assertEqual(self.ref[k], all_data[k])

    def test_save(self):
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_initial_distribution(f, **self.ref)

        # Read it back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_initial_distribution(f)

        # Confirm that the keys are the same
        self.assertEqual(self.ref.keys(), all_data.keys())
        for k in self.ref:
            if isinstance(self.ref[k], np.ndarray):
                np.testing.assert_almost_equal(self.ref[k], all_data[k])
            else:
                self.assertEqual(self.ref[k], all_data[k])

    def test_save2(self):
        """
        Tests saving another valid input.  Difference between this and test_save is that we use velocity as well as all
        optional elements.
        :return:
        """
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution2.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_initial_distribution(f, **self.ref2)

        # Read it back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_initial_distribution(f)

        # Confirm that the keys are the same
        self.assertEqual(self.ref2.keys(), all_data.keys())
        for k in self.ref2:
            if isinstance(self.ref2[k], np.ndarray):
                np.testing.assert_almost_equal(self.ref2[k], all_data[k])
            else:
                self.assertEqual(self.ref2[k], all_data[k])

    def test_save_wrong_dim(self):
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution_wrong_dim.gdf")
        with open(test_file, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save_initial_distribution(f, x=np.linspace(0, 1, 11), y=np.linspace(0, 1, 7))

    def test_save_length_normalization(self):
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution_length_normalization.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_initial_distribution(f, x=np.linspace(0, 1, 11))

        # Read it back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_initial_distribution(f)

        # Check array lengths
        arr_names = ['x', 'y', 'z', 'GBx', 'GBy', 'GBz']
        for a in arr_names:
            self.assertEqual(all_data[a].size, 11)

    def test_save_length_normalization_B(self):
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution_length_normalization_B.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_initial_distribution(f, Bx=np.linspace(0, 1, 11))

        # Read it back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_initial_distribution(f)

        # Check array lengths
        arr_names = ['x', 'y', 'z', 'Bx', 'By', 'Bz']
        for a in arr_names:
            self.assertEqual(all_data[a].size, 11)

    def test_save_both_speed_and_momentum(self):
        """
        Confirms error is thrown if user tries to write both speed and momentum to file
        :return:
        """
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution_both_speed_and_momentum.gdf")
        with open(test_file, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save_initial_distribution(f, Bx=np.linspace(0, 1, 11), GBx=np.linspace(0, 1, 11))

    def test_uniform_interface(self):
        # Try to load the file
        with pkg_resources.resource_stream("easygdf.tests", "data/initial_distribution.gdf") as f:
            all_data = easygdf.load_initial_distribution(f)

        # Directly save it
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distributionuniform_interface.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_initial_distribution(f, **all_data)
