import numpy as np


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
        raise ValueError('Unable to autodetect GDF flag for numpy data type "{0}" with size {1} bytes'.format(t, s))


# The bit masks for flags in the GDF header
GDF_DTYPE = 255
GDF_GROUP_BEGIN = 256
GDF_GROUP_END = 512
GDF_SINGLE = 1024
GDF_ARRAY = 2048
