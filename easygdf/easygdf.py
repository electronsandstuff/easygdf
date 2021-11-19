#  This file is part of easygdf and is released under the BSD 3-clause license

########################################################################################################################
# Imports
########################################################################################################################
import datetime
import io
import struct
import warnings

import numpy as np

from .utils import GDFIOError

########################################################################################################################
# GDF Specific Constants
########################################################################################################################
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
        raise ValueError("Unable to autodetect GDF flag for numpy data type \"{0}\" with size {1} bytes".format(t, s))

# The bit masks for flags in the GDF header
GDF_DTYPE = 255
GDF_GROUP_BEGIN = 256
GDF_GROUP_END = 512
GDF_SINGLE = 1024
GDF_ARRAY = 2048


########################################################################################################################
# Library functions start here
########################################################################################################################
def is_gdf(f):
    """
    Determines if a file is GDF formatted or not.

    If binary file is passed, file will be at location four bytes from start after this function is run.

    :param f: filename or open file/stream-like object
    :return: True/False whether the file is GDF formatted
    """
    # If we were handed a string, then run this function on it with the file opened
    if isinstance(f, str):
        with open(f, "rb") as ff:
            return is_gdf(ff)

    # Rewind the file to the beginning
    f.seek(0)

    # Get the magic number
    magic_number, = struct.unpack('i', f.read(4))

    # Check it against the real magic number
    return magic_number == GDF_MAGIC


def load_blocks(f, level=0, max_recurse=16, max_block=1e6):
    """
    Internal function.  Recursively reads groups of blocks in the GDF file.  Until group end or file end, block header
    is read and data is read.  If it is a group, we recurse to read all children until the group ends.

    :param f: An open file-like object which is read up to the point of the start of a group
    :param level: Tracks the level of recursion as the function is run.  Don't mess with it if calling externally.
    :param max_recurse: Maximum level of recursion before easyGDF will throw an error
    :param max_block: Maximum number of blocks that are allowed in this group before easyGDF throws error
    :return: list of blocks in this group
    """
    # If we have hit the max recursion depth throw an error
    if level >= max_recurse:
        raise RecursionError("Max GDF depth of recursion (set to {:d}) exceeded".format(max_recurse))

    # Make a place for the blocks
    blocks = []

    # Loop over the blocks
    for block_ind in range(int(max_block)):
        # Read the block's header
        header_raw = f.read(GDF_NAME_LEN + 8)

        # If no data came back and we are in the root group, then break.  If this isn't root group, then something
        # went wrong.
        if header_raw == b'':
            if level == 0:
                break
            else:
                raise IOError("File ended in middle of GDF group")

        # Unpack the header
        block_name, block_type_flag, block_size = struct.unpack("{0}sii".format(GDF_NAME_LEN), header_raw)
        block_name = block_name.split(b'\0', 1)[0].decode('ascii')

        # Make a new empty block with the correct name
        block = {"name": block_name, "value": None, "children": []}

        # Break up the type flag into group operations and throw an error if invalid
        group_begin = bool(block_type_flag & GDF_GROUP_BEGIN)
        group_end = bool(block_type_flag & GDF_GROUP_END)
        if group_begin and group_end:
            raise ValueError("Potentially invalid group flags in block "
                             "(\"group_begin\" = {0} \"group_end\" = {1}".format(group_begin, group_end))

        # If this is a group end block, then break out of the loop.  If this end block was encountered in root, then
        # something went wrong and throw an error
        if group_end:
            if level == 0:
                raise ValueError("Encountered \"group end\" block in GDF file, but we were not inside of a group")
            else:
                break

        # Figure out the value.  First, branch based on single value vs array.  For some reason it looks like the GDF
        # standard has a separate flag for each, but I think setting both to True or both to False gives an invalid
        # state which we will throw an error on.  This is based on reverse engineering, however, and so there could be
        # a real use case for these instances which will need to be added later.
        dtype = block_type_flag & GDF_DTYPE
        single = bool(block_type_flag & GDF_SINGLE)
        array = bool(block_type_flag & GDF_ARRAY)
        if single and not array:
            # If we can use struct to convert the type
            if dtype in GDF_DTYPES_STRUCT:
                # Confirm that the size is what we expect
                if block_size != GDF_DTYPES_STRUCT[dtype][1]:
                    raise ValueError("Potentially bad block size (expected {:d} bytes, got {:d} bytes)".format(
                        GDF_DTYPES_STRUCT[dtype][1], block_size))

                # Pull the data from the file and convert to the parameter
                block["value"], = struct.unpack(GDF_DTYPES_STRUCT[dtype][0], f.read(block_size))

            # If it is a string, pull it out and decode
            elif dtype == GDF_ASCII:
                block["value"] = f.read(block_size).split(b'\0', 1)[0].decode('ascii')

            # If it is null, put a None object and fast forward through the file by the block size
            elif dtype == GDF_NULL:
                block["value"] = None
                f.seek(block_size, 1)  # Second parameter of 1 means seek relative to current position

            # If it was an undefined data type, then take the raw bytes object
            elif dtype == GDF_UNDEFINED:
                block["value"] = f.read(block_size)

            # If we didn't understand the data type, then throw an error
            else:
                raise TypeError("Unrecognized single parameter data type ID (ID number 0x{:x})".format(dtype))

        elif array and not single:
            # If we can find a compatible numpy type
            if dtype in GDF_DTYPES_NUMPY:
                # Confirm that the size is what we expect (array is even multiple of type size)
                if block_size % GDF_DTYPES_NUMPY[dtype][1] != 0:
                    raise ValueError("Potentially bad block size in array (expected multiple of {:d} bytes,"
                                     " got {:d} bytes)".format(GDF_DTYPES_NUMPY[dtype][1], block_size))

                # Pull the data from the file and convert to the parameter
                block["value"] = np.fromfile(
                    f,
                    dtype=GDF_DTYPES_NUMPY[dtype][0],
                    count=block_size // GDF_DTYPES_NUMPY[dtype][1]
                )

            # If it is null, then I don't know how to interpret it as an array so through an error
            elif dtype == GDF_NULL:
                raise TypeError("Cannot interpret array block parameter with null data type")

            # If it was an undefined data type, then take the raw bytes object
            elif dtype == GDF_UNDEFINED:
                block["value"] = f.read(block_size)

            # If we didn't understand the data type, then throw an error
            else:
                raise TypeError("Unrecognized array parameter data type ID (ID number {:d})".format(dtype))

        # Something went wrong (single and array are both true or both false)
        else:
            raise ValueError("invalid block flags (\"single\" = {0}, \"array\" = {1})".format(single, array))

        # If we have children then recurse to get them
        if group_begin:
            block["children"] = load_blocks(
                f,
                level=level + 1,
                max_recurse=max_recurse,
                max_block=max_block
            )

        # Add this block to the list
        blocks.append(block)

    # Return the list of blocks when we are done
    return blocks


