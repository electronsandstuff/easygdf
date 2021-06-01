#  This file is part of easygdf and is released under the BSD 3-clause license

import numpy as np

from . import easygdf


def normalize_screen(screen):
    """
    Accepts an incomplete screen object and returns a version with correctly sized arrays and validation of redundant
    objects.

    :param screen: Dictionary with potentially incomplete or invalid screen data
    :return: Completed screen data
    """
    # Make an output screen
    out = {}

    # Write out the list of keys to create array objects from (Warning: G and rxy need to go at end)
    arr_keys = ['ID', 'x', 'y', 'z', 'Bx', 'By', 'Bz', 't', 'm', 'q', 'nmacro', 'rmacro', 'rxy', 'G']

    # Handle the position element
    if "position" not in screen:
        out["position"] = 0.0
    else:
        out["position"] = screen["position"]

    # Fix array lengths
    target_len = max([screen[x].size for x in arr_keys if x in screen], default=0)
    for key in arr_keys:
        if key in screen:
            if screen[key].size != target_len:
                raise ValueError("All screen elements must be the same length")
            else:
                out[key] = screen[key]
        else:
            # Handle special default values
            if key == "ID":
                out[key] = np.linspace(0, target_len - 1, target_len)
            elif key == "G":
                out[key] = 1 / np.sqrt(1 - (out["Bx"] ** 2 + out["By"] ** 2 + out["Bz"] ** 2))
            elif key == "rxy":
                out[key] = np.sqrt(out["x"] ** 2 + out["y"] ** 2)
            else:
                out[key] = np.zeros((target_len,))

    # Add auxiliary keys to the dict
    for key in screen:
        if key not in out:
            out[key] = screen[key]

    return out


def normalize_tout(tout):
    """
    Takes a user provided dictionary with tout data and completes it returning a valid object to be output to GDF

    :param tout: User provided dictionary with tout data.  May be invalid or incomplete.
    :return: The completed tout data as a dictionary
    """
    # Make an output tout
    out = {}

    # Write out the list of array keys (Warning: G and rxy need to be at end of array)
    par_keys = ['x', 'y', 'z', 'Bx', 'By', 'Bz', 'm', 'q', 'nmacro', 'rmacro', 'ID', 'fEx', 'fEy', 'fEz',
                'fBx', 'fBy', 'fBz', 'G', 'rxy']
    scat_keys = ['scat_x', 'scat_y', 'scat_z', 'scat_Qin', 'scat_Qout', 'scat_Qnet', 'scat_Ein', 'scat_Eout',
                 'scat_Enet', 'scat_inp']

    # Handle the time element
    if "time" not in tout:
        out["time"] = 0.0
    else:
        out["time"] = tout["time"]

    # Handle particle arrays
    target_len = max([tout[x].size for x in tout if x in par_keys], default=0)
    for key in par_keys:
        if key in tout:
            if tout[key].size != target_len:
                raise ValueError("All tout elements must be the same length")

            # Add the object to the array
            out[key] = tout[key]
        else:
            # Handle special default values
            if key == "ID":
                out[key] = np.linspace(0, target_len - 1, target_len)
            elif key == "G":
                out[key] = 1 / np.sqrt(1 - (out["Bx"] ** 2 + out["By"] ** 2 + out["Bz"] ** 2))
            elif key == "rxy":
                out[key] = np.sqrt(out["x"] ** 2 + out["y"] ** 2)
            else:
                out[key] = np.zeros((target_len,))

    # Handle scatter arrays
    target_len = max([tout[x].size for x in tout if x in scat_keys], default=0)
    for key in scat_keys:
        if key in tout:
            if tout[key].size != target_len:
                raise ValueError("All tout elements must be the same length")
            else:
                out[key] = tout[key]
        else:
            out[key] = np.zeros((target_len,))

    # Add auxiliary keys to the dict
    for key in tout:
        if key not in out:
            out[key] = tout[key]

    return out


