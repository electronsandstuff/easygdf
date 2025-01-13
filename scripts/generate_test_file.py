#  This file is part of easygdf and is released under the BSD 3-clause license

"""
This script is used to generate (potentially invalid) GDF files for testing out the library.  All of the files were then
double checked with the utility gdf2a as a third party confirmation that the test files are correct.
"""

import os
import struct
import numpy as np

import easygdf

# Define constants for the GDF specification
GDF_NAME_LEN = 16
GDF_MAGIC = 94325877

# The GDF data type identifiers
GDF_ASCII = 0x0001
GDF_DOUBLE = 0x0003
GDF_FLOAT = 0x0090
GDF_INT8 = 0x0030
GDF_INT16 = 0x0050
GDF_INT32 = 0x0002
GDF_INT64 = 0x0080
GDF_NULL = 0x0010
GDF_UINT8 = 0x0020
GDF_UINT16 = 0x0040
GDF_UINT32 = 0x0060
GDF_UINT64 = 0x0070
GDF_UNDEFINED = 0x0000

# The bit masks for flags in the GDF header
GDF_DTYPE = 255
GDF_GROUP_BEGIN = 256
GDF_GROUP_END = 512
GDF_SINGLE = 1024
GDF_ARRAY = 2048

# Conversion from GDF types to information used by struct to convert into a python type.  First element of the tuple is
# the identifier for conversion and the second element is the size required by struct (so we can double check the file)
GDF_DTYPES_STRUCT = {
    GDF_DOUBLE: ("d", 8),
    GDF_FLOAT: ("f", 4),
    GDF_INT8: ("b", 1),
    GDF_INT16: ("h", 2),
    GDF_INT32: ("i", 4),
    GDF_INT64: ("q", 8),
    GDF_UINT8: ("B", 1),
    GDF_UINT16: ("H", 2),
    GDF_UINT32: ("I", 4),
    GDF_UINT64: ("Q", 8),
}

# The same conversion, but for going to numpy data types
GDF_DTYPES_NUMPY = {
    GDF_DOUBLE: (np.float64, 8),
    GDF_FLOAT: (np.float32, 4),
    GDF_INT8: (np.int8, 1),
    GDF_INT16: (np.int16, 2),
    GDF_INT32: (np.int32, 4),
    GDF_INT64: (np.int64, 8),
    GDF_UINT8: (np.uint8, 1),
    GDF_UINT16: (np.uint16, 2),
    GDF_UINT32: (np.uint32, 4),
    GDF_UINT64: (np.uint64, 8),
}

# Going from numpy data types to GDF types
NUMPY_TO_GDF = {
    "int8": GDF_INT8,
    "int16": GDF_INT16,
    "int32": GDF_INT32,
    "int64": GDF_INT64,
    "uint8": GDF_UINT8,
    "uint16": GDF_UINT16,
    "uint32": GDF_UINT32,
    "uint64": GDF_UINT64,
    "float_": GDF_DOUBLE,
    "float32": GDF_FLOAT,
    "float64": GDF_DOUBLE,
}

# Detect platform specific data types for numpy
for t in ["int_", "intc", "intp"]:
    s = np.dtype(t).itemsize
    if s == 4:
        NUMPY_TO_GDF[t] = GDF_INT32
    elif s == 8:
        NUMPY_TO_GDF[t] = GDF_INT64
    else:
        raise ValueError('Unable to autodetect GDF flag for numpy data type "{0}" with size {1} bytes'.format(t, s))


########################################################################################################################
# Helper functions
########################################################################################################################
def get_header(magic_number=94325877, gdf_version=(1, 1)):
    return struct.pack(
        "2i{0}s{0}s8B".format(easygdf.GDF_NAME_LEN),
        magic_number,
        0,
        bytes("", "ascii"),
        bytes("", "ascii"),
        gdf_version[0],
        gdf_version[1],
        0,
        0,
        0,
        0,
        0,
        0,
    )


def get_block_header(
    name="", dtype=easygdf.GDF_NULL, single=True, array=False, group_begin=False, group_end=False, size=0
):
    flag = dtype + single * GDF_SINGLE + array * GDF_ARRAY + group_begin * GDF_GROUP_BEGIN + group_end * GDF_GROUP_END
    return struct.pack("16sii", bytes(name, "ascii"), flag, size)