def load(f, max_recurse=16, max_block=1e6):
    """
    All data in GDF file is loaded into python dictionary.  Dict will have the following keys which include the data
    blocks as well as information from the file's header.
     * creation_time: datetime object
     * creator: string
     * destination: string
     * gdf_version: tuple (int, int)
     * creator_version: tuple (int, int)
     * destination_version: tuple (int, int)
     * dummy: tuple (int, int)
     * blocks: list of block dictionaries (see following description)

    The main section of the file shows up in "blocks" which is a list of each hierarchical name-value pair.  Blocks are
    returned as python dicts with the keys: name, value, children.  The contents of "children" is itself a list of
    blocks with the same format.  Array values in the GDF file are populated into numpy arrays of the correct data type.

    :param f: filename or open file/stream-like object
    :param max_recurse: Maximum recursion depth while loading blocks in GDF file
    :param max_block: Maximum number of blocks allowed in each GDF group
    :return: dict of GDF data (see description)
    """
    # If we were handed a string, then run this function on it with the file opened
    if isinstance(f, str):
        with open(f, "rb") as ff:
            return load(ff, max_recurse=max_recurse, max_block=max_block)

    # Make sure we have got a GDF file opened in binary mode
    if not isinstance(f, io.BufferedReader):
        raise GDFIOError(f"f must be file-like or a string not '{type(f)}'")

    f.read(1)  # Trigger any IO errors here
    if not is_gdf(f):
        raise GDFIOError("Input is not a GDF file")

    # Read the GDF file header
    f.seek(0)
    fh_raw = struct.unpack("2i{0}s{0}s8B".format(GDF_NAME_LEN), f.read(48))
    ret = {
        "creation_time": datetime.datetime.fromtimestamp(fh_raw[1], tz=datetime.timezone.utc),
        "creator": fh_raw[2].split(b'\0', 1)[0].decode('ascii'),
        "destination": fh_raw[3].split(b'\0', 1)[0].decode('ascii'),
        "gdf_version": (fh_raw[4], fh_raw[5]),
        "creator_version": (fh_raw[6], fh_raw[7]),
        "destination_version": (fh_raw[8], fh_raw[9]),
        "dummy": (fh_raw[10], fh_raw[11])
    }

    # If the GDF version is too new, then give a warning
    v = ret["gdf_version"]
    if v[0] != 1 or v[1] != 1:
        warnings.warn("Attempting to open GDF v{:d}.{:d} file. easygdf has only been tested on GDF v1.1 files. "
                      "Please report any issues to project maintainer at contact@chris-pierce.com".format(v[0], v[1]))

    # Load all the groups and return
    ret["blocks"] = load_blocks(f, max_recurse=max_recurse, max_block=max_block)
    return ret


