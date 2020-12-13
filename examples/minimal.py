import easygdf
import numpy as np

# Let's write an example file with a variety of data types
blocks = [
    {"name": "an array", "value": np.array([0, 1, 2, 3])},
    {"name": "a string", "value": "Hello world!"},
    {"name": "a group", "value": 3.14, "children": [{"name": "child", "value": 1.0}]}
]
easygdf.save("minimal.gdf", blocks)

# Now we'll read it back and print out some info about each block
d = easygdf.load("minimal.gdf")
for b in d["blocks"]:
    print("name='{0}'; value='{1}'; n_children={2}".format(b["name"], b["value"], len(b["children"])))
