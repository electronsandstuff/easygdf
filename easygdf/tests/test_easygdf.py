#  This file is part of easygdf and is released under the BSD 3-clause license

import datetime
import os
import struct
import tempfile
import unittest

import numpy as np
import pkg_resources

import easygdf


class TestEasyGDFHelpers(unittest.TestCase):
    def test_is_gdf(self):
        # Attempt to open the file and use the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/test.gdf") as f:
            is_gdf = easygdf.is_gdf(f)
        self.assertEqual(is_gdf, True)

        # Try to open one of the text files
        with pkg_resources.resource_stream("easygdf.tests", "test_easygdf.py") as f:
            is_gdf = easygdf.is_gdf(f)
        self.assertEqual(is_gdf, False)

    def test_is_gdf_str_URI(self):
        # Attempt to open the file and use the method under test
        is_gdf = easygdf.is_gdf(pkg_resources.resource_filename("easygdf.tests", "data/test.gdf"))
        self.assertEqual(is_gdf, True)

        # Try to open one of the text files
        is_gdf = easygdf.is_gdf(pkg_resources.resource_filename("easygdf.tests", "test_easygdf.py"))
        self.assertEqual(is_gdf, False)


class TestEasyGDFLoad(unittest.TestCase):
    def test_load_simple_blocks(self):
        """
        Attempts to load a known GDF file created with asci2gdf and checks the blocks against known contents
        :return: None
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/test.gdf") as f:
            all_data = easygdf.load(f)

        # Create the reference data
        reference_data = [
            {"name": "X", "value": np.linspace(0, 5, 6), "children": []},
            {"name": "Y", "value": np.linspace(5, 0, 6), "children": []},
        ]

        # Confirm that the data is the same
        self.assertEqual(len(all_data["blocks"]), len(reference_data))
        for ref_block, test_block in zip(reference_data, all_data["blocks"]):
            # Confirm that the key, param, and children are the same
            self.assertEqual(test_block["name"], ref_block["name"])
            np.testing.assert_allclose(test_block["value"], ref_block["value"])
            self.assertEqual(test_block["children"], ref_block["children"])

    def test_load_simple_header(self):
        """
        Attempts to load a known GDF file created with asci2gdf and checks the header against contents
        :return: None
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/test.gdf") as f:
            all_data = easygdf.load(f)

        # Write out the expected header
        fh = {
            'creation_time': datetime.datetime(2020, 11, 25, 17, 34, 24, tzinfo=datetime.timezone.utc),
            'creator': 'ASCI2GDF',
            'destination': '',
            'gdf_version': (1, 1),
            'creator_version': (1, 0),
            'destination_version': (0, 0),
            'dummy': (0, 0)
        }

        # Compare with what we got
        all_data.pop("blocks")
        self.assertEqual(all_data, fh)

    def test_load_str_URI(self):
        """
        Attempts to load a file specified with a string instead of an open file
        :return: None
        """
        # Get the filename and open it with easygdf
        fname = pkg_resources.resource_filename("easygdf.tests", "data/test.gdf")
        all_data = easygdf.load(fname)

        # Write out the expected header
        fh = {
            'creation_time': datetime.datetime(2020, 11, 25, 17, 34, 24, tzinfo=datetime.timezone.utc),
            'creator': 'ASCI2GDF',
            'destination': '',
            'gdf_version': (1, 1),
            'creator_version': (1, 0),
            'destination_version': (0, 0),
            'dummy': (0, 0)
        }

        # Compare with what we got
        all_data.pop("blocks")
        self.assertEqual(all_data, fh)

    def test_load_all_dtypes(self):
        """
        Loads file with every dtype represented and compares with expected values
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/all_dtypes.gdf") as f:
            all_data = easygdf.load(f)

        # Check each block to confirm we got the correct value(s) back
        blocks = all_data["blocks"]

        # Single valued types
        self.assertEqual(blocks[0]["value"], 0.0)
        self.assertEqual(blocks[1]["value"], 0.0)
        self.assertEqual(blocks[2]["value"], 0)
        self.assertEqual(blocks[3]["value"], 0)
        self.assertEqual(blocks[4]["value"], 0)
        self.assertEqual(blocks[5]["value"], 0)
        self.assertEqual(blocks[6]["value"], 0)
        self.assertEqual(blocks[7]["value"], 0)
        self.assertEqual(blocks[8]["value"], 0)
        self.assertEqual(blocks[9]["value"], 0)
        self.assertEqual(blocks[10]["value"], "deadbeef")
        self.assertEqual(blocks[11]["value"], None)
        self.assertEqual(blocks[12]["value"], struct.pack("16s", bytes("deadbeef", "ascii")))

        # Array types
        np.testing.assert_equal(blocks[13]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[14]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[15]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[16]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[17]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[18]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[19]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[20]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[21]["value"], np.linspace(0, 5, 6))
        np.testing.assert_equal(blocks[22]["value"], np.linspace(0, 5, 6))
        self.assertEqual(blocks[23]["value"], struct.pack("16s", bytes("deadbeef", "ascii")))

    def test_load_both_single_array(self):
        """
        Loads file with block that has both single and array bits set.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/both_single_array.gdf") as f:
            with self.assertRaises(ValueError):
                easygdf.load(f)

    def test_load_empty_group(self):
        """
        Attempts to load a file with an empty group.
        :return: None
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/empty_group.gdf") as f:
            all_data = easygdf.load(f)

        # Check that the block shows up w/o children
        self.assertEqual(len(all_data["blocks"][0]["children"]), 0)

    def test_load_group_begin_and_end(self):
        """
        Loads file with a block that has a group begin and group end bit set.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/group_begin_and_end.gdf") as f:
            with self.assertRaises(ValueError):
                easygdf.load(f)

    def test_load_end_root(self):
        """
        Loads file with an end block in the root group.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/group_end_root.gdf") as f:
            with self.assertRaises(ValueError):
                easygdf.load(f)

    def test_load_invalid_dtype_array(self):
        """
        Loads file with an invalid dtype for an array block.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/invalid_dtype_array.gdf") as f:
            with self.assertRaises(TypeError):
                easygdf.load(f)

    def test_load_invalid_dtype_single(self):
        """
        Loads file with an invalid dtype for a single block.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/invalid_dtype_single.gdf") as f:
            with self.assertRaises(TypeError):
                easygdf.load(f)

    def test_load_invalid_size_array(self):
        """
        Loads file with an invalid size for an array block.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/invalid_size_array.gdf") as f:
            with self.assertRaises(ValueError):
                easygdf.load(f)

    def test_load_invalid_size_single(self):
        """
        Loads file with an invalid size for a single block.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/invalid_size_single.gdf") as f:
            with self.assertRaises(ValueError):
                easygdf.load(f)

    def test_load_nested_groups(self):
        """
        Loads file with multiple levels of groups.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/nested_groups.gdf") as f:
            all_data = easygdf.load(f)

        self.assertEqual(all_data["blocks"][0]["children"][0]["children"][0]["value"], "deadbeef")

    def test_load_too_much_recursion(self):
        """
        Loads file with enough groups to cause recursion error.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/too_much_recursion.gdf") as f:
            with self.assertRaises(RecursionError):
                easygdf.load(f)

    def test_load_unterminated_group(self):
        """
        Loads file with a group that is never ended correctly.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/unterminated_group.gdf") as f:
            with self.assertRaises(IOError):
                easygdf.load(f)

    def test_load_version_mismatch(self):
        """
        Loads file with a version that is too new.  Confirms warning is created.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/version_mismatch.gdf") as f:
            with self.assertWarns(Warning):
                easygdf.load(f)

    def test_load_wrong_magic_number(self):
        """
        Loads file with the wrong magic number.  Confirms exception is thrown.
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/wrong_magic_number.gdf") as f:
            with self.assertRaises(easygdf.GDFIOError):
                easygdf.load(f)

    def test_load_null_array(self):
        """
        Confirms exception is thrown when loading file with array that has null dtype
        :return:
        """
        # Attempt to open the file with the method under test
        with pkg_resources.resource_stream("easygdf.tests", "data/null_array.gdf") as f:
            with self.assertRaises(TypeError):
                easygdf.load(f)