def save_screens_touts(f, screens=None, touts=None, logo="B&M-General Particle Tracer", scat_x=np.array([]),
                       scat_y=np.array([]), scat_z=np.array([]), scat_Qin=np.array([]),
                       scat_Qout=np.array([]), scat_Qnet=np.array([]), scat_Ein=np.array([]),
                       scat_Eout=np.array([]), scat_Enet=np.array([]), scat_inp=np.array([]), numderivs=0,
                       cputime=0.0, creation_time=None, creator="easygdf", destination="", gdf_version=(1, 1),
                       creator_version=(2, 0), destination_version=(0, 0), dummy=(0, 0), max_recurse=16):
    """
    Saves user data into a file with the format of a GPT output.  Signature is fully compatible with the output of the
    corresponding load function.  Screens and touts are passed as a list of dicts with the following numpy arrays.

    particle keys in tout: 'x', 'y', 'z', 'Bx', 'By', 'Bz', 'm', 'q', 'nmacro', 'rmacro', 'ID', 'fEx', 'fEy', 'fEz',
    'fBx', 'fBy', 'fBz', 'G', 'rxy'

    scatter keys in tout: 'scat_x', 'scat_y', 'scat_z', 'scat_Qin', 'scat_Qout', 'scat_Qnet', 'scat_Ein', 'scat_Eout',
    'scat_Enet', 'scat_inp'

    particle keys in screen: 'ID', 'x', 'y', 'z', 'Bx', 'By', 'Bz', 't', 'm', 'q', 'nmacro', 'rmacro', 'rxy', 'G'

    Arrays don't need to be set in the dict if unused.  The missing keys will be automatically filled in with zeros to
    the correct length.  In the case of redundant keys (such as "rxy", "G", or "ID") values are computed from provided
    data.  Scatter keys and particle keys in tout are handled separately in filling out array lengths (IE: if "x" was
    set to an array of length 10, then "y" would be padded to that length in the output, but "scat_x" would remain
    empty).  Any auxiliary keys in the dict will be saved to the screen/tout.

    In addition to array elements, screen may contain the scalar "position" and tout can have the scalar "time" which
    will be used as parameters for the groups.  Defaults are zero for each.

    :param f: filename or open file/stream-like object
    :param screens: list of screen dicts
    :param touts: list of tout dicts
    :param logo: string
    :param scat_x: numpy array
    :param scat_y: numpy array
    :param scat_z: numpy array
    :param scat_Qin: numpy array
    :param scat_Qout: numpy array
    :param scat_Qnet: numpy array
    :param scat_Ein: numpy array
    :param scat_Eout: numpy array
    :param scat_Enet: numpy array
    :param scat_inp: numpy array
    :param numderivs: int
    :param cputime: float
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
    # Deal with mutable arguments
    if touts is None:
        touts = []
    if screens is None:
        screens = []

    # Deal with the array arguments which must have the same dimensions
    arr_elems = {
        "scat_x": scat_x, "scat_y": scat_y, "scat_z": scat_z, "scat_Qin": scat_Qin, "scat_Qout": scat_Qout,
        "scat_Qnet": scat_Qnet, "scat_Ein": scat_Ein, "scat_Eout": scat_Eout, "scat_Enet": scat_Enet,
        "scat_inp": scat_inp
    }
    target_len = max([arr_elems[x].size for x in arr_elems])
    for key in arr_elems:
        if arr_elems[key].size == 0:
            arr_elems[key] = np.zeros((target_len,))
        elif arr_elems[key].size == target_len:
            pass
        else:
            raise ValueError("All scatter elements in screen/tout save must have same length")

    # Make a place to store our blocks
    blocks = [
        {"name": "@logo", "value": logo},
        {"name": "numderivs", "value": numderivs},
        {"name": "cputime", "value": cputime}
    ]

    # Add all root elements to the blocks
    for key in arr_elems:
        blocks.append({"name": key, "value": arr_elems[key]})

    # Go through each screen
    for screen in screens:
        # Normalize the user provided screen
        nscreen = normalize_screen(screen)

        # Create the block
        pos = nscreen.pop("position")
        blocks.append({"name": "position",
                       "value": pos,
                       "children": [{"name": x, "value": nscreen[x]} for x in nscreen]})

    # Go through each tout and add them
    for tout in touts:
        # Normalize the user provided screen
        ntout = normalize_tout(tout)

        # Create the block
        time = ntout.pop("time")
        blocks.append({"name": "time",
                       "value": time,
                       "children": [{"name": x, "value": ntout[x]} for x in ntout]})

    # Write the blocks to disk
    easygdf.save(f, blocks, creation_time=creation_time, creator=creator, destination=destination,
                 gdf_version=gdf_version, creator_version=creator_version, destination_version=destination_version,
                 dummy=dummy, max_recurse=max_recurse)


def load_screens_touts(f, max_recurse=16, max_block=1e6):
    """
    Loads screens and touts from a GDF file and returns them in a more friendly dictionary.  Screens are in the list
    "screens" and touts in the corresponding list "touts".  Root level parameters and header objects are returned in
    the root of the dictionary.

    :param f: filename or open file/stream-like object
    :param max_recurse: Maximum recursion depth while loading blocks in GDF file
    :param max_block: Maximum number of blocks allowed in each GDF group
    :return: dictionary with screens/touts and root level data
    """
    # Load the file using easygdf
    d = easygdf.load(f, max_recurse=max_recurse, max_block=max_block)

    # Create an empty set of screns/touts
    screens_touts = {"screens": [], "touts": []}

    # Dict to convert between the block names and what we use in the dictionary
    conv = {"time": ("touts", normalize_tout), "position": ("screens", normalize_screen)}

    # Go through each block
    for b in d.pop("blocks"):
        # If it's a screen or tout, extract the children and add it
        if b["name"] in conv:
            # Dump all the children into the group
            group = {}
            for c in b["children"]:
                group[c["name"]] = c["value"]

            # Add in the parameter
            group[b["name"]] = b["value"]

            # Add to the touts or screens
            screens_touts[conv[b["name"]][0]].append(conv[b["name"]][1](group))

        # If it's an auxiliary block, add it to the root
        else:
            screens_touts[b["name"]] = b["value"]

    # Add material from the header into the screens/touts object
    screens_touts.update(d)

    # Fix "@logo" so that it is compatible with python arguments
    if "@logo" in screens_touts:
        screens_touts["logo"] = screens_touts.pop("@logo")

    # Return the screens and touts
    return screens_touts