########################################################################################################################
# Functions for generating test files
########################################################################################################################
def get_file_version_mismatch():
    """
    Generates a file with a GDF version number that is too high for easygdf to read
    :return: Bytes object representing file
    """
    f = get_header(gdf_version=(10, 0))
    f += get_block_header()
    return f


def get_file_wrong_magic_number():
    """
    Creates a GDF file with the wrong magic number
    :return: Bytes string representing file
    """
    f = get_header(magic_number=1)
    f += get_block_header()
    return f


def get_file_too_much_recursion():
    """
    Makes a file with enough group begin blocks to trigger easygdf's recursion error (at 16 levels by default)
    :return: Bytes string representing file
    """
    f = get_header()
    for _ in range(17):
        f += get_block_header(group_begin=True)
    for _ in range(17):
        f += get_block_header(group_end=True)
    return f


def get_file_group_begin_and_end():
    """
    Makes a GDF file where the first block has both the group start and end bits set (invalid block)
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(group_begin=True, group_end=True)
    return f


def get_file_group_end_root():
    """
    Makes a GDF file with a block that "ends" the root group (not valid)
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(group_end=True)
    return f


def get_file_unterminated_group():
    """
    Makes a GDF file with a group that isn't properly terminated
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(group_begin=True)
    return f


def get_file_empty_group():
    """
    Makes a GDF file with a group that doesn't really have children
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(group_begin=True)
    f += get_block_header(group_end=True)
    return f


def get_file_both_single_array():
    """
    Makes a GDF file with a block that is both single and array (invalid)
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(single=True, array=True)
    return f


def get_file_neither_single_array():
    """
    Makes a GDF file with a block that is neither single and array (invalid)
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(single=False, array=False)
    return f


def get_file_all_dtypes():
    """
    Makes a GDF file with each datatype (single and array) in root group.
    :return: Bytes string representing file
    """
    # GDF header
    f = get_header()

    # Single types
    for dtype in GDF_DTYPES_STRUCT:
        f += get_block_header(dtype=dtype, single=True, array=False, size=GDF_DTYPES_STRUCT[dtype][1])
        f += struct.pack(GDF_DTYPES_STRUCT[dtype][0], 0)
    f += get_block_header(dtype=easygdf.GDF_ASCII, single=True, array=False, size=16)
    f += struct.pack("16s", bytes("deadbeef", "ascii"))
    f += get_block_header(dtype=easygdf.GDF_NULL, single=True, array=False, size=0)
    f += get_block_header(dtype=easygdf.GDF_UNDEFINED, single=True, array=False, size=16)
    f += struct.pack("16s", bytes("deadbeef", "ascii"))

    # Now the array types
    for dtype in GDF_DTYPES_NUMPY:
        f += get_block_header(dtype=dtype, single=False, array=True, size=6 * GDF_DTYPES_STRUCT[dtype][1])
        d = GDF_DTYPES_STRUCT[dtype][0]
        f += struct.pack(6 * d, 0, 1, 2, 3, 4, 5)
    f += get_block_header(dtype=easygdf.GDF_UNDEFINED, single=False, array=True, size=16)
    f += struct.pack("16s", bytes("deadbeef", "ascii"))
    return f


def get_file_invalid_dtype_single():
    """
    Makes a GDF file with an invalid data type for single value
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(dtype=0x0013)
    return f


def get_file_invalid_dtype_array():
    """
    Makes a GDF file with an invalid data type for array value
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(single=False, array=True, dtype=0x0013)
    return f


def get_file_null_array():
    """
    Makes a GDF file with an array of null dtype
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(single=False, array=True, dtype=easygdf.GDF_NULL)
    return f


def get_file_invalid_single_size():
    """
    Makes a GDF file with an invalid size for a single datatype
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(dtype=easygdf.GDF_DOUBLE, size=16)
    f += struct.pack("16s", bytes("deadbeef", "ascii"))
    return f


