#  This file is part of easygdf and is released under the BSD 3-clause license

import numpy as np

from . import easygdf


def load_initial_distribution(f, max_recurse=16, max_block=1e6):
    """
    Loads GPT initial distribution file into dict.  All arrays are loaded directly into the returned dict as well as the
    GDF header.

    :param f: filename or open file/stream-like object
    :param max_recurse: Maximum recursion depth while loading blocks in GDF file
    :param max_block: Maximum number of blocks allowed in each GDF group
    :return: dict of initial distribution data
    """
    # Load the file using easygdf
    d = easygdf.load(f, max_recurse=max_recurse, max_block=max_block)

    # Add in all of the blocks in the root group
    out = {}
    for b in d.pop("blocks"):
        out[b["name"]] = b["value"]

        # If there wer children, then maybe this isn't an initial dist file
        if len(b["children"]) > 0:
            raise ValueError("Found block with children.  Is this really an initial distribution file?")

    # Add in the header information
    out.update(d)

    # Return it
    return out


def save_initial_distribution(f, x=None, y=None, z=None, GBx=None, GBy=None, GBz=None, Bx=None, By=None, Bz=None,
                              t=None, G=None, m=None, q=None, nmacro=None, rmacro=None, creation_time=None,
                              creator="easygdf", destination="", gdf_version=(1, 1), creator_version=(2, 0),
                              destination_version=(0, 0), dummy=(0, 0), max_recurse=16):
    """
    Saves GPT compatible initial distribution file.  All array objects must be the same length (IE the number of
    particles).  If required values (either {x,y,z,GBx,GBy,GBz} or {x,y,z,Bx,By,Bz}) are missing, easyGDF will autofill
    them with zeros.  Only specify the momentum or the velocity of particles, not both.

    :param f: filename or open file/stream-like object
    :param x: numpy array, particle position
    :param y:numpy array, particle position
    :param z:numpy array, particle position
    :param GBx:numpy array, particle momentum
    :param GBy:numpy array, particle momentum
    :param GBz:numpy array, particle momentum
    :param Bx:numpy array, particle velocity
    :param By:numpy array, particle velocity
    :param Bz:numpy array, particle velocity
    :param t:numpy array, particle spawn time
    :param G:numpy array, Lorentz factor
    :param m:numpy array, particle mass
    :param q:numpy array, particle charge
    :param nmacro:numpy array, number of macroparticles
    :param rmacro:numpy array, macroparticle size
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
    # Copy all array elements into dict for processing and get rid of Nones
    data_raw = {"x": x, "y": y, "z": z, "GBx": GBx, "GBy": GBy, "GBz": GBz, "Bx": Bx, "By": By, "Bz": Bz, "t": t,
                "G": G, "m": m, "q": q, "nmacro": nmacro, "rmacro": rmacro}
    data = {x: data_raw[x] for x in data_raw if data_raw[x] is not None}

    # Check if user has specified momentum or velocity
    momentum = GBx is not None or GBy is not None or GBz is not None
    velocity = Bx is not None or By is not None or Bz is not None

    # Get required elements depending on this
    if (momentum and not velocity) or (not momentum and not velocity):
        required_arrays = ["x", "y", "z", "GBx", "GBy", "GBz"]

    elif velocity and not momentum:
        required_arrays = ["x", "y", "z", "Bx", "By", "Bz"]

    else:
        raise ValueError("Cannot specify both momentum (IE GBx) and velocity (IE Bx)")

    # Fill in any missing elements
    target_length = max([data[x].size for x in data], default=0)
    for arr in required_arrays:
        if arr in data:
            if data[arr].size != target_length:
                raise ValueError("All arrays must be same length")

        else:
            data[arr] = np.zeros((target_length,))

    # Turn the data into blocks
    blocks = [{"name": x, "value": data[x]} for x in data]

    # Save the blocks
    easygdf.save(f, blocks, creation_time=creation_time, creator=creator, destination=destination,
                 gdf_version=gdf_version, creator_version=creator_version, destination_version=destination_version,
                 dummy=dummy, max_recurse=max_recurse)
