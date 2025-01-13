import os


def load_test_resource(path):
    return open(os.path.join(os.path.dirname(os.path.realpath(__file__)), path), "rb")