def get_file_invalid_array_size():
    """
    Makes a GDF file with an invalid size for an array datatype
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(single=False, array=True, dtype=easygdf.GDF_DOUBLE, size=13)
    f += struct.pack("13s", bytes("deadbeef", "ascii"))
    return f


def get_file_nested_group():
    """
    Makes a GDF file with a valid nested group
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(name="group 1", group_begin=True)
    f += get_block_header(name="group 2", group_begin=True)
    f += get_block_header(dtype=easygdf.GDF_ASCII, single=True, array=False, size=16)
    f += struct.pack("16s", bytes("deadbeef", "ascii"))
    f += get_block_header(name="", group_end=True)
    f += get_block_header(name="", group_end=True)
    return f


def get_normalize_screen_floats():
    """
    Makes a GDF file with a valid nested group
    :return: Bytes string representing file
    """
    f = get_header()
    f += get_block_header(
        name="position",
        dtype=GDF_DOUBLE,
        single=True,
        array=False,
        size=GDF_DTYPES_STRUCT[GDF_DOUBLE][1],
        group_begin=True,
    )
    f += struct.pack(GDF_DTYPES_STRUCT[GDF_DOUBLE][0], 0.0)

    for k in ["ID", "x", "y", "z", "Bx", "By", "Bz", "t", "m", "q", "nmacro", "rmacro", "rxy", "G"]:
        dtype = GDF_DOUBLE
        f += get_block_header(name=k, dtype=dtype, single=False, array=True, size=6 * GDF_DTYPES_STRUCT[dtype][1])
        d = GDF_DTYPES_STRUCT[dtype][0]
        f += struct.pack(6 * d, 0, 1, 2, 3, 4, 5)
    f += get_block_header(
        name="Particles", dtype=GDF_DOUBLE, single=True, array=False, size=GDF_DTYPES_STRUCT[GDF_DOUBLE][1]
    )
    f += struct.pack(GDF_DTYPES_STRUCT[GDF_DOUBLE][0], 0.0)
    f += get_block_header(
        name="pCentral", dtype=GDF_DOUBLE, single=True, array=False, size=GDF_DTYPES_STRUCT[GDF_DOUBLE][1]
    )
    f += struct.pack(GDF_DTYPES_STRUCT[GDF_DOUBLE][0], 0.0)
    f += get_block_header(
        name="Charge", dtype=GDF_DOUBLE, single=True, array=False, size=GDF_DTYPES_STRUCT[GDF_DOUBLE][1]
    )
    f += struct.pack(GDF_DTYPES_STRUCT[GDF_DOUBLE][0], 0.0)
    f += get_block_header(name="", group_end=True)
    return f


def write_file(path, b):
    with open(path, "wb") as f:
        f.write(b)


########################################################################################################################
# Script begins here
########################################################################################################################
data_files_path = "easygdf/tests/data"
if __name__ == "__main__":
    write_file(os.path.join(data_files_path, "normalize_screen_floats.gdf"), get_normalize_screen_floats())
    """
    write_file(os.path.join(data_files_path, "version_mismatch.gdf"), get_file_version_mismatch())
    write_file(os.path.join(data_files_path, "wrong_magic_number.gdf"), get_file_wrong_magic_number())
    write_file(os.path.join(data_files_path, "too_much_recursion.gdf"), get_file_too_much_recursion())
    write_file(os.path.join(data_files_path, "group_begin_and_end.gdf"), get_file_group_begin_and_end())
    write_file(os.path.join(data_files_path, "group_end_root.gdf"), get_file_group_end_root())
    write_file(os.path.join(data_files_path, "unterminated_group.gdf"), get_file_unterminated_group())
    write_file(os.path.join(data_files_path, "empty_group.gdf"), get_file_empty_group())
    write_file(os.path.join(data_files_path, "both_single_array.gdf"), get_file_both_single_array())
    write_file(os.path.join(data_files_path, "all_dtypes.gdf"), get_file_all_dtypes())
    write_file(os.path.join(data_files_path, "invalid_dtype_single.gdf"), get_file_invalid_dtype_single())
    write_file(os.path.join(data_files_path, "invalid_dtype_array.gdf"), get_file_invalid_dtype_array())
    write_file(os.path.join(data_files_path, "invalid_size_single.gdf"), get_file_invalid_single_size())
    write_file(os.path.join(data_files_path, "invalid_size_array.gdf"), get_file_invalid_array_size())
    write_file(os.path.join(data_files_path, "nested_groups.gdf"), get_file_nested_group())
    write_file(os.path.join(data_files_path, "null_array.gdf"), get_file_null_array())
    """
