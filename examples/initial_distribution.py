import easygdf
import numpy as np

# Save some data to an initial distribution file.  Unspecified required values are autofilled for us
easygdf.save_initial_distribution(
    "initial.gdf",
    x=np.random.normal(size=(3,)),
    GBx=np.random.normal(size=(3,)),
    t=np.random.random((3,)),
)