def save_blocks(f, blocks, level=0, max_recurse=16):
    """
    Internal function which is recursively called to save all hierarchical blocks

    :param f: filename or open file/stream-like object
    :param blocks: List of blocks which are being saved
    :param level: Tracks the level of recursion as the function is run.  Don't mess with it if calling externally.
    :param max_recurse: Maximum level of recursion before easyGDF will throw an error
    :return: None
    """
    # Check that blocks is really a list
    if not isinstance(blocks, list):
        raise TypeError("Blocks must be a list, not a \"{0}\"".format(type(blocks)))

    # If we have hit the max recursion depth throw an error
    if level >= max_recurse:
        raise RecursionError("Max GDF depth of recursion (currently set to {:d}) exceeded".format(max_recurse))

    # Iterate over each block
    for user_block in blocks:
        # Make an empty block with defaults
        block = {
            "name": "",
            "value": None,
            "children": [],
        }

        # Apply user defined parts of block
        for key in user_block:
            # If the override isn't a valid part of the block, throw an error
            if key not in block:
                raise ValueError("Invalid key in user provided block: \"{:s}\"".format(key))

            # Check dtype when required
            if key == "name":
                if not isinstance(user_block[key], str):
                    raise TypeError("Block attribute \"name\" must be a string not "
                                    "\"{0}\"".format(type(user_block[key])))
            if key == "children":
                if not isinstance(user_block[key], list):
                    raise TypeError("Block attribute \"children\" must be a list not "
                                    "\"{0}\"".format(type(user_block[key])))

            # Override the header
            block[key] = user_block[key]

        # Set the initial value of the block flag header
        block_type_flag = 0

        # If we have children, then set the group start bit
        if len(block["children"]) != 0:
            block_type_flag += GDF_GROUP_BEGIN

        # Create the padded block name
        bname = struct.pack("{0}s".format(GDF_NAME_LEN), bytes(block["name"], "ascii"))

        # If we are a numpy array then write it
        if isinstance(block["value"], np.ndarray):
            if block["value"].dtype == np.dtype('int64'):
                if (np.abs(block["value"]) > 0x7FFFFFFF).any():
                    idx = np.argmax(np.abs(block["value"]))
                    raise ValueError(f'An array element exceeds the range of int32 (max compatible GDF size).  The '
                                     f'element at index {idx} had value {block["value"]}, but int32s must have a max '
                                     f'absolute value of 2,147,483,647.')
                bval = block["value"].astype(np.int32)
            elif block["value"].dtype == np.dtype('uint64'):
                if (block["value"] > 0xFFFFFFFF).any():
                    idx = np.argmax(np.abs(block["value"]))
                    raise ValueError(f'An array element exceeds the range of uint32 (max compatible GDF size).  The '
                                     f'element at index {idx} had value {block["value"]}, but int32s must have a max '
                                     f'absolute value of 4,294,967,295.')
                bval = block["value"].astype(np.uint32)
            else:
                bval = block["value"]

            # Set the array bit in the header
            block_type_flag += GDF_ARRAY

            # Determine the data type and add it to the header
            dname = bval.dtype.name
            if dname not in NUMPY_TO_GDF:
                raise TypeError("Cannot write numpy data type \"{0}\" to GDF file".format(dname))
            block_type_flag += NUMPY_TO_GDF[dname]

            # Write the header and then write the numpy array to the file
            block_size = bval.size * bval.itemsize
            f.write(bname + struct.pack("ii", block_type_flag, block_size))
            bval.tofile(f)

        # If we aren't an array then we are a single value
        else:
            # Set the flag
            block_type_flag += GDF_SINGLE

            # Separate out writing based on data type
            if isinstance(block["value"], str):
                block_type_flag += GDF_ASCII
                block_size = len(block["value"])
                f.write(bname + struct.pack("ii{:d}s".format(block_size), block_type_flag, block_size,
                                            bytes(block["value"], "ascii")))
            elif isinstance(block["value"], int):
                if block["value"] > 0:
                    if abs(block["value"]) > 0xFFFFFFFF:
                        raise ValueError(f"Value exceeds range of 32-bit unsigned int (largest supported size in GDF). "
                                         f"Value cannot exceed 4,294,967,295.  Received {block['value']}")
                    block_type_flag += GDF_UINT32
                    block_size = 4
                    f.write(bname + struct.pack("iiI", block_type_flag, block_size, block["value"]))
                else:
                    if abs(block["value"]) > 0x7FFFFFFF:
                        raise ValueError(f"Value exceeds range of 32-bit signed int (largest supported size in GDF). "
                                         f"Absolute value cannot exceed 2,147,483,647.  Received {block['value']}")
                    block_type_flag += GDF_INT32
                    block_size = 4
                    f.write(bname + struct.pack("iii", block_type_flag, block_size, block["value"]))
            elif isinstance(block["value"], float):
                block_type_flag += GDF_DOUBLE
                block_size = 8
                f.write(bname + struct.pack("iid", block_type_flag, block_size, block["value"]))
            elif block["value"] is None:
                block_type_flag += GDF_NULL
                block_size = 0
                f.write(bname + struct.pack("ii", block_type_flag, block_size))
            else:
                raise TypeError("Cannot write data type \"{0}\" to GDF file".format(type(block["value"])))

        # Recurse on the children of this block
        if len(block["children"]) != 0:
            save_blocks(
                f,
                block["children"],
                level=level + 1,
                max_recurse=max_recurse
            )

    # If we are not the root group, then write a group end block
    if level > 0:
        f.write(struct.pack("{0}sii".format(GDF_NAME_LEN), b"", GDF_NULL + GDF_GROUP_END, 0))


