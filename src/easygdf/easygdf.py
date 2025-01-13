import datetime
import io
import logging
import numpy as np
import struct
import time
import warnings

from .utils import is_gdf
from .exceptions import GDFIOError
from .constants import (
    GDF_NAME_LEN,
    GDF_MAGIC,
    GDF_ASCII,
    GDF_DOUBLE,
    GDF_INT32,
    GDF_NULL,
    GDF_UINT32,
    GDF_UNDEFINED,
    GDF_DTYPES_STRUCT,
    GDF_DTYPES_NUMPY,
    NUMPY_TO_GDF,
    GDF_DTYPE,
    GDF_GROUP_BEGIN,
    GDF_GROUP_END,
    GDF_SINGLE,
    GDF_ARRAY,
)

logger = logging.getLogger(__name__)


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
    # Track statistics for logging
    total_bytes_read = 0
    block_count = 0

    # If we have hit the max recursion depth throw an error
    if level >= max_recurse:
        err_msg = f"Max GDF depth of recursion (set to {max_recurse}) exceeded at level {level}"
        logger.error(err_msg)
        raise RecursionError(err_msg)

    # Make a place for the blocks
    blocks = []

    # Loop over the blocks
    for _ in range(int(max_block)):
        block_start_time = time.perf_counter()

        # Read the block's header
        header_raw = f.read(GDF_NAME_LEN + 8)
        total_bytes_read += len(header_raw)

        # If no data came back and we are in the root group, then break.  If this isn't root group, then something
        # went wrong.
        if header_raw == b"":
            if level == 0:
                break
            else:
                err_msg = "File ended in middle of GDF group"
                logger.error(err_msg)
                raise IOError(err_msg)

        # Unpack the header
        block_name, block_type_flag, block_size = struct.unpack("{0}sii".format(GDF_NAME_LEN), header_raw)
        block_name = block_name.split(b"\0", 1)[0].decode("ascii")

        # Make a new empty block with the correct name
        block = {"name": block_name, "value": None, "children": []}

        # Break up the type flag into group operations and throw an error if invalid
        group_begin = bool(block_type_flag & GDF_GROUP_BEGIN)
        group_end = bool(block_type_flag & GDF_GROUP_END)
        if group_begin and group_end:
            err_msg = f"Invalid group flags in block '{block_name}': begin={group_begin}, end={group_end}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        # If this is a group end block, then break out of the loop.  If this end block was encountered in root, then
        # something went wrong and throw an error
        if group_end:
            if level == 0:
                err_msg = 'Encountered "group end" block in GDF file root level'
                logger.error(err_msg)
                raise ValueError(err_msg)
            else:
                break

        # Figure out the value.  First, branch based on single value vs array.  For some reason it looks like the GDF
        # standard has a separate flag for each, but I think setting both to True or both to False gives an invalid
        # state which we will throw an error on.  This is based on reverse engineering, however, and so there could be
        # a real use case for these instances which will need to be added later.
        dtype = block_type_flag & GDF_DTYPE
        single = bool(block_type_flag & GDF_SINGLE)
        array = bool(block_type_flag & GDF_ARRAY)

        value_type = None
        value_info = ""

        if single and not array:
            # If we can use struct to convert the type
            if dtype in GDF_DTYPES_STRUCT:
                if block_size != GDF_DTYPES_STRUCT[dtype][1]:
                    err_msg = f"Block size mismatch for '{block_name}': expected {GDF_DTYPES_STRUCT[dtype][1]} bytes, got {block_size} bytes"
                    logger.error(err_msg)
                    raise ValueError(err_msg)

                data = f.read(block_size)
                total_bytes_read += block_size
                (block["value"],) = struct.unpack(GDF_DTYPES_STRUCT[dtype][0], data)
                value_type = "struct"

            # If it is a string, pull it out and decode
            elif dtype == GDF_ASCII:
                data = f.read(block_size)
                total_bytes_read += block_size
                block["value"] = data.split(b"\0", 1)[0].decode("ascii")
                value_type = "ASCII"

            # If it is null, put a None object and fast forward through the file by the block size
            elif dtype == GDF_NULL:
                block["value"] = None
                f.seek(block_size, 1)  # Second parameter of 1 means seek relative to current position
                total_bytes_read += block_size
                value_type = "null"
                value_info = f"skip={block_size}"

            # If it was an undefined data type, then take the raw bytes object
            elif dtype == GDF_UNDEFINED:
                block["value"] = f.read(block_size)
                total_bytes_read += block_size
                value_type = "undefined"

            # If we didn't understand the data type, then throw an error
            else:
                err_msg = f"Unrecognized single parameter data type ID (0x{dtype:x})"
                logger.error(err_msg)
                raise TypeError(err_msg)

        elif array and not single:
            # If we can find a compatible numpy type
            if dtype in GDF_DTYPES_NUMPY:
                if block_size % GDF_DTYPES_NUMPY[dtype][1] != 0:
                    err_msg = f"Invalid array block size for '{block_name}': {block_size} bytes is not multiple of element size {GDF_DTYPES_NUMPY[dtype][1]}"
                    logger.error(err_msg)
                    raise ValueError(err_msg)

                block["value"] = np.fromfile(
                    f, dtype=GDF_DTYPES_NUMPY[dtype][0], count=block_size // GDF_DTYPES_NUMPY[dtype][1]
                )
                total_bytes_read += block_size
                value_type = "numpy"
                value_info = f"type={GDF_DTYPES_NUMPY[dtype][0]}, elements={len(block['value'])}"

            # If it is null, then I don't know how to interpret it as an array so throw an error
            elif dtype == GDF_NULL:
                err_msg = "Cannot interpret array block parameter with null data type"
                logger.error(err_msg)
                raise TypeError(err_msg)

            # If it was an undefined data type, then take the raw bytes object
            elif dtype == GDF_UNDEFINED:
                block["value"] = f.read(block_size)
                total_bytes_read += block_size
                value_type = "undefined array"

            # If we didn't understand the data type, then throw an error
            else:
                err_msg = f"Unrecognized array parameter data type ID (0x{dtype:x})"
                logger.error(err_msg)
                raise TypeError(err_msg)

        # Something went wrong (single and array are both true or both false)
        else:
            err_msg = f"Invalid block flags for '{block_name}': single={single}, array={array}"
            logger.error(err_msg)
            raise ValueError(err_msg)

        block_time = time.perf_counter() - block_start_time

        # Handle flags
        flags = []
        if group_begin:
            flags.append("Group")
        if array:
            flags.append("Array")
        if single:
            flags.append("Single")
        flags = ", ".join(flags)

        # Log this block
        if value_info:
            value_info = value_info + ", "
        logger.debug(
            f'Read block at level {level}, index {block_count} "{block_name}" in {1e3*block_time:.3f} ms'
            f" (type=0x{dtype:x} ({value_type}), size={block_size} bytes, {value_info}flags=[{flags}])"
        )

        # If we have children then recurse to get them
        if group_begin:
            block["children"] = load_blocks(f, level=level + 1, max_recurse=max_recurse, max_block=max_block)

        # Add this block to the list
        blocks.append(block)
        block_count += 1

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
    start_time = time.perf_counter()

    # If we were handed a string, then run this function on it with the file opened
    if isinstance(f, str):
        logger.debug(f"Opening file: {f}")
        with open(f, "rb") as ff:
            return load(ff, max_recurse=max_recurse, max_block=max_block)

    # Make sure we have got a GDF file opened in binary mode
    if not isinstance(f, io.BufferedReader):
        err_msg = f"f must be file-like or a string not '{type(f)}'"
        logger.error(err_msg)
        raise GDFIOError(err_msg)

    try:
        f.read(1)  # Trigger any IO errors here
    except IOError as e:
        logger.error(f"Failed to read file: {str(e)}")
        raise

    if not is_gdf(f):
        err_msg = "Input is not a GDF file"
        logger.error(err_msg)
        raise GDFIOError(err_msg)

    # Read the GDF file header
    header_start = time.perf_counter()
    f.seek(0)
    fh_raw = struct.unpack("2i{0}s{0}s8B".format(GDF_NAME_LEN), f.read(48))
    ret = {
        "creation_time": datetime.datetime.fromtimestamp(fh_raw[1], tz=datetime.timezone.utc),
        "creator": fh_raw[2].split(b"\0", 1)[0].decode("ascii"),
        "destination": fh_raw[3].split(b"\0", 1)[0].decode("ascii"),
        "gdf_version": (fh_raw[4], fh_raw[5]),
        "creator_version": (fh_raw[6], fh_raw[7]),
        "destination_version": (fh_raw[8], fh_raw[9]),
        "dummy": (fh_raw[10], fh_raw[11]),
    }
    header_time = time.perf_counter() - header_start

    logger.debug(
        f"GDF header loaded time={header_time:.3f}s gdf_version={ret['gdf_version']} "
        f"creator='{ret['creator']}' creator_version={ret['creation_time'].isoformat()}"
    )

    # If the GDF version is too new, then give a warning
    v = ret["gdf_version"]
    if v[0] != 1 or v[1] != 1:
        warning_msg = (
            f"Attempting to open GDF v{v[0]}.{v[1]} file. easygdf has only been tested on GDF v1.1 files. "
            "Please report any issues to project maintainer at contact@chris-pierce.com"
        )
        logger.warning(warning_msg)
        warnings.warn(warning_msg)

    # Load all the groups and return
    ret["blocks"] = load_blocks(f, max_recurse=max_recurse, max_block=max_block)
    total_time = time.perf_counter() - start_time

    logger.info(
        f"Loaded GDF file in {1e3*total_time:.3f} ms (root_blocks={len(ret['blocks'])}, file_version={v[0]}.{v[1]})"
    )
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
    # Track statistics for logging
    total_bytes_written = 0
    block_count = 0

    # Check that blocks is really a list
    if not isinstance(blocks, list):
        err_msg = f'Blocks must be a list, not a "{type(blocks)}"'
        logger.error(err_msg)
        raise TypeError(err_msg)

    # If we have hit the max recursion depth throw an error
    if level >= max_recurse:
        err_msg = f"Max GDF depth of recursion (currently set to {max_recurse}) exceeded at level {level}"
        logger.error(err_msg)
        raise RecursionError(err_msg)

    # Iterate over each block
    for user_block in blocks:
        block_start_time = time.perf_counter()

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
                err_msg = f'Invalid key in user provided block: "{key}"'
                logger.error(err_msg)
                raise ValueError(err_msg)

            # Check dtype when required
            if key == "name" and not isinstance(user_block[key], str):
                err_msg = f'Block attribute "name" must be a string not "{type(user_block[key])}"'
                logger.error(err_msg)
                raise TypeError(err_msg)
            if key == "children" and not isinstance(user_block[key], list):
                err_msg = f'Block attribute "children" must be a list not "{type(user_block[key])}"'
                logger.error(err_msg)
                raise TypeError(err_msg)

            # Override the header
            block[key] = user_block[key]

        # Track block metadata for logging
        value_type = None
        value_info = ""
        bytes_written = 0

        block_type_flag = 0

        # If we have children, then set the group start bit
        if len(block["children"]) != 0:
            block_type_flag += GDF_GROUP_BEGIN

        # Create the padded block name
        bname = struct.pack("{0}s".format(GDF_NAME_LEN), bytes(block["name"], "ascii"))

        # If we are a numpy array then write it
        if isinstance(block["value"], np.ndarray):
            if block["value"].dtype == np.dtype("int64"):
                if (np.abs(block["value"]) > 0x7FFFFFFF).any():
                    idx = np.argmax(np.abs(block["value"]))
                    err_msg = f'Array element at index {idx} exceeds int32 range: {block["value"][idx]}'
                    logger.error(err_msg)
                    raise ValueError(err_msg)
                bval = block["value"].astype(np.int32)
            elif block["value"].dtype == np.dtype("uint64"):
                if (block["value"] > 0xFFFFFFFF).any():
                    idx = np.argmax(np.abs(block["value"]))
                    err_msg = f'Array element at index {idx} exceeds uint32 range: {block["value"][idx]}'
                    logger.error(err_msg)
                    raise ValueError(err_msg)
                bval = block["value"].astype(np.uint32)
            else:
                bval = block["value"]

            block_type_flag += GDF_ARRAY
            dname = bval.dtype.name
            if dname not in NUMPY_TO_GDF:
                err_msg = f'Cannot write numpy data type "{dname}" to GDF file'
                logger.error(err_msg)
                raise TypeError(err_msg)

            block_type_flag += NUMPY_TO_GDF[dname]
            block_size = bval.size * bval.itemsize
            header = bname + struct.pack("ii", block_type_flag, block_size)
            f.write(header)
            bval.tofile(f)
            bytes_written = len(header) + block_size
            value_type = "numpy"
            value_info = f"type={dname}, elements={bval.size}"

        # If we aren't an array then we are a single value
        else:
            # Set the flag
            block_type_flag += GDF_SINGLE

            # Separate out writing based on data type
            if isinstance(block["value"], str):
                block_type_flag += GDF_ASCII
                block_size = len(block["value"])
                data = bname + struct.pack(
                    "ii{:d}s".format(block_size), block_type_flag, block_size, bytes(block["value"], "ascii")
                )
                f.write(data)
                bytes_written = len(data)
                value_type = "string"

            elif isinstance(block["value"], int):
                if block["value"] > 0:
                    if abs(block["value"]) > 0xFFFFFFFF:
                        err_msg = f"Value exceeds uint32 range: {block['value']}"
                        logger.error(err_msg)
                        raise ValueError(err_msg)
                    block_type_flag += GDF_UINT32
                    block_size = 4
                    data = bname + struct.pack("iiI", block_type_flag, block_size, block["value"])
                    value_type = "uint32"
                else:
                    if abs(block["value"]) > 0x7FFFFFFF:
                        err_msg = f"Value exceeds int32 range: {block['value']}"
                        logger.error(err_msg)
                        raise ValueError(err_msg)
                    block_type_flag += GDF_INT32
                    block_size = 4
                    data = bname + struct.pack("iii", block_type_flag, block_size, block["value"])
                    value_type = "int32"
                f.write(data)
                bytes_written = len(data)
                value_info = f"value={block['value']}"

            elif isinstance(block["value"], float):
                block_type_flag += GDF_DOUBLE
                block_size = 8
                data = bname + struct.pack("iid", block_type_flag, block_size, block["value"])
                f.write(data)
                bytes_written = len(data)
                value_type = "double"
                value_info = f"value={block['value']}"

            elif block["value"] is None:
                block_type_flag += GDF_NULL
                block_size = 0
                data = bname + struct.pack("ii", block_type_flag, block_size)
                f.write(data)
                bytes_written = len(data)
                value_type = "null"

            else:
                err_msg = f'Cannot write data type "{type(block["value"])}" to GDF file'
                logger.error(err_msg)
                raise TypeError(err_msg)

        block_time = time.perf_counter() - block_start_time

        # Handle flags
        flags = []
        if len(block["children"]):
            flags.append("Group")
        if isinstance(block["value"], np.ndarray):
            flags.append("Array")
        else:
            flags.append("Single")
        flags = ", ".join(flags)

        if value_info:
            value_info = value_info + ", "
        logger.debug(
            f"Wrote block at level {level}, index {block_count} \"{block['name']}\" in {1e3*block_time:.3f}ms "
            f"(type=0x{block_type_flag:x} ({value_type}), size={block_size} bytes, {value_info}flags=[{flags}])"
        )

        total_bytes_written += bytes_written
        block_count += 1

        # Recurse on the children of this block
        if len(block["children"]) != 0:
            child_bytes, child_blocks = save_blocks(f, block["children"], level=level + 1, max_recurse=max_recurse)
            total_bytes_written += child_bytes
            block_count += child_blocks

    # If we are not the root group, then write a group end block
    if level > 0:
        end_block = struct.pack("{0}sii".format(GDF_NAME_LEN), b"", GDF_NULL + GDF_GROUP_END, 0)
        f.write(end_block)
        total_bytes_written += len(end_block)

    return total_bytes_written, block_count


