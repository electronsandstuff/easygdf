import easygdf

# Pull out an example screen/tout file from easygdf
filename = easygdf.get_example_screen_tout_filename()

# Load it back and print the number of screens and time outs
d = easygdf.load_screens_touts(filename)
print("n_screens: {0}".format(len(d["screens"])))
print("n_touts: {0}".format(len(d["touts"])))

# Let's print some data from the first screen in the file
screen = d["screens"][0]
print("x: {0}".format(screen["x"]))
print("Bx: {0}".format(screen["Bx"]))
print("m: {0}".format(screen["m"]))