def save(f, blocks=None, creation_time=None, creator="easygdf", destination="", gdf_version=(1, 1),
         creator_version=(2, 0), destination_version=(0, 0), dummy=(0, 0), max_recurse=16):
    """
    Saves user provided data into a GDF file.  Blocks are python dicts with the keys: name, value, children.  Name must
    be a string that may be encoded as ASCII.  Values may be an int, a float, a string, None, a bytes object, or a numpy
    array.  Most numpy data types are supported with the exception of complex types.  The contents of "children" is
    itself a list of blocks with the same format.

    Function signature is fully compatible with load function to simplify the following example of editing a GDF file:

    >>> import easygdf
    >>> d = easygdf.load("your_file.gdf")
    >>> # Modify the data in "d" here
    >>> easygdf.save("modified_file.gdf", **d)

    :param f: filename or open file/stream-like object
    :param blocks: List of GDF blocks to be saved (see description)
    :param creation_time: int/datetime object creation time written to header (default: time when file is written)
    :param creator: string written to header
    :param destination: string written to header
    :param gdf_version: tuple (int, int) written to header.  (Don't change unless you like messing with low-level stuff)
    :param creator_version: tuple (int, int) written to header
    :param destination_version: tuple (int, int) written to header
    :param dummy: tuple (int, int) written to header
    :param max_recurse: Maximum recursion depth while saving blocks in GDF file
    :return: None
    """
    # Fix for mutable default argument
    if blocks is None:
        blocks = []

    # If we were handed a string, then run this function on it with the file opened
    if isinstance(f, str):
        with open(f, "wb") as ff:
            return save(
                ff,
                blocks=blocks,
                creation_time=creation_time,
                creator=creator, destination=destination,
                gdf_version=gdf_version,
                creator_version=creator_version,
                destination_version=destination_version,
                dummy=dummy,
                max_recurse=max_recurse
            )

    # Make sure we have an open file
    if not isinstance(f, io.BufferedWriter):
        raise GDFIOError(f"f must be file-like or a string not '{type(f)}'")

    # If not given user defined creation time, then take current date
    if creation_time is None:
        creation_time = datetime.datetime.now()

    # If the time is a datetime object (not an int), then convert
    if isinstance(creation_time, datetime.datetime):
        creation_time = int(datetime.datetime.timestamp(creation_time))

    # Write the header
    f.write(struct.pack(
        "2i{0}s{0}s8B".format(GDF_NAME_LEN),
        GDF_MAGIC,
        creation_time,
        bytes(creator, "ascii"),
        bytes(destination, "ascii"),
        gdf_version[0],
        gdf_version[1],
        creator_version[0],
        creator_version[1],
        destination_version[0],
        destination_version[1],
        dummy[0],
        dummy[1],
    ))

    # Save the root group and then recurse (inside function)
    save_blocks(f, blocks, max_recurse=max_recurse)