class TestEasyGDFSave(unittest.TestCase):
    def test_save_simple(self):
        """
        Saves same data as stored in a known existing binary file and compares the two.
        :return:
        """
        # Write the header expected for the reference file
        fh = {
            'creation_time': datetime.datetime(2020, 11, 25, 17, 34, 24, tzinfo=datetime.timezone.utc),
            'creator': 'ASCI2GDF',
            'destination': '',
            'gdf_version': (1, 1),
            'creator_version': (1, 0),
            'destination_version': (0, 0),
            'dummy': (0, 0)
        }

        # Write out the block data for the reference file
        blocks = [
            {"name": "X", "value": np.linspace(0, 5, 6), "children": []},
            {"name": "Y", "value": np.linspace(5, 0, 6), "children": []},
        ]

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "easygdf_test.gdf")
        with open(test_file, "wb") as f:
            easygdf.save(f, blocks, **fh)

        # Read it back and read back the reference file
        with open(test_file, "rb") as f:
            test_data = bytearray(f.read())
        with pkg_resources.resource_stream("easygdf.tests", "data/test.gdf") as f:
            reference_data = bytearray(f.read())

        # Blank out the last bit of the string buffers that weren't written with zeros in the reference copy
        reference_data[31] = 0x00
        reference_data[32] = 0x00
        reference_data[33] = 0x00
        reference_data[34] = 0x00
        reference_data[56] = 0x00
        reference_data[57] = 0x00
        reference_data[58] = 0x00
        reference_data[59] = 0x00
        reference_data[60] = 0x00
        reference_data[61] = 0x00
        reference_data[128] = 0x00
        reference_data[129] = 0x00
        reference_data[130] = 0x00
        reference_data[131] = 0x00
        reference_data[132] = 0x00
        reference_data[133] = 0x00

        # Check the files against each other
        self.assertEqual(test_data, reference_data)

    def test_save_str_URI(self):
        """
        Saves same data as stored in a known existing binary file and compares the two, but uses a string filename
        instead of an open stream.
        :return:
        """
        # Write the header expected for the reference file
        fh = {
            'creation_time': datetime.datetime(2020, 11, 25, 17, 34, 24, tzinfo=datetime.timezone.utc),
            'creator': 'ASCI2GDF',
            'destination': '',
            'gdf_version': (1, 1),
            'creator_version': (1, 0),
            'destination_version': (0, 0),
            'dummy': (0, 0)
        }

        # Write out the block data for the reference file
        blocks = [
            {"name": "X", "value": np.linspace(0, 5, 6), "children": []},
            {"name": "Y", "value": np.linspace(5, 0, 6), "children": []},
        ]

        # Write it to the temp directory
        test_file = os.path.join(tempfile.gettempdir(), "easygdf_test_URI.gdf")
        easygdf.save(test_file, blocks, **fh)

        # Read it back and read back the reference file
        with open(test_file, "rb") as f:
            test_data = bytearray(f.read())
        with pkg_resources.resource_stream("easygdf.tests", "data/test.gdf") as f:
            reference_data = bytearray(f.read())

        # Blank out the last bit of the string buffers that weren't written with zeros in the reference copy
        reference_data[31] = 0x00
        reference_data[32] = 0x00
        reference_data[33] = 0x00
        reference_data[34] = 0x00
        reference_data[56] = 0x00
        reference_data[57] = 0x00
        reference_data[58] = 0x00
        reference_data[59] = 0x00
        reference_data[60] = 0x00
        reference_data[61] = 0x00
        reference_data[128] = 0x00
        reference_data[129] = 0x00
        reference_data[130] = 0x00
        reference_data[131] = 0x00
        reference_data[132] = 0x00
        reference_data[133] = 0x00

        # Check the files against each other
        self.assertEqual(test_data, reference_data)

    def test_save_all_dtypes(self):
        """
        Saves each possible valid datatype and
        :return:
        """
        # Make a place to hold blocks which we will write
        ref_blocks = []

        # Dump all of the possible numpy array types into blocks
        dtypes = ["int8", "int16", "int32", "int64", "uint8", "uint16", "uint32", "uint64", "float_",
                  "float32", "float64"]
        for dtype in dtypes:
            ref_blocks.append({
                "name": "array_" + dtype,
                "value": np.linspace(0, 5, 6, dtype=dtype),
            })

        # Add each single type
        ref_blocks.append({
            "name": "single_str",
            "value": "deadbeef",
        })
        ref_blocks.append({
            "name": "single_int",
            "value": 1729,
        })
        ref_blocks.append({
            "name": "single_float",
            "value": 3.14,
        })
        ref_blocks.append({
            "name": "single_none",
            "value": None,
        })

        # Save everything as a GDF file
        testfile = os.path.join(tempfile.gettempdir(), "save_all_dtypes.gdf")
        with open(testfile, "wb") as f:
            easygdf.save(f, ref_blocks)

        # Read it back in
        with open(testfile, "rb") as f:
            data = easygdf.load(f)

        # Go through the blocks and make sure they match
        for test, ref in zip(data["blocks"], ref_blocks):
            self.assertEqual(test["name"], ref["name"])
            if isinstance(ref["value"], np.ndarray):
                np.testing.assert_equal(test["value"], ref["value"])
            else:
                self.assertEqual(test["value"], ref["value"])

    def test_save_invalid_file(self):
        """
        Confirms exception is thrown when not given a file
        :return:
        """
        with self.assertRaises(easygdf.GDFIOError):
            easygdf.save(100, [])

    def test_save_wrong_file_mode(self):
        """
        Confirms exception is thrown when file open in wrong mode
        :return:
        """
        testfile = os.path.join(tempfile.gettempdir(), "save_wrong_file_mode.gdf")
        with open(testfile, "w") as f:
            with self.assertRaises(easygdf.GDFIOError):
                easygdf.save(f, [])

    def test_save_block_has_bad_key(self):
        """
        Confirms exception is thrown when block is given with an incorrect key
        :return:
        """
        testfile = os.path.join(tempfile.gettempdir(), "save_has_bad_key.gdf")
        with open(testfile, "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save(f, [{"Bad Key": None}])

    def test_save_block_bad_dtype(self):
        """
        Confirms exception is thrown when block is given with incorrect datatype for key
        :return:
        """
        testfile = os.path.join(tempfile.gettempdir(), "save_has_bad_key.gdf")
        with open(testfile, "wb") as f:
            with self.assertRaises(TypeError):
                easygdf.save(f, [{"name": None}])
        with open(testfile, "wb") as f:
            with self.assertRaises(TypeError):
                easygdf.save(f, [{"children": "my children"}])
        with open(testfile, "wb") as f:
            with self.assertRaises(TypeError):
                easygdf.save(f, [{"value": {"a": "dictionary"}}])

    def test_save_block_bad(self):
        """
        Try throwing random stuff into the blocks section
        :return:
        """
        testfile = os.path.join(tempfile.gettempdir(), "save_has_bad_key.gdf")
        with open(testfile, "wb") as f:
            with self.assertRaises(TypeError):
                easygdf.save(f, "some blocks")

    def test_header_write(self):
        """
        Saves a header and confirms it is the same after reading it back
        :return:
        """
        # Create a header to save
        my_time = datetime.datetime.fromtimestamp(int(datetime.datetime.timestamp(datetime.datetime.now())),
                                                  tz=datetime.timezone.utc)
        fh = {
            "creation_time": my_time,
            "creator": "easygdf",
            "destination": "hardgdf",
            "gdf_version": (1, 1),
            "creator_version": (3, 4),
            "destination_version": (5, 6),
            "dummy": (7, 8),
        }

        # Save it and reload it
        testfile = os.path.join(tempfile.gettempdir(), "save_header.gdf")
        with open(testfile, "wb") as f:
            easygdf.save(f, [], **fh)
        with open(testfile, "rb") as f:
            test = easygdf.load(f)

        # Check that the headers are the same
        test.pop("blocks")
        self.assertEqual(fh, test)

    def test_save_groups(self):
        """
        Try some blocks that have children
        :return:
        """
        # The reference blocks
        ref = [
            {"name": "A",
             "value": 0,
             "children": [
                 {"name": "B",
                  "value": "string",
                  "children": [
                      {"name": "C",
                       "value": 1.2,
                       "children": [
                           {"name": "D",
                            "value": "another string",
                            "children": []}
                       ]}
                  ]}
             ]}
        ]

        # Write it and read it back
        testfile = os.path.join(tempfile.gettempdir(), "save_groups.gdf")
        with open(testfile, "wb") as f:
            easygdf.save(f, ref)
        with open(testfile, "rb") as f:
            test = easygdf.load(f)["blocks"]

        # Check that they match
        self.assertEqual(test, ref)

    def test_save_recursion_limit(self):
        """
        Try hitting the recursion limit (16 levels by default)
        :return:
        """
        # Create a super deep set of blocks
        blocks = [{}]
        for _ in range(17):
            blocks = [{"children": blocks}]

        # Save the file and check the exception
        testfile = os.path.join(tempfile.gettempdir(), "save_recursion_limit.gdf")
        with open(testfile, "wb") as f:
            with self.assertRaises(RecursionError):
                easygdf.save(f, blocks)

    def test_save_bad_numpy_dtype(self):
        """
        Confirm exception when writing numpy array with dtype incompatible with GDF
        :return:
        """
        # Save the file and check the exception
        testfile = os.path.join(tempfile.gettempdir(), "save_bad_numpy_dtype.gdf")
        with open(testfile, "wb") as f:
            with self.assertRaises(TypeError):
                easygdf.save(f, [{"value": np.linspace(0, 5, 6, dtype=np.complex)}])

    def test_int_single_overflow(self):
        """
        Confirms error is thrown if an integer larger than GDFs max size is passed. Test this for both positive and
        negative values.  The positive integer should be cast to uint32 and the negative to int32.

        :return:
        """
        # Test overflowing the negative value
        with open(os.path.join(tempfile.gettempdir(), "save_int_single_overflow_1.gdf"), "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save(f, [{'name': 'ID', 'value': -0x80000000, 'children': []}, ])

        # Confirm something bigger than the max int32 but smaller than the max uint32 doesn't overflow
        with open(os.path.join(tempfile.gettempdir(), "save_int_single_overflow_2.gdf"), "wb") as f:
            easygdf.save(f, [{'name': 'ID', 'value': 0x80000000, 'children': []}, ])

        # Test overflowing the positive value
        with open(os.path.join(tempfile.gettempdir(), "save_int_single_overflow_3.gdf"), "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save(f, [{'name': 'ID', 'value': 0x100000000, 'children': []}, ])

    def test_int_array_overflow(self):
        """
        Confirms error is thrown if an integer larger than GDFs max size is passed, array version

        :return:
        """
        # Test overflowing int32
        with open(os.path.join(tempfile.gettempdir(), "save_int_array_overflow_1.gdf"), "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save(f, [{'name': 'ID', 'value': np.array([0x80000000, 0, 0, 0], dtype=np.int64),
                                  'children': []}, ])

        # Test overflowing int64
        with open(os.path.join(tempfile.gettempdir(), "save_int_array_overflow_2.gdf"), "wb") as f:
            with self.assertRaises(ValueError):
                easygdf.save(f, [{'name': 'ID', 'value': np.array([0x100000000, 0, 0, 0], dtype=np.uint64),
                                  'children': []}, ])


class TestEasyGDFLoadSave(unittest.TestCase):
    def test_uniform_interface(self):
        """
        This test confirms that the output of the load function can be dumped directly into the input of the save
        function of the library with no modifications.  This is one of my requirements for the library and would like a
        check on it.

        :return: None
        """
        # Open up one of our test problems
        with pkg_resources.resource_stream("easygdf.tests", "data/test.gdf") as f:
            all_data = easygdf.load(f)

        # Save it again
        test_file = os.path.join(tempfile.gettempdir(), "easygdf_interface_test.gdf")
        with open(test_file, "wb") as f:
            easygdf.save(f, **all_data)

    def test_integer_casting(self):
        """
        Confirms that integer 64 bit arrays get cast to 32 bits and saved.  This is related to github issue 5 because
        GDF appears to not support 64 bit integers.

        :return:
        """
        # Test conversion from int64 -> int32
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution_test_integer_casting_1.gdf")
        with open(test_file, "wb") as f:
            easygdf.save(f, [{'name': 'ID', 'value': np.zeros(32, dtype=np.int64), 'children': []}, ])
        self.assertEqual(easygdf.load_initial_distribution(test_file)['ID'].dtype, np.dtype('int32'))

        # Test conversion from uint64 -> uint32
        test_file = os.path.join(tempfile.gettempdir(), "save_initial_distribution_test_integer_casting_2.gdf")
        with open(test_file, "wb") as f:
            easygdf.save(f, [{'name': 'ID', 'value': np.zeros(32, dtype=np.uint64), 'children': []}, ])
        self.assertEqual(easygdf.load_initial_distribution(test_file)['ID'].dtype, np.dtype('uint32'))