"""
Create directory structure for dir walk testing.
"""
import os
base = "/var/tmp/dirwalk"
if not os.path.isdir(base):
    os.mkdir(base)

for i in range(5):
    sub=os.path.join(base, "test"+str(i))
    if not os.path.isdir(sub):
        os.mkdir(sub)

    for i in range(1000000):
        fname = os.path.join(os.path.join(base, sub),"fname"+str(i))
        if not os.path.isfile(fname):
            with open(fname, "w") as fh:
                fh.write("1\n")
