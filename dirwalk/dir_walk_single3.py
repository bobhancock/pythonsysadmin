import os

fout = "/var/tmp/dirwalk_single3.txt"
home = "/var/tmp/dirwalk/test3"
#home = "/var/tmp/dirwalk/test0"
i = 0


with open(fout, "w") as fh_out:
    for dirpath, dirs, files in os.walk(home, topdown=True):
        for f in files:
            fname = os.path.join(dirpath, f)
            stat = os.stat(fname).st_atime
            fh_out.write("{f}|{s}\n".format(f=fname, s=stat))

print("Done")
