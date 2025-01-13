#  This file is part of easygdf and is released under the BSD 3-clause license

import os
import numpy as np

import easygdf

########################################################################################################################
# Hardcoded inputs
########################################################################################################################
screen_tout_file = "/mnt/nfs/EasyGDF Stuff/0000_output.gdf"
initial_distribution_file = "/mnt/nfs/EasyGDF Stuff/0000_initial_distribution.gdf"
n_blocks = 1
n_particles = 5
data_files_path = "easygdf/tests/data"

########################################################################################################################
# Helper functions
########################################################################################################################
__logBase10of2 = 3.010299956639811952137388947244930267681898814621085413104274611e-1


def round_sigfigs(x, sigfigs):
    """
    Rounds the value(s) in x to the number of significant figures in sigfigs.
    Return value has the same type as x.

    Restrictions:
    sigfigs must be an integer type and store a positive value.
    x must be a real value or an array like object containing only real values.
    """
    if not (type(sigfigs) is int or isinstance(sigfigs, np.integer)):
        raise TypeError("RoundToSigFigs_fp: sigfigs must be an integer.")

    if sigfigs <= 0:
        raise ValueError("RoundToSigFigs_fp: sigfigs must be positive.")

    if not np.all(np.isreal(x)):
        raise TypeError("RoundToSigFigs_fp: all x must be real.")

    # temporarily suppres floating point errors
    errhanddict = np.geterr()
    np.seterr(all="ignore")

    matrixflag = False
    if isinstance(x, np.matrix):  # Convert matrices to arrays
        matrixflag = True
        x = np.asarray(x)

    xsgn = np.sign(x)
    absx = xsgn * x
    mantissas, binaryExponents = np.frexp(absx)

    decimalExponents = __logBase10of2 * binaryExponents
    omags = np.floor(decimalExponents)

    mantissas *= 10.0 ** (decimalExponents - omags)

    if type(mantissas) is float or isinstance(mantissas, np.floating):
        if mantissas < 1.0:
            mantissas *= 10.0
            omags -= 1.0

    else:  # elif np.all(np.isreal( mantissas )):
        fixmsk = (mantissas < 1.0,)
        mantissas[fixmsk] *= 10.0
        omags[fixmsk] -= 1.0

    result = xsgn * np.around(mantissas, decimals=sigfigs - 1) * 10.0**omags
    if matrixflag:
        result = np.matrix(result, copy=False)

    np.seterr(**errhanddict)
    return result


########################################################################################################################
# Script begins here
########################################################################################################################
def trim_screens_tout():
    # Load the screen/tout file
    with open(screen_tout_file, "rb") as f:
        d = easygdf.load(f)

    # Trim down the blocks
    trimmed_blocks = []
    seen_touts = 0
    seen_screens = 0
    for b in d["blocks"]:
        if b["name"] == "position":
            if seen_screens < n_blocks:
                trimmed_blocks.append(b)
                seen_screens += 1

        elif b["name"] == "time":
            if seen_touts < n_blocks:
                trimmed_blocks.append(b)
                seen_touts += 1

        else:
            trimmed_blocks.append(b)

    # Trim down the arrays to the correct number of particles
    particle_blocks = []
    for b in trimmed_blocks:
        new_block = {"name": b["name"], "param": b["param"], "children": []}
        for c in b["children"]:
            new_block["children"].append(
                {"name": c["name"], "param": round_sigfigs(c["param"][:n_particles], 4), "children": []}
            )
        particle_blocks.append(new_block)
    d["blocks"] = particle_blocks

    # Save the trimmed down blocks
    with open(os.path.join(data_files_path, "screens_touts.gdf"), "wb") as f:
        easygdf.save(f, **d)

    # Convert the blocks to the format we expect
    screens_touts = {"screens": [], "touts": []}
    conv = {"time": "touts", "position": "screens"}
    for b in particle_blocks:
        # If it's a screen or tout, extract the children and add it
        if b["name"] in conv:
            group = {}
            for c in b["children"]:
                group[c["name"]] = c["param"]
            group[b["name"]] = b["param"]
            screens_touts[conv[b["name"]]].append(group)

        # If it's an auxiliary block, add it to the root
        else:
            screens_touts[b["name"]] = b["param"]

    # Convert it to
    print(screens_touts)


def trim_initial_distribution():
    # Load the initial distribution file
    with open(initial_distribution_file, "rb") as f:
        d = easygdf.load(f)

    # Clip any arrays to the correct size
    trimmed_blocks = []
    for b in d["blocks"]:
        if isinstance(b["param"], np.ndarray):
            trimmed_blocks.append({"name": b["name"], "param": round_sigfigs(b["param"][:n_particles], 4)})
    d["blocks"] = trimmed_blocks

    # Save the file
    with open(os.path.join(data_files_path, "initial_distribution.gdf"), "wb") as f:
        easygdf.save(f, **d)

    # Create an example of the data structure we want
    ds = {x["name"]: x["param"] for x in d["blocks"]}
    d.pop("blocks")
    ds.update(d)
    print(ds)


if __name__ == "__main__":
    trim_screens_tout()
    trim_initial_distribution()
