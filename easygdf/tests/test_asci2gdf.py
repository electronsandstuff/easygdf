#  This file is part of easygdf and is released under the BSD 3-clause license

import os
import unittest
import tempfile
import numpy as np
import easygdf


class TestAsci2gdf(unittest.TestCase):
    def test_convert(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Generate test data
            x = np.linspace(0, 1, 32)
            y = np.sin(x)
            fname = os.path.join(tmpdirname, 'fieldmap.txt')
            np.savetxt(fname, np.vstack((x, y)).T, delimiter='\t', header='X\tY', comments='')

            # Try to convert it
            fname2 = os.path.join(tmpdirname, 'out.gdf')
            fname3 = os.path.join(tmpdirname, 'scaled.gdf')
            easygdf.asci2gdf_main([fname])
            easygdf.asci2gdf_main(['-o', fname2, fname])
            easygdf.asci2gdf_main(['-o', fname3, '--scale', 'X', '2', fname])

            # Read back the GDF files
            test = easygdf.load(os.path.join(tmpdirname, 'fieldmap.gdf'))
            np.testing.assert_allclose(next(x for x in test['blocks'] if x['name'] == 'X')['value'], x)
            np.testing.assert_allclose(next(x for x in test['blocks'] if x['name'] == 'Y')['value'], y)
            test = easygdf.load(fname2)
            np.testing.assert_allclose(next(x for x in test['blocks'] if x['name'] == 'X')['value'], x)
            np.testing.assert_allclose(next(x for x in test['blocks'] if x['name'] == 'Y')['value'], y)
            test = easygdf.load(fname3)
            np.testing.assert_allclose(next(x for x in test['blocks'] if x['name'] == 'X')['value'], 2*x)
            np.testing.assert_allclose(next(x for x in test['blocks'] if x['name'] == 'Y')['value'], y)
