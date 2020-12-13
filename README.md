# easyGDF
EasyGDF is a python library that simplifies the loading and saving of general datafile format (GDF) files used in the
particle accelerator simulation code [General Particle Tracer (GPT)](http://www.pulsar.nl/gpt/).  

## Quickstart
Let's look at a minimal example of reading and writing GDF files.  GDF files are organized into blocks which each have a
name, a value, and possibly some children which are also blocks.
```
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
```
For the output of GPT, however, we don't need to deal with raw blocks and can rely on easyGDF to return the data in a
cleaner format.  Let's try using one of the convenience functions for this task.
```
import easygdf

# Pull out an example screen/tout file from easygdf
filename = easygdf.get_example_screen_tout_filename()

# Load it and print the number of screens and time outs
d = easygdf.load_screens_touts(filename)
print("n_screens: {0}".format(len(d["screens"])))
print("n_touts: {0}".format(len(d["touts"])))

# Let's print some data from the first screen in the file
screen = d["screens"][0]
print("x: {0}".format(screen["x"]))
print("Bx: {0}".format(screen["Bx"]))
print("m: {0}".format(screen["m"]))
```
Another common use of GDF files is in specifying initial particle distributions for GPT.  Let's take a look at using the
library's function for this task.
```
import easygdf
import numpy as np

# Save some data to an initial distribution file.  Unspecified required values are autofilled for us
easygdf.save_initial_distribution(
    "initial.gdf",
    x=np.random.normal(size=(3,)),
    GBx=np.random.normal(size=(3,)),
    t=np.random.random((3,)),
)
```

## Testing
Developers may use the python script `run_all_tests.py` to execute all unit tests in the project.  These tests are also
distributed with the library and are available to end users.  They may be run on a system where easyGDF is installed
using the following command.
```
$ python -m unittest easygdf.tests
```
If you are contributing to the library (Thank you!) please make sure your PR passes the full test suite.  In addition,
please add unit tests during bugfixes that will fail on the bug being repaired.  For feature additions please add test
cases as reasonable.

## Reporting Issues and Contributing
Errors are tracked on [our github page](https://github.com/electronsandstuff/easygdf).  Please report your
problems/feature requests there with as much detail as possible.  Contributions are always welcome.  Please open an
issue on github and start a discussion there before working on a PR.  Thanks!
