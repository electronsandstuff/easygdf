from importlib.resources import files


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


class GDFError(Exception):
    pass


class GDFIOError(GDFError):
    pass
