from importlib.resources import files
import struct

from .constants import GDF_MAGIC


def get_example_screen_tout_filename():
    """
    Returns the path to an example screen/tout GDF file from easygdf.
    Used for testing and running demos of library.

    :return: Path to the example file
    """
    return str(files("easygdf").joinpath("data/screens_touts.gdf"))


def get_example_initial_distribution():
    """
    Returns the path to an example initial distribution GDF file from easygdf.
    Used for testing and running demos of library.

    :return: Path to the example file
    """
    return str(files("easygdf").joinpath("data/initial_distribution.gdf"))


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

    # Check if file has enough bytes to contain magic number
    if len(f.read(4)) != 4:
        return False

    # Rewind again to read the magic number
    f.seek(0)
    (magic_number,) = struct.unpack("i", f.read(4))
    return magic_number == GDF_MAGIC
