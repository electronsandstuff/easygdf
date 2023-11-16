#  This file is part of easygdf and is released under the BSD 3-clause license

import pkg_resources


def get_example_screen_tout_filename():
    """
    Unpacks an example of a screen/tout GDF file from easygdf and returns the path.  Used for testing and running demos
    of library.

    :return: Path to the example file
    """
    return pkg_resources.resource_filename("easygdf", "data/screens_touts.gdf")


def get_example_initial_distribution():
    """
    Unpacks an example of an initial distribution GDF file from easygdf and returns the path.  Used for testing and
    running demos of library.

    :return: Path to the example file
    """
    return pkg_resources.resource_filename("easygdf", "data/initial_distribution.gdf")


class GDFError(Exception):
    pass


class GDFIOError(GDFError):
    pass
