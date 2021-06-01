#  This file is part of easygdf and is released under the BSD 3-clause license

import os
import tempfile
import unittest

import numpy as np
import pkg_resources

import easygdf


class TestEasyGDFScreensTouts(unittest.TestCase):
    def setUp(self):
        # Gross data-dump of a test file that we will check against
        self.ref = {'screens': [{
            'x': np.array([3.173e-05, 2.286e-05, 2.331e-05, 3.735e-05, 3.040e-05]),
            'y': np.array([1.553e-06, 1.502e-06, 1.586e-06, 3.577e-06, 3.277e-06]),
            'z': np.array([0.01, 0.01, 0.01, 0.01, 0.01]),
            'rxy': np.array([3.177e-05, 2.291e-05, 2.337e-05, 3.752e-05, 3.057e-05]),
            'Bx': np.array([1.697e-04, 1.010e-04, 9.218e-05, 1.604e-04, 1.269e-04]),
            'By': np.array([-1.008e-06, -9.377e-08, -2.000e-06, 1.504e-05, 9.206e-06]),
            'Bz': np.array([0.5728, 0.5728, 0.5728, 0.5728, 0.5728]),
            'G': np.array([1.22, 1.22, 1.22, 1.22, 1.22]),
            't': np.array([7.681e-11, 7.682e-11, 7.655e-11, 7.662e-11, 7.650e-11]),
            'm': np.array([9.11e-31, 9.11e-31, 9.11e-31, 9.11e-31, 9.11e-31]),
            'q': np.array([-1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19]),
            'nmacro': np.array([8.752, 8.752, 8.752, 8.752, 8.752]),
            'rmacro': np.array([0., 0., 0., 0., 0.]),
            'ID': np.array([917., 1199., 1259., 1525., 1778.]), 'position': 0.01
        }],
            'touts': [{
                'scat_x': np.array([], dtype=np.float64), 'scat_y': np.array([], dtype=np.float64),
                'scat_z': np.array([], dtype=np.float64), 'scat_Qin': np.array([], dtype=np.float64),
                'scat_Qout': np.array([], dtype=np.float64), 'scat_Qnet': np.array([], dtype=np.float64),
                'scat_Ein': np.array([], dtype=np.float64), 'scat_Eout': np.array([], dtype=np.float64),
                'scat_Enet': np.array([], dtype=np.float64), 'scat_inp': np.array([], dtype=np.float64),
                'x': np.array([2.382e-05, 3.331e-05, 3.331e-05, 3.626e-05, 1.664e-05]),
                'y': np.array([-1.266e-08, 4.958e-08, 5.084e-08, 8.397e-08, 4.197e-08]),
                'z': np.array([2.876e-04, 1.831e-04, 9.718e-05, 1.503e-04, 2.548e-05]),
                'G': np.array([1.006, 1.004, 1.002, 1.003, 1.001]),
                'Bx': np.array([2.782e-04, 3.723e-04, 3.003e-04, 4.009e-04, 3.904e-05]),
                'By': np.array([-1.447e-05, 3.594e-06, 9.107e-06, 2.116e-05, 8.227e-06]),
                'Bz': np.array([0.112, 0.08946, 0.0652, 0.08107, 0.03326]),
                'rxy': np.array([2.382e-05, 3.331e-05, 3.331e-05, 3.626e-05, 1.664e-05]),
                'm': np.array([9.11e-31, 9.11e-31, 9.11e-31, 9.11e-31, 9.11e-31]),
                'q': np.array([-1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19, -1.602e-19]),
                'nmacro': np.array([8.752, 8.752, 8.752, 8.752, 8.752]), 'rmacro': np.array([0., 0., 0., 0., 0.]),
                'ID': np.array([2., 3., 4., 5., 6.]), 'fEx': np.array([-20340., -38070., -56560., -48510., -33310.]),
                'fEy': np.array([635.5, 737.7, -882.6, -1992., -1727.]),
                'fEz': np.array([-11250000., -11250000., -11250000., -11250000., -11190000.]),
                'fBx': np.array([-1.715e-07, -2.003e-07, 2.240e-07, 5.139e-07, 4.488e-07]),
                'fBy': np.array([-5.324e-06, -9.967e-06, -1.481e-05, -1.270e-05, -8.721e-06]),
                'fBz': np.array([4.428e-05, 4.423e-05, 4.420e-05, 4.422e-05, 4.417e-05]), 'time': 0.0
            }], 'logo': 'B&M-General Particle Tracer', 'scat_x': np.array([], dtype=np.float64),
            'scat_y': np.array([], dtype=np.float64), 'scat_z': np.array([], dtype=np.float64),
            'scat_Qin': np.array([], dtype=np.float64), 'scat_Qout': np.array([], dtype=np.float64),
            'scat_Qnet': np.array([], dtype=np.float64), 'scat_Ein': np.array([], dtype=np.float64),
            'scat_Eout': np.array([], dtype=np.float64), 'scat_Enet': np.array([], dtype=np.float64),
            'scat_inp': np.array([], dtype=np.float64), 'numderivs': 0, 'cputime': 6054.0}

    def test_load_screens_touts(self):
        # Try to load the file
        with pkg_resources.resource_stream("easygdf.tests", "data/screens_touts.gdf") as f:
            all_data = easygdf.load_screens_touts(f)

        # Ditch the header
        header_names = ["creation_time", "creator", "destination", "gdf_version", "creator_version",
                        "destination_version", "dummy"]
        for hn in header_names:
            all_data.pop(hn)

        # Compare with the reference
        self.assertEqual(all_data.keys(), self.ref.keys())

        # Go through each lower param
        for key in all_data:
            if key not in ["screens", "touts"]:
                if isinstance(all_data[key], np.ndarray):
                    np.testing.assert_almost_equal(all_data[key], self.ref[key])
                else:
                    self.assertEqual(all_data[key], self.ref[key])

        # Now check the screens and touts
        self.assertEqual(len(all_data["screens"]), len(self.ref["screens"]))
        for ts, rs in zip(all_data["screens"], self.ref["screens"]):
            self.assertEqual(ts.keys(), rs.keys())
            for key in ts:
                if isinstance(ts[key], np.ndarray):
                    np.testing.assert_almost_equal(ts[key], rs[key])
                else:
                    self.assertEqual(ts[key], rs[key])
        self.assertEqual(len(all_data["touts"]), len(self.ref["touts"]))
        for ts, rs in zip(all_data["touts"], self.ref["touts"]):
            self.assertEqual(ts.keys(), rs.keys())
            for key in ts:
                if isinstance(ts[key], np.ndarray):
                    np.testing.assert_almost_equal(ts[key], rs[key])
                else:
                    self.assertEqual(ts[key], rs[key])

    def test_save_screens_touts(self):
        """
        Writes our reference screen/tout object and confirms we get something similar back
        :return:
        """
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_touts.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_screens_touts(f, **self.ref)

        # Read it back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_screens_touts(f)

        # Ditch the header
        header_names = ["creation_time", "creator", "destination", "gdf_version", "creator_version",
                        "destination_version", "dummy"]
        for hn in header_names:
            all_data.pop(hn)

        # Compare with the reference
        self.assertEqual(all_data.keys(), self.ref.keys())

        # Go through each lower param
        for key in all_data:
            if key not in ["screens", "touts"]:
                if isinstance(all_data[key], np.ndarray):
                    np.testing.assert_almost_equal(all_data[key], self.ref[key])
                else:
                    self.assertEqual(all_data[key], self.ref[key])

        # Now check the screens and touts
        self.assertEqual(len(all_data["screens"]), len(self.ref["screens"]))
        for ts, rs in zip(all_data["screens"], self.ref["screens"]):
            self.assertEqual(ts.keys(), rs.keys())
            for key in ts:
                if isinstance(ts[key], np.ndarray):
                    np.testing.assert_almost_equal(ts[key], rs[key])
                else:
                    self.assertEqual(ts[key], rs[key])
        self.assertEqual(len(all_data["touts"]), len(self.ref["touts"]))
        for ts, rs in zip(all_data["touts"], self.ref["touts"]):
            self.assertEqual(ts.keys(), rs.keys())
            for key in ts:
                if isinstance(ts[key], np.ndarray):
                    np.testing.assert_almost_equal(ts[key], rs[key])
                else:
                    self.assertEqual(ts[key], rs[key])

    def test_save_screens_touts_scatter(self):
        """
        Writes a scatter object to confirm easygdf will auto-correct the array lengths.
        :return:
        """
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_touts_scatter.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_screens_touts(f, scat_Ein=np.linspace(0, 1, 10))

        # Read the file back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_screens_touts(f)

        # Confirm the lengths of the array objects
        arr = ["scat_x", "scat_y", "scat_z", "scat_Qin", "scat_Qout", "scat_Qnet", "scat_Ein", "scat_Eout",
               "scat_Enet", "scat_inp"]
        for an in arr:
            self.assertEqual(all_data[an].shape, all_data["scat_Ein"].shape)

    def test_save_screens_touts_scatter_wrong_dim(self):
        """
        Confirms error is thrown when two array elements of incorrect length are given to screen/tout save.
        :return:
        """
        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_touts_scatter_wrong_dim.gdf")
        with open(test_file, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save_screens_touts(f, scat_Ein=np.linspace(0, 1, 10), scat_Enet=np.linspace(0, 1, 9))

    def test_save_screens_touts_tout_arr(self):
        """
        Writing touts with array elements to confirm padding
        :return:
        """
        # Make a tout to write
        tout = {"scat_x": np.linspace(0, 1, 7), "x": np.linspace(0, 1, 11), "y": np.linspace(0, 1, 11),
                "Bx": np.linspace(0, 0.1, 11), "By": np.linspace(0, 0.1, 11)}

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_tout_tout_arr.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_screens_touts(f, touts=[tout, ])

        # Read it back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_screens_touts(f)

        # Confirm that the tout has the correctly shaped arrays
        arr = ["scat_x", "scat_y", "scat_z", "scat_Qin", "scat_Qout", "scat_Qnet", "scat_Ein", "scat_Eout",
               "scat_Enet", "scat_inp"]
        for an in arr:
            self.assertEqual(all_data["touts"][0][an].shape, all_data["touts"][0]["scat_x"].shape)
        arr2 = ["x", "y", "z", "G", "Bx", "By", "Bz", "rxy", "m", "q", "nmacro", "rmacro", "ID", "fEx", "fEy", "fEz",
                "fBx", "fBy", "fBz"]
        for an in arr2:
            self.assertEqual(all_data["touts"][0][an].shape, all_data["touts"][0]["x"].shape)

        # Check that specific entries have autofilled correctly
        to = all_data["touts"][0]
        np.testing.assert_almost_equal(to["rxy"], np.sqrt(to["x"] ** 2 + to["y"] ** 2))
        np.testing.assert_almost_equal(to["G"], 1 / np.sqrt(1 - to["Bx"] ** 2 - to["By"] ** 2))
        np.testing.assert_almost_equal(to["ID"], np.linspace(0, 10, 11))

    def test_save_screens_touts_tout_arr_wrong_dim(self):
        """
        Confirms error is thrown when arrays with wrong dimension are included
        :return:
        """
        # Make a tout to write
        tout = {"x": np.linspace(0, 1, 11), "y": np.linspace(0, 1, 7)}

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_tout_tout_arr_wrong_dim.gdf")
        with open(test_file, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save_screens_touts(f, touts=[tout, ])

        # Make a tout to write
        tout = {"scat_x": np.linspace(0, 1, 7), "scat_y": np.linspace(0, 1, 11)}

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_tout_tout_arr_wrong_dim2.gdf")
        with open(test_file, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save_screens_touts(f, touts=[tout, ])

        # Make a tout to write
        tout = {"scat_x": np.linspace(0, 1, 7), "scat_y": np.linspace(0, 1, 11), "x": np.linspace(0, 1, 11),
                "y": np.linspace(0, 1, 7)}

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_tout_tout_arr_wrong_dim3.gdf")
        with open(test_file, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save_screens_touts(f, touts=[tout, ])

    def test_save_screens_touts_tout_aux_elem(self):
        """
        Checks that we may save touts with auxiliary elements
        :return:
        """
        # Make a tout to write
        tout = {"deadbeef": np.linspace(0, 1, 11), }

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_touts_tout_wrong_elem.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_screens_touts(f, touts=[tout, ])

        # Load it back and check we saved it
        all_data = easygdf.load_screens_touts(test_file)
        self.assertEqual(all_data["touts"][0]["deadbeef"].size, 11)

    def test_save_screens_touts_screen_arr(self):
        """
        Writing screens with array elements to confirm padding
        :return:
        """
        # Make a tout to write
        screen = {"x": np.linspace(0, 1, 11), "y": np.linspace(0, 1, 11),
                  "Bx": np.linspace(0, 0.1, 11), "By": np.linspace(0, 0.1, 11)}

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_touts_screen_arr.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_screens_touts(f, screens=[screen, ])

        # Read it back
        with open(test_file, "rb") as f:
            all_data = easygdf.load_screens_touts(f)

        # Confirm that the tout has the correctly shaped arrays
        arr2 = ["x", "y", "z", "G", "Bx", "By", "Bz", "rxy", "m", "q", "nmacro", "rmacro", "ID", "t"]
        for an in arr2:
            self.assertEqual(all_data["screens"][0][an].shape, all_data["screens"][0]["x"].shape)

        # Check that specific entries have autofilled correctly
        ss = all_data["screens"][0]
        np.testing.assert_almost_equal(ss["rxy"], np.sqrt(ss["x"] ** 2 + ss["y"] ** 2))
        np.testing.assert_almost_equal(ss["G"], 1 / np.sqrt(1 - ss["Bx"] ** 2 - ss["By"] ** 2))
        np.testing.assert_almost_equal(ss["ID"], np.linspace(0, 10, 11))

    def test_save_screens_touts_screen_arr_wrong_dim(self):
        """
        Confirms error is thrown when arrays with wrong dimension are included
        :return:
        """
        # Make a tout to write
        screen = {"x": np.linspace(0, 1, 11), "y": np.linspace(0, 1, 7)}

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_touts_screen_arr_wrong_dim.gdf")
        with open(test_file, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save_screens_touts(f, screens=[screen, ])

    def test_save_screens_touts_screen_aux_elem(self):
        """
        Makes sure we can save screens w/ auxiliary elements
        :return:
        """
        # Make a tout to write
        screen = {"deadbeef": np.linspace(0, 1, 11)}

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "save_screens_touts_tout_wrong_elem.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_screens_touts(f, screens=[screen, ])

        # Load it back and check we saved it
        all_data = easygdf.load_screens_touts(test_file)
        self.assertEqual(all_data["screens"][0]["deadbeef"].size, 11)

    def test_screens_touts_uniform_interface(self):
        """
        Confirms that the output of the screen/tout loader can be dumped directly into the saver
        :return:
        """
        # Load a file
        with pkg_resources.resource_stream("easygdf.tests", "data/screens_touts.gdf") as f:
            all_data = easygdf.load_screens_touts(f)

        # Try to save it
        test_file = os.path.join(tempfile.gettempdir(), "screens_touts_uniform_interface.gdf")
        with open(test_file, "wb") as f:
            easygdf.save_screens_touts(f, **all_data)

    def test_normalize_screen_float(self):
        """
        Tests screen normalization with a file that has a float in screen.  This test added as part of pull-request 2
        """
        # Load a file
        with pkg_resources.resource_stream("easygdf.tests", "data/normalize_screen_floats.gdf") as f:
            all_data = easygdf.load_screens_touts(f)