def save(
    f,
    blocks=None,
    creation_time=None,
    creator="easygdf",
    destination="",
    gdf_version=(1, 1),
    creator_version=(2, 0),
    destination_version=(0, 0),
    dummy=(0, 0),
    max_recurse=16,
):
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
    start_time = time.perf_counter()

    # Fix for mutable default argument
    if blocks is None:
        blocks = []

    # If we were handed a string, then run this function on it with the file opened
    if isinstance(f, str):
        logger.debug(f"Opening file for writing: {f}")
        with open(f, "wb") as ff:
            return save(
                ff,
                blocks=blocks,
                creation_time=creation_time,
                creator=creator,
                destination=destination,
                gdf_version=gdf_version,
                creator_version=creator_version,
                destination_version=destination_version,
                dummy=dummy,
                max_recurse=max_recurse,
            )

    # Make sure we have an open file
    if not isinstance(f, io.BufferedWriter):
        err_msg = f"f must be file-like or a string not '{type(f)}'"
        logger.error(err_msg)
        raise GDFIOError(err_msg)

    # If not given user defined creation time, then take current date
    if creation_time is None:
        creation_time = datetime.datetime.now()

    # If the time is a datetime object (not an int), then convert
    if isinstance(creation_time, datetime.datetime):
        creation_time = int(datetime.datetime.timestamp(creation_time))

    # Write the header
    header = struct.pack(
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
    )
    f.write(header)
    total_bytes = len(header)
    logger.debug(
        f"Wrote GDF header ({total_bytes} bytes): version={gdf_version[0]}.{gdf_version[1]} creator='{creator}'"
    )

    # Save the root group and then recurse (inside function)
    block_bytes, total_blocks = save_blocks(f, blocks, max_recurse=max_recurse)
    total_time = time.perf_counter() - start_time
    total_bytes += block_bytes

    logger.info(
        f"Saved GDF file in {1e3*total_time:.3f} ms (root_blocks={len(blocks)}, total_blocks={total_blocks}, bytes_written={total_bytes})"
    )
